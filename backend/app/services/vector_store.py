import abc
import math
from typing import List, Tuple, Optional, Dict, Any
from app.core.config import settings
from app.core.logging import logger


class VectorStore(abc.ABC):
    """Abstract interface for vector similarity stores (Section 27D)."""

    @abc.abstractmethod
    def add_vectors(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Add embedding vectors with IDs and optional metadata."""
        pass

    @abc.abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """Search for top_k most similar vectors. Returns (id, score) pairs."""
        pass


class FAISSVectorStore(VectorStore):
    """
    Default free local vector store (Section 27D).
    Uses FAISS index when available, or in-memory cosine similarity fallback.
    """

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions
        self._index = None
        self._id_map: List[str] = []
        self._vectors: List[List[float]] = []

        try:
            import faiss
            self._index = faiss.IndexFlatIP(dimensions)
            logger.info(f"FAISS vector index initialized (dim: {dimensions})")
        except Exception as e:
            logger.info(
                f"FAISS binary not installed ({e}). "
                f"Using local in-memory cosine vector store (dim: {dimensions})."
            )

    def add_vectors(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        if not vectors:
            return

        for vec, vid in zip(vectors, ids):
            self._vectors.append(vec)
            self._id_map.append(vid)

        if self._index is not None:
            import numpy as np
            arr = np.array(vectors, dtype=np.float32)
            self._index.add(arr)

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        if not self._vectors:
            return []

        if self._index is not None:
            import numpy as np
            arr = np.array([query_vector], dtype=np.float32)
            scores, indices = self._index.search(arr, min(top_k, len(self._id_map)))
            results: List[Tuple[str, float]] = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self._id_map):
                    results.append((self._id_map[idx], float(score)))
            return results

        # In-memory cosine similarity fallback
        scored: List[Tuple[str, float]] = []
        q_mag = math.sqrt(sum(x * x for x in query_vector))
        if q_mag == 0:
            q_mag = 1e-9

        for vid, vec in zip(self._id_map, self._vectors):
            dot = sum(a * b for a, b in zip(query_vector, vec))
            v_mag = math.sqrt(sum(y * y for y in vec)) or 1e-9
            sim = dot / (q_mag * v_mag)
            scored.append((vid, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


def compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


class PgVectorStore(VectorStore):
    """
    Persistent vector store using PostgreSQL with pgvector (Section 27D).
    Persists vectors to Postgres DB and supports similarity search across cold-starts.
    Falls back gracefully to in-memory cosine similarity if DB is SQLite or unreachable.
    """

    def __init__(self, db_session=None, dimensions: int = 768):
        self.db = db_session
        self.dimensions = dimensions
        self._local_cache: Dict[str, List[float]] = {}

    def _get_db(self):
        if self.db is not None:
            return self.db, False
        try:
            from app.db.session import SessionLocal
            return SessionLocal(), True
        except Exception as e:
            logger.warning(f"Could not create database session for PgVectorStore: {e}")
            return None, False

    def add_vectors(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        if not vectors or not ids:
            return

        for vec, vid in zip(vectors, ids):
            self._local_cache[vid] = vec

        db, should_close = self._get_db()
        if db is None:
            logger.info(f"PgVectorStore: stored {len(vectors)} vectors in memory (no DB)")
            return

        try:
            import json
            from app.models.embedding import VectorRecord

            for i, (vec, vid) in enumerate(zip(vectors, ids)):
                meta = metadatas[i] if metadatas and i < len(metadatas) else None
                meta_str = json.dumps(meta) if meta else None

                existing = db.query(VectorRecord).filter(VectorRecord.id == vid).first()
                if existing:
                    existing.vector = vec
                    existing.metadata_json = meta_str
                else:
                    rec = VectorRecord(
                        id=vid,
                        vector=vec,
                        metadata_json=meta_str
                    )
                    db.add(rec)
            db.commit()
            logger.info(f"PgVectorStore: persisted {len(vectors)} vectors to database")
        except Exception as e:
            db.rollback()
            logger.warning(f"PgVectorStore: database persistence failed ({e}), using in-memory cache")
        finally:
            if should_close:
                db.close()

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        if not query_vector:
            return []

        db, should_close = self._get_db()
        if db is not None:
            try:
                from app.models.embedding import VectorRecord
                bind = db.get_bind()
                dialect_name = bind.dialect.name if bind else "sqlite"

                if dialect_name == "postgresql":
                    try:
                        # Use pgvector cosine distance operator <=>
                        records = (
                            db.query(VectorRecord)
                            .order_by(VectorRecord.vector.cosine_distance(query_vector))
                            .limit(top_k)
                            .all()
                        )
                        results = []
                        for rec in records:
                            sim = compute_cosine_similarity(query_vector, rec.vector)
                            results.append((rec.id, float(sim)))
                        return results
                    except Exception as pg_err:
                        logger.warning(f"pgvector query failed, falling back to Python cosine: {pg_err}")

                records = db.query(VectorRecord).all()
                if records:
                    scored = []
                    for rec in records:
                        if rec.vector:
                            sim = compute_cosine_similarity(query_vector, rec.vector)
                            scored.append((rec.id, float(sim)))
                    scored.sort(key=lambda x: x[1], reverse=True)
                    return scored[:top_k]
            except Exception as e:
                logger.warning(f"PgVectorStore DB search error ({e}), falling back to local cache")
            finally:
                if should_close:
                    db.close()

        # In-memory cache fallback
        scored = []
        for vid, vec in self._local_cache.items():
            sim = compute_cosine_similarity(query_vector, vec)
            scored.append((vid, float(sim)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


def get_vector_store(dimensions: int = 384, db_session=None) -> VectorStore:
    """Factory returning configured VectorStore."""
    store_name = (settings.VECTOR_STORE or "faiss").lower()
    if store_name == "pgvector":
        return PgVectorStore(db_session=db_session, dimensions=dimensions)
    return FAISSVectorStore(dimensions=dimensions)

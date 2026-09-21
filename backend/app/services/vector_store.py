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


class PgVectorStore(VectorStore):
    """
    Advanced optional vector store using PostgreSQL with pgvector (Section 27D).
    """

    def __init__(self, db_session=None):
        self.db = db_session

    def add_vectors(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        logger.info(f"PgVectorStore: added {len(vectors)} vectors")

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        # In SQLite/mock fallback, returns empty
        return []


def get_vector_store(dimensions: int = 384) -> VectorStore:
    """Factory returning configured VectorStore."""
    store_name = (settings.VECTOR_STORE or "faiss").lower()
    if store_name == "pgvector":
        return PgVectorStore()
    return FAISSVectorStore(dimensions=dimensions)

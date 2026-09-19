import math
from typing import List, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentVersion
from app.models.chunk import DocumentChunk
from app.models.embedding import Embedding
from app.models.retrieval import RetrievalRun, RetrievalResult
from app.services.embedding_service import EmbeddingService
from app.core.logging import logger


@dataclass
class RetrievalHit:
    chunk_id: str
    score: float
    rank: int
    page_start: int
    page_end: int
    heading_path: Optional[str]
    content: str
    contextual_content: str
    document_id: str
    document_title: str
    version_id: str


def compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


class RetrievalService:
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self.embedding_service = embedding_service or EmbeddingService()

    def dense_search(
        self,
        db: Session,
        user_id: str,
        query: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[RetrievalHit]:
        """
        Execute dense vector retrieval for a query scoped to documents owned by user_id.
        Optionally filter to specific document_ids.
        Supports both pgvector SQL execution and in-memory fallback for local SQLite development.
        """
        if not query or not query.strip():
            return []

        query_vector = self.embedding_service.embed_text(query.strip())

        # Base query joining Embedding -> DocumentChunk -> DocumentVersion -> Document
        base_query = (
            db.query(Embedding, DocumentChunk, Document)
            .join(DocumentChunk, Embedding.chunk_id == DocumentChunk.id)
            .join(DocumentVersion, DocumentChunk.version_id == DocumentVersion.id)
            .join(Document, DocumentVersion.document_id == Document.id)
            .filter(Document.owner_id == user_id)
        )

        if document_ids:
            base_query = base_query.filter(Document.id.in_(document_ids))

        # Check dialect: if postgresql and pgvector is supported
        bind = db.get_bind()
        dialect_name = bind.dialect.name if bind else "sqlite"

        hits: List[RetrievalHit] = []

        if dialect_name == "postgresql":
            try:
                # Use pgvector cosine distance operator <=>
                results = (
                    base_query.order_by(
                        Embedding.embedding.cosine_distance(query_vector)
                    )
                    .limit(top_k)
                    .all()
                )
                for rank, (emb, chunk, doc) in enumerate(results, start=1):
                    # In pgvector cosine_distance = 1 - cosine_similarity
                    sim = compute_cosine_similarity(query_vector, emb.embedding)
                    if score_threshold is None or sim >= score_threshold:
                        hits.append(
                            RetrievalHit(
                                chunk_id=chunk.id,
                                score=round(sim, 4),
                                rank=rank,
                                page_start=chunk.page_start,
                                page_end=chunk.page_end,
                                heading_path=chunk.heading_path,
                                content=chunk.content,
                                contextual_content=chunk.contextual_content,
                                document_id=doc.id,
                                document_title=doc.title,
                                version_id=chunk.version_id
                            )
                        )
                return hits
            except Exception as e:
                logger.warning(f"PostgreSQL pgvector query failed, falling back to in-memory: {e}")

        # In-memory vector calculation (SQLite fallback and local testing)
        records = base_query.all()
        scored_records = []

        for emb, chunk, doc in records:
            if not emb.embedding:
                continue
            sim = compute_cosine_similarity(query_vector, emb.embedding)
            if score_threshold is None or sim >= score_threshold:
                scored_records.append((sim, chunk, doc))

        # Sort by similarity descending
        scored_records.sort(key=lambda item: item[0], reverse=True)
        top_records = scored_records[:top_k]

        for rank, (sim, chunk, doc) in enumerate(top_records, start=1):
            hits.append(
                RetrievalHit(
                    chunk_id=chunk.id,
                    score=round(sim, 4),
                    rank=rank,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    heading_path=chunk.heading_path,
                    content=chunk.content,
                    contextual_content=chunk.contextual_content,
                    document_id=doc.id,
                    document_title=doc.title,
                    version_id=chunk.version_id
                )
            )

        return hits

    def record_retrieval_run(
        self,
        db: Session,
        message_id: str,
        query: str,
        hits: List[RetrievalHit],
        retrieval_method: str = "dense",
        latency_ms: float = 0.0
    ) -> RetrievalRun:
        """Persist RetrievalRun and associated RetrievalResult records for auditability."""
        run = RetrievalRun(
            message_id=message_id,
            query=query,
            retrieval_method=retrieval_method,
            latency_ms=latency_ms
        )
        db.add(run)
        db.flush()

        for hit in hits:
            res = RetrievalResult(
                retrieval_run_id=run.id,
                chunk_id=hit.chunk_id,
                retrieval_source=retrieval_method,
                rank=hit.rank,
                score=hit.score
            )
            db.add(res)

        db.commit()
        return run

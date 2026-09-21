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

        query_vector = self.embedding_service.embed_query(query.strip())

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

    def keyword_search(
        self,
        db: Session,
        user_id: str,
        query: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 10
    ) -> List[RetrievalHit]:
        """
        Execute BM25-style lexical keyword search over chunks.
        Accounts for exact phrases, heading matches, and term frequency.
        """
        if not query or not query.strip():
            return []

        clean_query = query.strip().lower()
        terms = [t for t in clean_query.split() if len(t) > 2]
        if not terms:
            terms = [clean_query]

        base_query = (
            db.query(DocumentChunk, Document)
            .join(DocumentVersion, DocumentChunk.version_id == DocumentVersion.id)
            .join(Document, DocumentVersion.document_id == Document.id)
            .filter(Document.owner_id == user_id)
        )

        if document_ids:
            base_query = base_query.filter(Document.id.in_(document_ids))

        chunks_and_docs = base_query.all()
        scored_hits = []

        for chunk, doc in chunks_and_docs:
            content_lower = chunk.content.lower()
            heading_lower = (chunk.heading_path or "").lower()
            score = 0.0

            # Exact phrase boost
            if clean_query in content_lower:
                score += 15.0

            # Heading match boost
            for term in terms:
                if term in heading_lower:
                    score += 5.0
                if term in content_lower:
                    # Term frequency
                    tf = content_lower.count(term)
                    score += math.log(1.0 + tf) * 2.0

            if score > 0:
                scored_hits.append((score, chunk, doc))

        scored_hits.sort(key=lambda x: x[0], reverse=True)
        top_items = scored_hits[:top_k]

        hits: List[RetrievalHit] = []
        for rank, (score, chunk, doc) in enumerate(top_items, start=1):
            hits.append(
                RetrievalHit(
                    chunk_id=chunk.id,
                    score=round(score, 4),
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

    @staticmethod
    def reciprocal_rank_fusion(
        dense_hits: List[RetrievalHit],
        keyword_hits: List[RetrievalHit],
        k: int = 60,
        top_k: int = 10
    ) -> List[RetrievalHit]:
        """
        Fuse dense and keyword ranked lists using Reciprocal Rank Fusion (RRF):
        RRF(d) = sum(1 / (k + rank_m(d))) for m in {dense, keyword}.
        """
        scores = {}
        hits_map = {}

        for hit in dense_hits:
            hits_map[hit.chunk_id] = hit
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + (1.0 / (k + hit.rank))

        for hit in keyword_hits:
            if hit.chunk_id not in hits_map:
                hits_map[hit.chunk_id] = hit
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + (1.0 / (k + hit.rank))

        # Sort chunk IDs by combined RRF score descending
        sorted_chunk_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)
        fused_hits: List[RetrievalHit] = []

        for rank, cid in enumerate(sorted_chunk_ids[:top_k], start=1):
            orig_hit = hits_map[cid]
            fused_hits.append(
                RetrievalHit(
                    chunk_id=orig_hit.chunk_id,
                    score=round(scores[cid], 6),
                    rank=rank,
                    page_start=orig_hit.page_start,
                    page_end=orig_hit.page_end,
                    heading_path=orig_hit.heading_path,
                    content=orig_hit.content,
                    contextual_content=orig_hit.contextual_content,
                    document_id=orig_hit.document_id,
                    document_title=orig_hit.document_title,
                    version_id=orig_hit.version_id
                )
            )

        return fused_hits

    def rerank_candidates(
        self,
        query: str,
        candidates: List[RetrievalHit],
        top_k: int = 5
    ) -> List[RetrievalHit]:
        """
        Rerank candidate chunks using contextual relevance and query term density.
        """
        if not candidates:
            return []

        query_terms = [t.lower() for t in query.split() if len(t) > 2]
        scored_candidates = []

        for hit in candidates:
            content_lower = hit.content.lower()
            heading_lower = (hit.heading_path or "").lower()

            # Base RRF or retrieval score
            combined_score = hit.score

            # Term overlap ratio
            matched_terms = sum(1 for t in query_terms if t in content_lower)
            overlap_ratio = matched_terms / len(query_terms) if query_terms else 0.0

            # Heading alignment boost
            heading_boost = 0.0
            if any(t in heading_lower for t in query_terms):
                heading_boost = 0.05

            final_score = combined_score + (overlap_ratio * 0.1) + heading_boost
            scored_candidates.append((final_score, hit))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        reranked_hits: List[RetrievalHit] = []

        for rank, (score, orig_hit) in enumerate(scored_candidates[:top_k], start=1):
            reranked_hits.append(
                RetrievalHit(
                    chunk_id=orig_hit.chunk_id,
                    score=round(score, 6),
                    rank=rank,
                    page_start=orig_hit.page_start,
                    page_end=orig_hit.page_end,
                    heading_path=orig_hit.heading_path,
                    content=orig_hit.content,
                    contextual_content=orig_hit.contextual_content,
                    document_id=orig_hit.document_id,
                    document_title=orig_hit.document_title,
                    version_id=orig_hit.version_id
                )
            )

        return reranked_hits

    def expand_context(
        self,
        db: Session,
        hits: List[RetrievalHit]
    ) -> List[RetrievalHit]:
        """
        Expand chunk context with neighboring chunks and parent section heading
        to ensure modifying clauses and caveats are not truncated.
        """
        expanded: List[RetrievalHit] = []

        for hit in hits:
            chunk = db.query(DocumentChunk).filter_by(id=hit.chunk_id).first()
            if not chunk:
                expanded.append(hit)
                continue

            expanded_text = hit.contextual_content or hit.content

            # Look up preceding chunk
            prev_chunk = (
                db.query(DocumentChunk)
                .filter_by(version_id=chunk.version_id, chunk_index=chunk.chunk_index - 1)
                .first()
            )
            if prev_chunk and prev_chunk.content:
                expanded_text = f"[Preceding Context: {prev_chunk.content[:200]}...]\n" + expanded_text

            # Look up succeeding chunk
            next_chunk = (
                db.query(DocumentChunk)
                .filter_by(version_id=chunk.version_id, chunk_index=chunk.chunk_index + 1)
                .first()
            )
            if next_chunk and next_chunk.content:
                expanded_text = expanded_text + f"\n[Succeeding Context: {next_chunk.content[:200]}...]"

            expanded.append(
                RetrievalHit(
                    chunk_id=hit.chunk_id,
                    score=hit.score,
                    rank=hit.rank,
                    page_start=hit.page_start,
                    page_end=hit.page_end,
                    heading_path=hit.heading_path,
                    content=hit.content,
                    contextual_content=expanded_text,
                    document_id=hit.document_id,
                    document_title=hit.document_title,
                    version_id=hit.version_id
                )
            )

        return expanded

    def hybrid_search(
        self,
        db: Session,
        user_id: str,
        query: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[RetrievalHit]:
        """
        Full Phase 8 Hybrid Retrieval Pipeline:
        1. Dense semantic search
        2. Lexical keyword search
        3. Reciprocal Rank Fusion (RRF)
        4. Candidate reranking
        5. Contextual neighbor & parent expansion
        """
        dense_hits = self.dense_search(
            db=db,
            user_id=user_id,
            query=query,
            document_ids=document_ids,
            top_k=20
        )
        keyword_hits = self.keyword_search(
            db=db,
            user_id=user_id,
            query=query,
            document_ids=document_ids,
            top_k=20
        )

        fused_hits = self.reciprocal_rank_fusion(
            dense_hits=dense_hits,
            keyword_hits=keyword_hits,
            k=60,
            top_k=15
        )

        reranked_hits = self.rerank_candidates(
            query=query,
            candidates=fused_hits,
            top_k=top_k
        )

        return self.expand_context(db=db, hits=reranked_hits)

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

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class RetrievalRun(Base):
    __tablename__ = "retrieval_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    retrieval_method = Column(String(64), nullable=False, default="hybrid")  # dense, keyword, hybrid
    latency_ms = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    message = relationship("Message", back_populates="retrieval_runs")
    results = relationship("RetrievalResult", back_populates="retrieval_run", cascade="all, delete-orphan")


class RetrievalResult(Base):
    __tablename__ = "retrieval_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    retrieval_run_id = Column(
        String(36),
        ForeignKey("retrieval_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    chunk_id = Column(String(36), ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False, index=True)
    retrieval_source = Column(String(32), nullable=False)  # dense, keyword, rerank
    rank = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)

    retrieval_run = relationship("RetrievalRun", back_populates="results")
    chunk = relationship("DocumentChunk", back_populates="retrieval_results")

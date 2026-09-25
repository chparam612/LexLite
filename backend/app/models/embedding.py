import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.types import VectorType


class EmbeddingModel(Base):
    __tablename__ = "embedding_models"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String(64), nullable=False, default="google")
    model_name = Column(String(128), nullable=False)
    dimensions = Column(Integer, nullable=False, default=768)
    version = Column(String(32), nullable=False, default="v1")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    embeddings = relationship("Embedding", back_populates="model")


class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chunk_id = Column(String(36), ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False, index=True)
    model_id = Column(String(36), ForeignKey("embedding_models.id"), nullable=False, index=True)
    embedding = Column(VectorType(768), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    chunk = relationship("DocumentChunk", back_populates="embeddings")
    model = relationship("EmbeddingModel", back_populates="embeddings")


class VectorRecord(Base):
    """General vector record for persistent vector store."""
    __tablename__ = "vector_records"

    id = Column(String(128), primary_key=True)
    vector = Column(VectorType(768), nullable=False)
    metadata_json = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = Column(String(36), ForeignKey("legal_sections.id", ondelete="SET NULL"), nullable=True, index=True)
    page_start = Column(Integer, nullable=False)
    page_end = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    heading_path = Column(String(512), nullable=True)
    content = Column(Text, nullable=False)  # Exact original text
    contextual_content = Column(Text, nullable=False)  # Enriched with metadata for embedding
    token_count = Column(Integer, nullable=False, default=0)
    checksum = Column(String(64), nullable=False)
    chunk_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    version = relationship("DocumentVersion", back_populates="chunks")
    section = relationship("LegalSection", back_populates="chunks")
    embeddings = relationship("Embedding", back_populates="chunk", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="chunk", cascade="all, delete-orphan")
    retrieval_results = relationship("RetrievalResult", back_populates="chunk", cascade="all, delete-orphan")
    claim_evidence = relationship("ClaimEvidence", back_populates="chunk", cascade="all, delete-orphan")

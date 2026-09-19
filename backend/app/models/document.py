import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    document_type = Column(String(64), nullable=True, default="contract")
    jurisdiction = Column(String(128), nullable=True)
    language = Column(String(16), nullable=False, default="en")
    status = Column(String(32), nullable=False, default="uploaded", index=True)
    page_count = Column(Integer, nullable=False, default=0)
    file_size = Column(Integer, nullable=False, default=0)
    storage_key = Column(String(512), nullable=False)
    checksum = Column(String(64), nullable=False, index=True)  # SHA-256
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    owner = relationship("User", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    storage_key = Column(String(512), nullable=False)
    extraction_status = Column(String(32), nullable=False, default="pending")
    processing_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document", back_populates="versions")
    pages = relationship("DocumentPage", back_populates="version", cascade="all, delete-orphan")
    sections = relationship("LegalSection", back_populates="version", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="version", cascade="all, delete-orphan")
    jobs = relationship("ProcessingJob", back_populates="version", cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    extracted_text = Column(Text, nullable=False, default="")
    ocr_used = Column(Boolean, nullable=False, default=False)
    page_metadata = Column("metadata", JSON, nullable=True)

    version = relationship("DocumentVersion", back_populates="pages")

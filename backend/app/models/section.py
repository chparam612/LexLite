import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class LegalSection(Base):
    __tablename__ = "legal_sections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_section_id = Column(String(36), ForeignKey("legal_sections.id", ondelete="SET NULL"), nullable=True)
    section_number = Column(String(64), nullable=True)
    heading = Column(String(512), nullable=True)
    section_type = Column(String(64), nullable=False, default="section")  # article, chapter, section, clause, etc.
    page_start = Column(Integer, nullable=False)
    page_end = Column(Integer, nullable=False)
    full_text = Column(Text, nullable=False, default="")

    version = relationship("DocumentVersion", back_populates="sections")
    parent = relationship("LegalSection", remote_side=[id], backref="subsections")
    chunks = relationship("DocumentChunk", back_populates="section")

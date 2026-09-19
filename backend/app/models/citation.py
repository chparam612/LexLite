import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class Citation(Base):
    __tablename__ = "citations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(String(36), ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    section_label = Column(String(255), nullable=True)
    quoted_text = Column(Text, nullable=False)
    citation_order = Column(Integer, nullable=False, default=1)

    message = relationship("Message", back_populates="citations")
    chunk = relationship("DocumentChunk", back_populates="citations")


class AnswerClaim(Base):
    __tablename__ = "answer_claims"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_text = Column(Text, nullable=False)
    claim_type = Column(String(64), nullable=False, default="document_fact")
    support_status = Column(String(32), nullable=False, default="supported")

    message = relationship("Message", back_populates="claims")
    evidence = relationship("ClaimEvidence", back_populates="claim", cascade="all, delete-orphan")


class ClaimEvidence(Base):
    __tablename__ = "claim_evidence"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(36), ForeignKey("answer_claims.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(String(36), ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False, index=True)
    entailment_score = Column(Float, nullable=False, default=1.0)
    evidence_type = Column(String(32), nullable=False, default="direct_quote")

    claim = relationship("AnswerClaim", back_populates="evidence")
    chunk = relationship("DocumentChunk", back_populates="claim_evidence")

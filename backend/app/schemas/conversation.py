from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class CitationResponse(BaseModel):
    id: str
    chunk_id: str
    page_number: int
    section_label: Optional[str] = None
    quoted_text: str
    citation_order: int
    document_title: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ClaimResponse(BaseModel):
    id: str
    claim_text: str
    claim_type: str
    support_status: str

    model_config = ConfigDict(from_attributes=True)


class ProcessingDetails(BaseModel):
    retrieval_method: str = "hybrid"
    candidate_chunks: int = 0
    context_chunks: int = 0
    reranking_used: bool = True
    verification_performed: bool = True
    verification_status: str = "supported"
    latency_ms: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    model_name: Optional[str] = None
    citations: List[CitationResponse] = []
    claims: List[ClaimResponse] = []
    processing_details: Optional[ProcessingDetails] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    title: Optional[str] = "Legal Research"
    document_ids: Optional[List[str]] = []


class ConversationUpdate(BaseModel):
    title: str


class ConversationResponse(BaseModel):
    id: str
    title: str
    document_ids: List[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationDetailResponse(BaseModel):
    id: str
    title: str
    document_ids: List[str] = []
    messages: List[MessageResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

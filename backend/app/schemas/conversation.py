from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, model_validator


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
    candidate_chunks_retrieved: Optional[int] = None
    context_chunks: int = 0
    context_chunks_used: Optional[int] = None
    reranking_used: bool = True
    verification_performed: bool = True
    verification_status: str = "supported"
    latency_ms: Optional[float] = None
    total_latency_ms: Optional[float] = None
    retrieval_latency_ms: Optional[float] = None
    generation_latency_ms: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def sync_aliases(self) -> "ProcessingDetails":
        if self.candidate_chunks_retrieved is None:
            self.candidate_chunks_retrieved = self.candidate_chunks
        if self.context_chunks_used is None:
            self.context_chunks_used = self.context_chunks
        if self.total_latency_ms is None:
            self.total_latency_ms = self.latency_ms
        if self.latency_ms is None:
            self.latency_ms = self.total_latency_ms
        return self


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

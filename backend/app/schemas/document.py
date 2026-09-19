from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class DocumentBase(BaseModel):
    title: str
    document_type: Optional[str] = "contract"
    jurisdiction: Optional[str] = None
    language: Optional[str] = "en"


class DocumentResponse(DocumentBase):
    id: str
    owner_id: str
    status: str
    page_count: int
    file_size: int
    checksum: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentVersionResponse(BaseModel):
    id: str
    version_number: int
    extraction_status: str
    processing_error: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentResponse):
    versions: List[DocumentVersionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class DocumentStatusResponse(BaseModel):
    document_id: str
    status: str
    current_step: str
    progress_percentage: int
    error: Optional[str] = None
    updated_at: datetime


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    message: str
    status: str

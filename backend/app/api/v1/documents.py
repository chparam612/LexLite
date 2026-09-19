from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.document import (
    DocumentResponse,
    DocumentDetailResponse,
    DocumentStatusResponse,
    DocumentUploadResponse
)
from app.services.document_service import DocumentService
from app.workers.processing_worker import DocumentProcessingPipeline

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    jurisdiction: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a legal PDF document. Validates file integrity, calculates SHA-256,
    stores the file securely, and initializes the processing pipeline.
    """
    content = await file.read()
    doc = DocumentService.upload_document(
        db=db,
        owner_id=current_user.id,
        file_data=content,
        original_filename=file.filename or "uploaded_document.pdf",
        title=title,
        jurisdiction=jurisdiction
    )

    if doc.versions:
        background_tasks.add_task(
            DocumentProcessingPipeline.process_in_background,
            doc.versions[-1].id
        )

    return DocumentUploadResponse(
        document=DocumentResponse.model_validate(doc),
        message="Document uploaded successfully and queued for processing.",
        status=doc.status
    )


@router.get("", response_model=List[DocumentResponse], status_code=status.HTTP_200_OK)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all documents owned by the authenticated tenant.
    """
    return DocumentService.list_documents(db=db, owner_id=current_user.id)


@router.get("/{document_id}", response_model=DocumentDetailResponse, status_code=status.HTTP_200_OK)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed document metadata. Strictly enforces document ownership.
    """
    return DocumentService.get_document(db=db, document_id=document_id, owner_id=current_user.id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Permanently delete a document, purged from physical storage and relational tables.
    """
    DocumentService.delete_document(db=db, document_id=document_id, owner_id=current_user.id)
    return None


@router.get("/{document_id}/status", response_model=DocumentStatusResponse, status_code=status.HTTP_200_OK)
def get_document_status(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Inspect the real-time processing status, current stage, and progress percentage.
    """
    return DocumentService.get_document_status(db=db, document_id=document_id, owner_id=current_user.id)


@router.post("/{document_id}/retry", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
def retry_document_processing(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retry processing on a failed document job.
    """
    doc = DocumentService.retry_processing(db=db, document_id=document_id, owner_id=current_user.id)
    if doc.versions:
        background_tasks.add_task(
            DocumentProcessingPipeline.process_in_background,
            doc.versions[-1].id
        )
    return doc

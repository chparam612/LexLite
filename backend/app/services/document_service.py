import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentVersion
from app.models.job import ProcessingJob
from app.schemas.document import DocumentStatusResponse
from app.services.storage_service import get_storage_service
from app.utils.file_utils import validate_pdf_file, compute_sha256
from app.core.exceptions import DocumentNotFoundError, ForbiddenError, FileValidationError
from app.core.config import settings
from app.core.logging import logger


class DocumentService:
    @staticmethod
    def upload_document(
        db: Session,
        owner_id: str,
        file_data: bytes,
        original_filename: str,
        title: Optional[str] = None,
        jurisdiction: Optional[str] = None
    ) -> Document:
        """
        Validate, deduplicate, securely store, and register a legal PDF document.
        """
        # 1. Validation & sanitization
        clean_filename, page_count = validate_pdf_file(
            file_data,
            original_filename,
            max_size_mb=settings.MAX_UPLOAD_SIZE_MB
        )

        # 2. Checksum calculation
        checksum = compute_sha256(file_data)

        # 3. Duplicate detection for this tenant
        existing_doc = db.query(Document).filter_by(
            owner_id=owner_id,
            checksum=checksum
        ).first()

        if existing_doc:
            logger.info(f"Duplicate upload detected for owner {owner_id} (checksum {checksum}). Reusing {existing_doc.id}")
            return existing_doc

        doc_id = str(uuid.uuid4())
        version_id = str(uuid.uuid4())
        storage_key = f"documents/{owner_id}/{doc_id}/{clean_filename}"

        # 4. Secure Storage
        storage = get_storage_service()
        storage.upload_file(file_data, storage_key)

        # 5. Database Records
        doc_title = title.strip() if (title and title.strip()) else clean_filename.replace(".pdf", "")

        document = Document(
            id=doc_id,
            owner_id=owner_id,
            title=doc_title,
            document_type="contract",
            jurisdiction=jurisdiction,
            language="en",
            status="uploaded",
            page_count=page_count,
            file_size=len(file_data),
            storage_key=storage_key,
            checksum=checksum
        )
        db.add(document)

        version = DocumentVersion(
            id=version_id,
            document_id=doc_id,
            version_number=1,
            storage_key=storage_key,
            extraction_status="pending"
        )
        db.add(version)

        job = ProcessingJob(
            id=str(uuid.uuid4()),
            version_id=version_id,
            job_type="extract",
            status="pending",
            attempts=0
        )
        db.add(job)

        db.commit()
        db.refresh(document)
        logger.info(f"Document {doc_id} created successfully with {page_count} pages.")
        return document

    @staticmethod
    def list_documents(db: Session, owner_id: str) -> List[Document]:
        """Fetch all documents belonging strictly to the requesting user."""
        return db.query(Document).filter_by(owner_id=owner_id).order_by(Document.created_at.desc()).all()

    @staticmethod
    def get_document(db: Session, document_id: str, owner_id: str) -> Document:
        """Fetch document details while strictly enforcing ownership."""
        doc = db.query(Document).filter_by(id=document_id).first()
        if not doc:
            raise DocumentNotFoundError(document_id)
        if doc.owner_id != owner_id:
            logger.warning(f"Unauthorized document access attempt: User {owner_id} tried to access {document_id}")
            raise ForbiddenError("You do not have permission to access this document.")
        return doc

    @staticmethod
    def get_document_file_bytes(db: Session, document_id: str, owner_id: str):
        """Fetch raw document bytes and title ensuring tenant authorization."""
        doc = DocumentService.get_document(db, document_id, owner_id)
        storage = get_storage_service()
        file_bytes = storage.get_file(doc.storage_key)
        return file_bytes, doc.title

    @staticmethod
    def delete_document(db: Session, document_id: str, owner_id: str) -> bool:
        """Enforce ownership, purge physical storage, and cascade delete document entities."""
        doc = DocumentService.get_document(db, document_id, owner_id)
        storage = get_storage_service()

        # Delete physical files from all versions
        for ver in doc.versions:
            storage.delete_file(ver.storage_key)
        storage.delete_file(doc.storage_key)

        db.delete(doc)
        db.commit()
        logger.info(f"Document {document_id} and all related data purged for owner {owner_id}.")
        return True

    @staticmethod
    def get_document_status(db: Session, document_id: str, owner_id: str) -> DocumentStatusResponse:
        """Retrieve progress and current processing stage of a document."""
        doc = DocumentService.get_document(db, document_id, owner_id)
        status_steps = {
            "uploaded": ("Uploaded and awaiting ingestion", 10),
            "extracting": ("Extracting text page-by-page", 30),
            "ocr_processing": ("Running optical character recognition", 45),
            "structuring": ("Detecting legal clauses and sections", 60),
            "chunking": ("Building legal-aware chunks", 75),
            "embedding": ("Generating semantic vector embeddings", 90),
            "completed": ("Processing completed successfully", 100),
            "failed": ("Processing encountered an error", 0),
        }

        step_desc, pct = status_steps.get(doc.status, ("Processing document", 50))
        error_msg = None
        if doc.versions and doc.versions[-1].processing_error:
            error_msg = doc.versions[-1].processing_error

        return DocumentStatusResponse(
            document_id=doc.id,
            status=doc.status,
            current_step=step_desc,
            progress_percentage=pct,
            error=error_msg,
            updated_at=doc.updated_at
        )

    @staticmethod
    def retry_processing(db: Session, document_id: str, owner_id: str) -> Document:
        """Retry processing for a failed document."""
        doc = DocumentService.get_document(db, document_id, owner_id)
        if doc.status != "failed":
            raise FileValidationError(
                f"Document {document_id} is in status '{doc.status}', only failed documents can be retried."
            )

        doc.status = "uploaded"
        if doc.versions:
            ver = doc.versions[-1]
            ver.extraction_status = "pending"
            ver.processing_error = None

            # Reset jobs
            for job in ver.jobs:
                if job.status == "failed":
                    job.status = "pending"
                    job.attempts += 1
                    job.error_message = None

        db.commit()
        db.refresh(doc)
        logger.info(f"Retrying document processing for {document_id}.")
        return doc

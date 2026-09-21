import uuid
from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import Session

from app.models.document import DocumentVersion, DocumentPage
from app.models.section import LegalSection
from app.models.chunk import DocumentChunk
from app.models.job import ProcessingJob
from app.services.storage_service import get_storage_service
from app.services.extraction_service import ExtractionService
from app.services.structure_service import StructureService
from app.services.chunking_service import ChunkingService
from app.core.logging import logger


class DocumentProcessingPipeline:
    @staticmethod
    def process_in_background(version_id: str):
        """Execute document processing pipeline in a background task with a dedicated session."""
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            DocumentProcessingPipeline.process_document_version(db, version_id)
        except Exception as e:
            logger.error(f"Background processing task error for version {version_id}: {e}")
        finally:
            db.close()

    @staticmethod
    def process_document_version(db: Session, version_id: str) -> bool:
        """
        Execute the end-to-end ingestion pipeline for a document version:
        1. Extract text page by page (with OCR if needed)
        2. Detect legal structure (Articles, Sections, Definitions)
        3. Construct contextual legal chunks
        4. Update status & jobs
        """
        version = db.query(DocumentVersion).filter_by(id=version_id).first()
        if not version:
            logger.error(f"Cannot process: DocumentVersion {version_id} not found.")
            return False

        doc = version.document
        storage = get_storage_service()

        # Find or create processing job
        job = db.query(ProcessingJob).filter_by(version_id=version_id, job_type="extract").first()
        if not job:
            job = ProcessingJob(
                id=str(uuid.uuid4()),
                version_id=version_id,
                job_type="extract",
                status="processing",
                started_at=datetime.now(timezone.utc)
            )
            db.add(job)
        else:
            job.status = "processing"
            job.started_at = datetime.now(timezone.utc)

        doc.status = "extracting"
        version.extraction_status = "extracting"
        db.commit()

        try:
            # 1. Fetch file data
            pdf_bytes = storage.get_file(version.storage_key)

            # 2. Extract pages
            extractor = ExtractionService()
            extracted_pages = extractor.extract_pages(pdf_bytes)

            # Clear any existing pages (for retryability)
            db.query(DocumentPage).filter_by(version_id=version_id).delete()

            for p_data in extracted_pages:
                page_rec = DocumentPage(
                    id=str(uuid.uuid4()),
                    version_id=version_id,
                    page_number=p_data["page_number"],
                    extracted_text=p_data["extracted_text"],
                    ocr_used=p_data["ocr_used"],
                    page_metadata=p_data["metadata"]
                )
                db.add(page_rec)

            doc.page_count = len(extracted_pages)
            doc.status = "structuring"
            db.commit()

            # 3. Detect legal structure
            parsed_sections = StructureService.parse_legal_structure(extracted_pages)

            # Clear existing sections and chunks (for retryability)
            db.query(DocumentChunk).filter_by(version_id=version_id).delete()
            db.query(LegalSection).filter_by(version_id=version_id).delete()

            section_db_records: List[LegalSection] = []
            for sec in parsed_sections:
                sec_rec = LegalSection(
                    id=str(uuid.uuid4()),
                    version_id=version_id,
                    section_number=sec.section_number,
                    heading=sec.heading,
                    section_type=sec.section_type,
                    page_start=sec.page_start,
                    page_end=sec.page_end,
                    full_text=sec.full_text
                )
                db.add(sec_rec)
                section_db_records.append(sec_rec)

            db.commit()

            # Wire parent-child relationships
            for i, sec in enumerate(parsed_sections):
                if sec.parent_index is not None and sec.parent_index < len(section_db_records):
                    section_db_records[i].parent_section_id = section_db_records[sec.parent_index].id
            db.commit()

            # 4. Construct legal chunks
            doc.status = "chunking"
            db.commit()

            chunks = ChunkingService.chunk_legal_sections(
                document_title=doc.title,
                jurisdiction=doc.jurisdiction,
                sections=parsed_sections
            )

            for c in chunks:
                # Link to corresponding section record if available
                sec_id = None
                if section_db_records:
                    # Find closest matching section
                    for s_rec in section_db_records:
                        if s_rec.section_number == c.section_number:
                            sec_id = s_rec.id
                            break
                    if not sec_id and section_db_records:
                        sec_id = section_db_records[0].id

                chunk_rec = DocumentChunk(
                    id=str(uuid.uuid4()),
                    version_id=version_id,
                    section_id=sec_id,
                    page_start=c.page_start,
                    page_end=c.page_end,
                    chunk_index=c.chunk_index,
                    heading_path=c.heading_path,
                    content=c.content,
                    contextual_content=c.contextual_content,
                    token_count=c.token_count,
                    checksum=c.checksum,
                    chunk_metadata=c.metadata
                )
                db.add(chunk_rec)

            db.commit()

            # 5. Embeddings
            doc.status = "embedding"
            db.commit()

            created_chunks = (
                db.query(DocumentChunk)
                .filter_by(version_id=version_id)
                .order_by(DocumentChunk.chunk_index)
                .all()
            )
            from app.services.embedding_service import EmbeddingService
            embedding_service = EmbeddingService()
            emb_count = embedding_service.generate_and_store_embeddings(db, created_chunks)

            # 6. Success
            doc.status = "completed"
            version.extraction_status = "completed"
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            db.commit()

            logger.info(
                f"Processing completed for {doc.id}: {len(extracted_pages)} pages, "
                f"{len(section_db_records)} sections, {len(chunks)} chunks, {emb_count} embeddings."
            )
            return True

        except Exception as e:
            logger.error(f"Document processing failed for {doc.id}: {str(e)}", exc_info=True)
            db.rollback()
            try:
                doc.status = "failed"
                version.extraction_status = "failed"
                version.processing_error = str(e)
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
            except Exception as commit_err:
                logger.error(f"Failed to record failure status in database: {commit_err}")
                db.rollback()
            return False

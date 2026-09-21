from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.demo_document_service import get_sample_rental_agreement_bytes
from app.services.document_service import DocumentService
from app.workers.processing_worker import DocumentProcessingPipeline
from app.schemas.document import DocumentResponse

router = APIRouter(prefix="/demo", tags=["Demo & Judging"])


@router.get("/sample-document", status_code=status.HTTP_200_OK)
def download_sample_document():
    """
    Download the standard synthetic residential rental agreement PDF
    designed for judging, evaluations, and live testing.
    """
    pdf_bytes = get_sample_rental_agreement_bytes()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="Sample_Residential_Rental_Agreement_Fictional_Demo.pdf"'
        }
    )


@router.post("/load-sample", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def load_sample_document_for_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Uploads and synchronously processes the synthetic rental agreement
    into the authenticated tenant's library for instant live testing.
    """
    pdf_bytes = get_sample_rental_agreement_bytes()

    doc = DocumentService.upload_document(
        db=db,
        owner_id=current_user.id,
        file_data=pdf_bytes,
        original_filename="Sample_Residential_Rental_Agreement_Fictional_Demo.pdf",
        title="Sample Residential Rental Agreement — Fictional Demo",
        jurisdiction="State of New York"
    )

    # Process immediately so document is ready for queries
    if doc.versions and doc.status != "completed":
        DocumentProcessingPipeline.process_document_version(db, doc.versions[-1].id)
        db.refresh(doc)

    return DocumentResponse.model_validate(doc)

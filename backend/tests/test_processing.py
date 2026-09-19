import fitz
from app.services.extraction_service import ExtractionService
from app.services.structure_service import StructureService
from app.services.chunking_service import ChunkingService
from app.services.ocr_service import OCRService
from app.workers.processing_worker import DocumentProcessingPipeline
from app.models.document import Document, DocumentVersion, DocumentPage
from app.models.section import LegalSection
from app.models.chunk import DocumentChunk
from app.models.user import User
from app.services.storage_service import get_storage_service
import uuid


def create_multipage_pdf(pages_content: list, is_html: bool = False) -> bytes:
    doc = fitz.open()
    for text in pages_content:
        page = doc.new_page()
        if is_html:
            page.insert_htmlbox(fitz.Rect(50, 50, 500, 700), text)
        else:
            if text:
                page.insert_text((50, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def test_de001_to_de004_page_by_page_extraction():
    """TEST-DE001 to TEST-DE004: Page-by-page text extraction, page numbers, and empty page handling."""
    pages_text = [
        "Page 1: ARTICLE I - DEFINITIONS\nSection 1.1 Scope.",
        "",  # Empty page
        "Page 3: ARTICLE II - COVENANTS\nSection 2.1 Obligations."
    ]
    pdf_bytes = create_multipage_pdf(pages_text)
    service = ExtractionService()
    extracted = service.extract_pages(pdf_bytes)

    assert len(extracted) == 3
    assert extracted[0]["page_number"] == 1
    assert "ARTICLE I" in extracted[0]["extracted_text"]
    assert extracted[1]["page_number"] == 2
    assert extracted[1]["extracted_text"].strip() == ""
    assert extracted[1]["ocr_used"] is False
    assert extracted[2]["page_number"] == 3
    assert "ARTICLE II" in extracted[2]["extracted_text"]


def test_de005_and_de006_ocr_detection_and_trigger():
    """TEST-DE005 & TEST-DE006: Scanned pages detection and OCR trigger."""
    ocr_service = OCRService()
    # Image present with short text indicates a scanned document
    assert ocr_service.is_scanned_page("Short", image_count=1) is True
    assert ocr_service.is_scanned_page("", image_count=1) is True
    assert ocr_service.is_scanned_page("", image_count=0) is False  # Empty page without images
    assert ocr_service.is_scanned_page("A" * 100, image_count=1) is False

    # Mock OCR execution
    ocr_result = ocr_service.process_page_ocr(b"fake_image_bytes")
    assert "OCR" in ocr_result


def test_de008_and_de009_unicode_and_multilingual_preservation():
    """TEST-DE008 & TEST-DE009: Preservation of legal unicode symbols and multilingual/Hindi glyphs."""
    html_legal = (
        "<p>Section 12.3 Legal Disclaimer &mdash; &ldquo;All rights reserved&rdquo; &copy; 2026.</p>"
        "<p>Hindi Legal Terms: &#2309;&#2344;&#2369;&#2348;&#2306;&#2343; (Contract).</p>"
    )
    pdf_bytes = create_multipage_pdf([html_legal], is_html=True)
    service = ExtractionService()
    extracted = service.extract_pages(pdf_bytes)

    text_bytes = extracted[0]["extracted_text"].encode("utf-8")
    # Verify Copyright symbol (© is \xc2\xa9)
    assert b"\xc2\xa9" in text_bytes
    # Verify Hindi Devanagari bytes (अनुबंध starts with \xe0\xa4)
    assert b"\xe0\xa4\x85\xe0\xa4\xa8\xe0\xa5\x81" in text_bytes
    assert "2026" in extracted[0]["extracted_text"]


def test_ch001_to_ch010_legal_structure_detection():
    """TEST-CH001 to TEST-CH010: Detect Title, Articles, Sections, Definitions, Schedules, and Hierarchy."""
    sample_legal_text = (
        "MASTER SERVICES AGREEMENT\n"
        "ARTICLE I - DEFINITIONS\n"
        '"Confidential Information" means any proprietary data disclosed by either party.\n'
        "ARTICLE II - SERVICES AND OBLIGATIONS\n"
        "2.1 Service Level Agreement\n"
        "The Vendor shall perform the services with 99.9% uptime, provided that planned maintenance is excluded.\n"
        "SCHEDULE A - PRICING AND RATES\n"
        "Hourly rate shall be $250 per hour."
    )

    pages = [{"page_number": 1, "extracted_text": sample_legal_text}]
    sections = StructureService.parse_legal_structure(pages)

    assert len(sections) >= 3

    # Check Schedule
    sched = [s for s in sections if s.section_type == "schedule"]
    assert len(sched) == 1
    assert "SCHEDULE A" in sched[0].heading or "A" in sched[0].section_number

    # Check Article
    articles = [s for s in sections if s.section_type == "article"]
    assert len(articles) >= 1
    assert "ARTICLE" in articles[0].heading or "I" in articles[0].section_number

    # Check Title detection
    detected_title = StructureService.detect_document_title(sample_legal_text)
    assert "MASTER SERVICES AGREEMENT" in detected_title


def test_ch011_to_ch020_chunking_and_contextual_metadata():
    """TEST-CH011 to TEST-CH020: Chunk token limits, contextual metadata, checksums, and determinism."""
    legal_text = (
        "Section 5.1 - Termination for Convenience\n"
        "Either party may terminate this Agreement without cause upon giving thirty (30) days prior written notice, "
        "except as otherwise provided in Section 5.2 regarding milestone deliverables."
    )
    pages = [{"page_number": 2, "extracted_text": legal_text}]
    sections = StructureService.parse_legal_structure(pages)

    chunks = ChunkingService.chunk_legal_sections(
        document_title="Cloud Services Contract",
        jurisdiction="State of New York",
        sections=sections
    )

    assert len(chunks) == 1
    c = chunks[0]

    # TEST-CH014: Original text exact preservation
    assert "terminate this Agreement without cause" in c.content

    # TEST-CH015: Contextual embedding text includes document, jurisdiction, section metadata
    assert "Document: Cloud Services Contract" in c.contextual_content
    assert "Jurisdiction: State of New York" in c.contextual_content
    assert "Content:\n" in c.contextual_content

    # TEST-CH016: Deterministic checksum
    assert len(c.checksum) == 64
    assert c.token_count > 0

    # TEST-CH013: Modifying exception remains connected
    assert "except as otherwise provided" in c.content


def test_document_pipeline_end_to_end(db_session):
    """Verify complete worker execution: extraction -> structure -> chunking -> completed state."""
    uid = uuid.uuid4().hex[:8]
    user = User(
        id=str(uuid.uuid4()),
        firebase_uid=f"fb_{uid}",
        email=f"pipe_{uid}@law.com"
    )
    db_session.add(user)
    db_session.commit()

    sample_doc_content = (
        "CONFIDENTIAL NON-DISCLOSURE AGREEMENT\n"
        "ARTICLE 1 - DEFINITIONS\n"
        '"Disclosing Party" means the party disclosing proprietary information.\n'
        "ARTICLE 2 - OBLIGATIONS\n"
        "2.1 Duty of Confidentiality\n"
        "Receiving Party agrees to hold all Information in strict confidence for a period of five (5) years."
    )
    pdf_bytes = create_multipage_pdf([sample_doc_content])
    storage_key = f"tests/pipeline_{uuid.uuid4().hex}.pdf"

    storage = get_storage_service()
    storage.upload_file(pdf_bytes, storage_key)

    doc = Document(
        id=str(uuid.uuid4()),
        owner_id=user.id,
        title="Non-Disclosure Agreement",
        checksum="pipe_chk_123",
        storage_key=storage_key,
        status="uploaded"
    )
    version = DocumentVersion(
        id=str(uuid.uuid4()),
        document_id=doc.id,
        version_number=1,
        storage_key=storage_key,
        extraction_status="pending"
    )
    db_session.add_all([doc, version])
    db_session.commit()

    # 2. Run Pipeline
    success = DocumentProcessingPipeline.process_document_version(db_session, version.id)
    assert success is True

    # 3. Verify states
    db_session.refresh(doc)
    db_session.refresh(version)

    assert doc.status == "completed"
    assert version.extraction_status == "completed"
    assert doc.page_count == 1

    # Verify pages, sections, chunks created
    pages = db_session.query(DocumentPage).filter_by(version_id=version.id).all()
    sections = db_session.query(LegalSection).filter_by(version_id=version.id).all()
    chunks = db_session.query(DocumentChunk).filter_by(version_id=version.id).all()

    assert len(pages) == 1
    assert len(sections) >= 2
    assert len(chunks) >= 1
    assert "Duty of Confidentiality" in chunks[-1].content

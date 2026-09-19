import uuid
import pytest
from unittest.mock import patch, MagicMock

from app.models.user import User
from app.models.document import Document, DocumentVersion
from app.models.chunk import DocumentChunk
from app.models.embedding import Embedding, EmbeddingModel
from app.services.embedding_service import EmbeddingService, DEFAULT_DIMENSIONS
from app.core.exceptions import LegalAIException
import fitz
from app.workers.processing_worker import DocumentProcessingPipeline
from app.services.storage_service import get_storage_service


def create_sample_pdf_bytes(text: str = "Legal Section 1") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def test_em001_generate_valid_embedding():
    """TEST-EM001: Generate embedding vector with 768 dimensions for valid legal text."""
    service = EmbeddingService()
    vec = service.embed_text("Section 10 of the Indian Contract Act 1872: All agreements are contracts.")
    assert isinstance(vec, list)
    assert len(vec) == DEFAULT_DIMENSIONS
    # Check L2 norm is approximately 1.0 (unit vector)
    norm = sum(x * x for x in vec) ** 0.5
    assert abs(norm - 1.0) < 1e-4


def test_em002_empty_text_rejected():
    """TEST-EM002: Empty or whitespace-only text is rejected with 400."""
    service = EmbeddingService()
    with pytest.raises(LegalAIException) as exc_info:
        service.embed_text("")
    assert exc_info.value.status_code == 400
    assert exc_info.value.code == "EMPTY_EMBEDDING_INPUT"

    with pytest.raises(LegalAIException):
        service.embed_text("   \n\t   ")


def test_em003_model_record_creation(db_session):
    """TEST-EM003: Model metadata record is created and retrieved idempotently."""
    service = EmbeddingService()
    model1 = service.get_or_create_model_record(db_session)
    assert isinstance(model1, EmbeddingModel)
    assert model1.dimensions == 768
    assert model1.model_name == service.model_name
    assert model1.is_active is True

    # Calling again should retrieve the same record
    model2 = service.get_or_create_model_record(db_session)
    assert model1.id == model2.id


def test_em004_embedding_persistence_and_chunk_link(db_session):
    """TEST-EM004: Embedding persistence correctly linked to DocumentChunk and Model ID."""
    user = User(
        id=str(uuid.uuid4()),
        firebase_uid=str(uuid.uuid4()),
        email="lawyer@example.com",
        display_name="Counsel"
    )
    doc = Document(
        id=str(uuid.uuid4()),
        owner_id=user.id,
        title="Test Act",
        checksum="chk1",
        storage_key="k",
        status="processing"
    )
    version = DocumentVersion(id=str(uuid.uuid4()), document_id=doc.id, version_number=1, storage_key="k")
    chunk = DocumentChunk(
        id=str(uuid.uuid4()),
        version_id=version.id,
        chunk_index=0,
        page_start=1,
        page_end=1,
        content="Raw chunk text",
        contextual_content="[Document: Test Act] Raw chunk text",
        checksum="chunk_chk_1"
    )
    db_session.add_all([user, doc, version, chunk])
    db_session.commit()

    service = EmbeddingService()
    stored_count = service.generate_and_store_embeddings(db_session, [chunk])
    assert stored_count == 1

    emb = db_session.query(Embedding).filter_by(chunk_id=chunk.id).first()
    assert emb is not None
    assert len(emb.embedding) == 768
    assert emb.model_id is not None


def test_em005_idempotent_embedding_generation(db_session):
    """TEST-EM005: Running embedding generation twice on same chunks avoids duplicates."""
    user = User(
        id=str(uuid.uuid4()),
        firebase_uid=str(uuid.uuid4()),
        email="lawyer2@example.com",
        display_name="Counsel 2"
    )
    doc = Document(
        id=str(uuid.uuid4()),
        owner_id=user.id,
        title="Contract Law",
        checksum="chk2",
        storage_key="k2",
        status="processing"
    )
    version = DocumentVersion(id=str(uuid.uuid4()), document_id=doc.id, version_number=1, storage_key="k2")
    chunk = DocumentChunk(
        id=str(uuid.uuid4()),
        version_id=version.id,
        chunk_index=0,
        page_start=1,
        page_end=1,
        content="Free consent is essential for a valid contract.",
        contextual_content="Free consent is essential for a valid contract.",
        checksum="chunk_chk_2"
    )
    db_session.add_all([user, doc, version, chunk])
    db_session.commit()

    service = EmbeddingService()
    first_pass = service.generate_and_store_embeddings(db_session, [chunk])
    assert first_pass == 1

    second_pass = service.generate_and_store_embeddings(db_session, [chunk])
    assert second_pass == 0

    total_embeddings = db_session.query(Embedding).filter_by(chunk_id=chunk.id).count()
    assert total_embeddings == 1


def test_em006_secret_redaction_in_errors():
    """TEST-EM006: Sensitive API keys must be redacted from all error logs and messages."""
    fake_key = "AIzaSySecretApiKey123456789"
    service = EmbeddingService(api_key=fake_key)
    service.client_initialized = True

    with patch("google.generativeai.embed_content", side_effect=Exception(f"Error connecting with {fake_key}")):
        with pytest.raises(LegalAIException) as exc_info:
            service.embed_text("Sample legal text", retries=1)

        # Ensure fake_key is not in the raised exception message
        assert fake_key not in str(exc_info.value.message)


def test_em007_rate_limit_retry_mechanism():
    """TEST-EM007: Rate limit errors trigger retry backoff."""
    service = EmbeddingService(api_key="real-mock-key")
    service.client_initialized = True

    mock_embed = MagicMock()
    # First call raises 429 ResourceExhausted, second call succeeds
    mock_embed.side_effect = [
        Exception("429 Resource Exhausted: Quota exceeded"),
        {"embedding": [0.01] * DEFAULT_DIMENSIONS}
    ]

    with patch("google.generativeai.embed_content", mock_embed), patch("time.sleep") as mock_sleep:
        vec = service.embed_text("Legal text requiring retry", retries=2)
        assert len(vec) == DEFAULT_DIMENSIONS
        assert mock_embed.call_count == 2
        mock_sleep.assert_called_once_with(1)  # 2^0 = 1s backoff


def test_em008_embed_batch():
    """TEST-EM008: Batch embedding generation handles multiple texts cleanly."""
    service = EmbeddingService()
    texts = ["First legal clause", "Second legal definition", "Third schedule"]
    embeddings = service.embed_batch(texts)
    assert len(embeddings) == 3
    for emb in embeddings:
        assert len(emb) == DEFAULT_DIMENSIONS


def test_em009_contextual_content_preferred(db_session):
    """TEST-EM009: contextual_content is preferred over raw content for embedding."""
    user = User(
        id=str(uuid.uuid4()),
        firebase_uid=str(uuid.uuid4()),
        email="lawyer3@example.com",
        display_name="Counsel 3"
    )
    doc = Document(
        id=str(uuid.uuid4()),
        owner_id=user.id,
        title="Arbitration Act",
        checksum="chk3",
        storage_key="k3",
        status="processing"
    )
    version = DocumentVersion(id=str(uuid.uuid4()), document_id=doc.id, version_number=1, storage_key="k3")
    chunk = DocumentChunk(
        id=str(uuid.uuid4()),
        version_id=version.id,
        chunk_index=0,
        page_start=1,
        page_end=1,
        content="Plain content",
        contextual_content="[Document: Arbitration Act > Section 7] Plain content",
        checksum="chunk_chk_3"
    )
    db_session.add_all([user, doc, version, chunk])
    db_session.commit()

    service = EmbeddingService()
    with patch.object(service, "embed_text", wraps=service.embed_text) as mock_embed:
        service.generate_and_store_embeddings(db_session, [chunk])
        mock_embed.assert_called_once_with(chunk.contextual_content)


def test_em010_pipeline_generates_embeddings(db_session):
    """TEST-EM010: DocumentProcessingPipeline end-to-end creates chunks AND embeddings."""
    user = User(
        id=str(uuid.uuid4()),
        firebase_uid=str(uuid.uuid4()),
        email="counsel_pipeline@example.com",
        display_name="Pipeline User"
    )
    storage_key = f"tests/pipeline_emb_{uuid.uuid4().hex}.pdf"
    pdf_bytes = create_sample_pdf_bytes(
        "Section 1. Short Title\nThis Act may be called the Full Pipeline Act 2024.\n"
        "Section 2. Scope\nIt extends to the whole of India."
    )
    storage = get_storage_service()
    storage.upload_file(pdf_bytes, storage_key)

    doc = Document(
        id=str(uuid.uuid4()),
        owner_id=user.id,
        title="Full Pipeline Act 2024",
        jurisdiction="IN",
        checksum="chk_pipeline_10",
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
    db_session.add_all([user, doc, version])
    db_session.commit()

    success = DocumentProcessingPipeline.process_document_version(db_session, version.id)
    assert success is True
    assert doc.status == "completed"

    chunks = db_session.query(DocumentChunk).filter_by(version_id=version.id).all()
    assert len(chunks) > 0

    embeddings = db_session.query(Embedding).join(DocumentChunk).filter(
        DocumentChunk.version_id == version.id
    ).all()
    assert len(embeddings) == len(chunks)
    for emb in embeddings:
        assert len(emb.embedding) == 768

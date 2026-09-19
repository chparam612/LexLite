import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from app.models import (
    User,
    Document,
    DocumentVersion,
    DocumentPage,
    LegalSection,
    DocumentChunk,
    EmbeddingModel,
    Embedding,
    Conversation,
    Message,
    Citation,
    AnswerClaim,
    ClaimEvidence,
    ProcessingJob
)


def test_user_creation_and_constraints(db_session):
    """Verify User model creation, uniqueness constraints, and relationships."""
    unique_email = f"counsel_{uuid.uuid4().hex[:8]}@firm.com"
    user = User(
        id=str(uuid.uuid4()),
        firebase_uid=f"fb_{uuid.uuid4().hex[:8]}",
        email=unique_email,
        display_name="Corporate Counsel"
    )
    db_session.add(user)
    db_session.commit()

    saved = db_session.query(User).filter_by(email=unique_email).first()
    assert saved is not None
    assert saved.display_name == "Corporate Counsel"

    # Test uniqueness constraint
    duplicate_user = User(
        id=str(uuid.uuid4()),
        firebase_uid=saved.firebase_uid,
        email=unique_email
    )
    db_session.add(duplicate_user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_document_and_version_hierarchy(db_session):
    """Verify document, version, and page creation with cascade rules."""
    user = User(
        id=str(uuid.uuid4()),
        firebase_uid=f"fb_{uuid.uuid4().hex[:8]}",
        email=f"user_{uuid.uuid4().hex[:8]}@example.com"
    )
    db_session.add(user)
    db_session.commit()

    doc = Document(
        id=str(uuid.uuid4()),
        owner_id=user.id,
        title="Non-Disclosure Agreement",
        document_type="contract",
        jurisdiction="California",
        status="uploaded",
        checksum="sha256_mock_12345",
        storage_key="docs/nda.pdf"
    )
    db_session.add(doc)
    db_session.commit()

    version = DocumentVersion(
        id=str(uuid.uuid4()),
        document_id=doc.id,
        version_number=1,
        storage_key="docs/nda_v1.pdf"
    )
    db_session.add(version)
    db_session.commit()

    page = DocumentPage(
        id=str(uuid.uuid4()),
        version_id=version.id,
        page_number=1,
        extracted_text="CONFIDENTIALITY AGREEMENT\n1. Definition...",
        ocr_used=False,
        page_metadata={"dpi": 300, "word_count": 120}
    )
    db_session.add(page)
    db_session.commit()

    # Query back
    queried_doc = db_session.query(Document).filter_by(id=doc.id).first()
    assert len(queried_doc.versions) == 1
    assert len(queried_doc.versions[0].pages) == 1
    assert queried_doc.versions[0].pages[0].page_metadata["word_count"] == 120


def test_legal_sections_and_chunks(db_session):
    """Verify section nesting and chunk mapping."""
    user = User(id=str(uuid.uuid4()), firebase_uid=f"fb_{uuid.uuid4().hex[:8]}", email=f"u_{uuid.uuid4().hex[:8]}@law.com")
    db_session.add(user)
    db_session.commit()

    doc = Document(id=str(uuid.uuid4()), owner_id=user.id, title="Bylaws", checksum="chk1", storage_key="k1")
    ver = DocumentVersion(id=str(uuid.uuid4()), document_id=doc.id, version_number=1, storage_key="k1")
    db_session.add_all([doc, ver])
    db_session.commit()

    # Parent section (Article I)
    parent_sec = LegalSection(
        id=str(uuid.uuid4()),
        version_id=ver.id,
        section_number="I",
        heading="Offices and Records",
        section_type="article",
        page_start=1,
        page_end=2
    )
    db_session.add(parent_sec)
    db_session.commit()

    # Child section (Section 1.1)
    child_sec = LegalSection(
        id=str(uuid.uuid4()),
        version_id=ver.id,
        parent_section_id=parent_sec.id,
        section_number="1.1",
        heading="Registered Office",
        section_type="section",
        page_start=1,
        page_end=1,
        full_text="The registered office of the Corporation shall be located in Dover, Delaware."
    )
    db_session.add(child_sec)
    db_session.commit()

    # Chunk attached to child section
    chunk = DocumentChunk(
        id=str(uuid.uuid4()),
        version_id=ver.id,
        section_id=child_sec.id,
        page_start=1,
        page_end=1,
        chunk_index=0,
        heading_path="Article I > Section 1.1 Registered Office",
        content="The registered office of the Corporation shall be located in Dover, Delaware.",
        contextual_content="Document: Bylaws | Section: Article I > Section 1.1 | Content: The registered office...",
        token_count=18,
        checksum="chk_chunk_1"
    )
    db_session.add(chunk)
    db_session.commit()

    saved_child = db_session.query(LegalSection).filter_by(id=child_sec.id).first()
    assert saved_child.parent.heading == "Offices and Records"
    assert len(saved_child.chunks) == 1
    assert saved_child.chunks[0].token_count == 18


def test_embedding_vector_storage(db_session):
    """Verify vector serialization, dimensions, and chunk relationships."""
    user = User(id=str(uuid.uuid4()), firebase_uid=f"fb_{uuid.uuid4().hex[:8]}", email=f"u_{uuid.uuid4().hex[:8]}@vec.com")
    doc = Document(id=str(uuid.uuid4()), owner_id=user.id, title="Doc", checksum="chk", storage_key="k")
    ver = DocumentVersion(id=str(uuid.uuid4()), document_id=doc.id, version_number=1, storage_key="k")
    chunk = DocumentChunk(
        id=str(uuid.uuid4()),
        version_id=ver.id,
        page_start=1,
        page_end=1,
        chunk_index=0,
        content="Text",
        contextual_content="Text",
        checksum="c"
    )
    model = EmbeddingModel(
        id=str(uuid.uuid4()),
        provider="google",
        model_name="models/text-embedding-004",
        dimensions=768
    )
    db_session.add_all([user, doc, ver, chunk, model])
    db_session.commit()

    test_vector = [0.1] * 768
    emb = Embedding(
        id=str(uuid.uuid4()),
        chunk_id=chunk.id,
        model_id=model.id,
        embedding=test_vector
    )
    db_session.add(emb)
    db_session.commit()

    saved_emb = db_session.query(Embedding).filter_by(id=emb.id).first()
    assert len(saved_emb.embedding) == 768
    assert abs(saved_emb.embedding[0] - 0.1) < 1e-5


def test_retrieval_and_citation_evidence(db_session):
    """Verify retrieval runs, citations, answer claims, and claim evidence links."""
    user = User(id=str(uuid.uuid4()), firebase_uid=f"fb_{uuid.uuid4().hex[:8]}", email=f"u_{uuid.uuid4().hex[:8]}@cit.com")
    doc = Document(id=str(uuid.uuid4()), owner_id=user.id, title="Agreement", checksum="chk_a", storage_key="ka")
    ver = DocumentVersion(id=str(uuid.uuid4()), document_id=doc.id, version_number=1, storage_key="ka")
    chunk = DocumentChunk(
        id=str(uuid.uuid4()),
        version_id=ver.id,
        page_start=3,
        page_end=3,
        chunk_index=0,
        content="Governing Law: This Agreement is governed by the laws of New York.",
        contextual_content="Context...",
        checksum="c_gov"
    )
    convo = Conversation(id=str(uuid.uuid4()), user_id=user.id, title="Gov Law Query")
    msg = Message(id=str(uuid.uuid4()), conversation_id=convo.id, role="assistant", content="New York laws govern.")

    db_session.add_all([user, doc, ver, chunk, convo, msg])
    db_session.commit()

    # Citation
    cit = Citation(
        id=str(uuid.uuid4()),
        message_id=msg.id,
        chunk_id=chunk.id,
        page_number=3,
        section_label="Section 9. Governing Law",
        quoted_text="This Agreement is governed by the laws of New York."
    )
    # Claim & Evidence
    claim = AnswerClaim(
        id=str(uuid.uuid4()),
        message_id=msg.id,
        claim_text="The Agreement is subject to New York jurisdiction.",
        claim_type="document_fact",
        support_status="supported"
    )
    db_session.add_all([cit, claim])
    db_session.commit()

    evidence = ClaimEvidence(
        id=str(uuid.uuid4()),
        claim_id=claim.id,
        chunk_id=chunk.id,
        entailment_score=0.98,
        evidence_type="direct_quote"
    )
    db_session.add(evidence)
    db_session.commit()

    saved_claim = db_session.query(AnswerClaim).filter_by(id=claim.id).first()
    assert len(saved_claim.evidence) == 1
    assert saved_claim.evidence[0].entailment_score == 0.98


def test_processing_job_lifecycle(db_session):
    """Verify processing job status tracking."""
    user = User(id=str(uuid.uuid4()), firebase_uid=f"fb_{uuid.uuid4().hex[:8]}", email=f"u_{uuid.uuid4().hex[:8]}@job.com")
    doc = Document(id=str(uuid.uuid4()), owner_id=user.id, title="Patent", checksum="p1", storage_key="p1")
    ver = DocumentVersion(id=str(uuid.uuid4()), document_id=doc.id, version_number=1, storage_key="p1")
    db_session.add_all([user, doc, ver])
    db_session.commit()

    job = ProcessingJob(
        id=str(uuid.uuid4()),
        version_id=ver.id,
        job_type="extract",
        status="pending",
        attempts=0
    )
    db_session.add(job)
    db_session.commit()

    job.status = "processing"
    job.attempts = 1
    db_session.commit()

    job.status = "completed"
    db_session.commit()

    saved_job = db_session.query(ProcessingJob).filter_by(id=job.id).first()
    assert saved_job.status == "completed"
    assert saved_job.attempts == 1

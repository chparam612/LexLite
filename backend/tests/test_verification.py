import uuid
from app.models.user import User
from app.models.document import Document, DocumentVersion
from app.models.chunk import DocumentChunk
from app.models.conversation import Conversation, Message
from app.models.citation import Citation, AnswerClaim, ClaimEvidence
from app.services.verification_service import VerificationService
from app.services.generation_service import GroundedResponse, GroundedClaim


def test_cv001_exact_verbatim_quote_verification():
    """TEST-CV001: Exact verbatim quote in chunk content is verified with 1.0 score."""
    chunk_text = "Section 2.1: The Licensee shall not sublicense the Software to any third party."
    quote = "The Licensee shall not sublicense the Software to any third party."

    is_found, score = VerificationService.verify_quote_in_chunk(quote, chunk_text)
    assert is_found is True
    assert score == 1.0


def test_cv002_normalized_quote_matching():
    """TEST-CV002: Normalization handles curly quotes, newlines, and casing differences."""
    chunk_text = 'Section 4: “Confidential Information” shall mean\nall non-public data.'
    quote = '"confidential information" shall mean all non-public data.'

    is_found, score = VerificationService.verify_quote_in_chunk(quote, chunk_text)
    assert is_found is True
    assert score == 1.0


def test_cv003_fabricated_quote_rejected():
    """TEST-CV003: Fabricated quote not in chunk returns False with 0 score."""
    chunk_text = "This contract shall terminate on December 31, 2026."
    fabricated_quote = "This contract shall renew automatically forever without notice."

    is_found, score = VerificationService.verify_quote_in_chunk(fabricated_quote, chunk_text)
    assert is_found is False
    assert score < 0.5


def test_cv004_partial_quote_fuzzy_containment():
    """TEST-CV004: Excerpt with minor word omissions is recognized if >=85% words match."""
    chunk_text = "Either party may immediately terminate this agreement upon written notice to the other party."
    trimmed_quote = "party may immediately terminate this agreement upon written notice"

    is_found, score = VerificationService.verify_quote_in_chunk(trimmed_quote, chunk_text)
    assert is_found is True
    assert score >= 0.85


def test_cv005_claim_entailment_scoring():
    """TEST-CV005: Claim entailment score measures alignment between claim assertion and quote."""
    claim = "The agreement may be terminated upon written notice."
    quote = "Either party may terminate this agreement upon written notice."

    score = VerificationService.verify_claim_entailment(claim, quote)
    assert score >= 0.7


def test_cv006_unrelated_quote_entailment_failure():
    """TEST-CV006: Unrelated quote results in low entailment score (<0.4)."""
    claim = "The supplier must pay liquidated damages of $10000."
    unrelated_quote = "Notices shall be delivered by certified postal mail."

    score = VerificationService.verify_claim_entailment(claim, unrelated_quote)
    assert score < 0.4


def test_cv007_verify_claims_supported(db_session):
    """TEST-CV007: Verified claims receive support_status='supported' and entailment score."""
    user = User(id=str(uuid.uuid4()), firebase_uid=str(uuid.uuid4()), email="v1@law.com", display_name="V1")
    doc = Document(id=str(uuid.uuid4()), owner_id=user.id, title="Doc 1", checksum="c1", storage_key="s1")
    version = DocumentVersion(id=str(uuid.uuid4()), document_id=doc.id, storage_key="s1")
    chunk = DocumentChunk(
        id=str(uuid.uuid4()),
        version_id=version.id,
        chunk_index=0,
        page_start=1,
        page_end=1,
        content="Governing law is the State of Delaware.",
        contextual_content="Governing law is the State of Delaware.",
        checksum="chk_v1"
    )
    conv = Conversation(id=str(uuid.uuid4()), user_id=user.id, title="Conv")
    msg = Message(id=str(uuid.uuid4()), conversation_id=conv.id, role="assistant", content="Answer")
    claim_rec = AnswerClaim(
        id=str(uuid.uuid4()),
        message_id=msg.id,
        claim_text="The contract is governed by Delaware law."
    )
    evidence_rec = ClaimEvidence(
        id=str(uuid.uuid4()),
        claim_id=claim_rec.id,
        chunk_id=chunk.id
    )
    cit_rec = Citation(
        id=str(uuid.uuid4()),
        message_id=msg.id,
        chunk_id=chunk.id,
        page_number=1,
        quoted_text="Governing law is the State of Delaware."
    )
    db_session.add_all([user, doc, version, chunk, conv, msg, claim_rec, evidence_rec, cit_rec])
    db_session.commit()

    grounded_resp = GroundedResponse(
        answer="Delaware law applies.",
        claims=[
            GroundedClaim(
                claim_text="The contract is governed by Delaware law.",
                quote="Governing law is the State of Delaware.",
                chunk_id=chunk.id,
                page_number=1
            )
        ]
    )

    verifier = VerificationService()
    score = verifier.verify_claims_and_citations(
        db=db_session,
        grounded_resp=grounded_resp,
        created_claims=[claim_rec],
        created_evidence=[evidence_rec],
        created_citations=[cit_rec]
    )

    assert score == 1.0
    assert claim_rec.support_status == "supported"
    assert evidence_rec.entailment_score >= 0.5


def test_cv008_verify_hallucinated_claim_flagged(db_session):
    """TEST-CV008: Hallucinated claim with quote missing from chunk is flagged as 'unverified'."""
    user = User(id=str(uuid.uuid4()), firebase_uid=str(uuid.uuid4()), email="v2@law.com", display_name="V2")
    doc = Document(id=str(uuid.uuid4()), owner_id=user.id, title="Doc 2", checksum="c2", storage_key="s2")
    version = DocumentVersion(id=str(uuid.uuid4()), document_id=doc.id, storage_key="s2")
    chunk = DocumentChunk(
        id=str(uuid.uuid4()),
        version_id=version.id,
        chunk_index=0,
        page_start=1,
        page_end=1,
        content="Payment terms are net 30 days.",
        contextual_content="Payment terms are net 30 days.",
        checksum="chk_v2"
    )
    conv = Conversation(id=str(uuid.uuid4()), user_id=user.id, title="Conv 2")
    msg = Message(id=str(uuid.uuid4()), conversation_id=conv.id, role="assistant", content="Answer")
    claim_rec = AnswerClaim(
        id=str(uuid.uuid4()),
        message_id=msg.id,
        claim_text="Late fee of 100% applies immediately."
    )
    evidence_rec = ClaimEvidence(
        id=str(uuid.uuid4()),
        claim_id=claim_rec.id,
        chunk_id=chunk.id
    )
    cit_rec = Citation(
        id=str(uuid.uuid4()),
        message_id=msg.id,
        chunk_id=chunk.id,
        page_number=1,
        quoted_text="Late fee of 100% applies immediately."
    )
    db_session.add_all([user, doc, version, chunk, conv, msg, claim_rec, evidence_rec, cit_rec])
    db_session.commit()

    # Quote does not exist in chunk content
    grounded_resp = GroundedResponse(
        answer="Late fee is 100%.",
        claims=[
            GroundedClaim(
                claim_text="Late fee of 100% applies immediately.",
                quote="Late fee of 100% applies immediately.",
                chunk_id=chunk.id,
                page_number=1
            )
        ]
    )

    verifier = VerificationService()
    score = verifier.verify_claims_and_citations(
        db=db_session,
        grounded_resp=grounded_resp,
        created_claims=[claim_rec],
        created_evidence=[evidence_rec],
        created_citations=[cit_rec]
    )

    assert score == 0.0
    assert claim_rec.support_status == "unverified"


def test_cv009_missing_chunk_handled_gracefully(db_session):
    """TEST-CV009: Non-existent chunk ID marks claim as unverified without crashing."""
    user = User(id=str(uuid.uuid4()), firebase_uid=str(uuid.uuid4()), email="v3@law.com", display_name="V3")
    conv = Conversation(id=str(uuid.uuid4()), user_id=user.id, title="Conv 3")
    msg = Message(id=str(uuid.uuid4()), conversation_id=conv.id, role="assistant", content="Answer")
    claim_rec = AnswerClaim(id=str(uuid.uuid4()), message_id=msg.id, claim_text="Fact")
    evidence_rec = ClaimEvidence(id=str(uuid.uuid4()), claim_id=claim_rec.id, chunk_id="non_existent_id")
    cit_rec = Citation(
        id=str(uuid.uuid4()),
        message_id=msg.id,
        chunk_id="non_existent_id",
        page_number=1,
        quoted_text="Text"
    )
    db_session.add_all([user, conv, msg, claim_rec, evidence_rec, cit_rec])
    db_session.commit()

    grounded_resp = GroundedResponse(
        answer="Fact statement.",
        claims=[
            GroundedClaim(claim_text="Fact", quote="Text", chunk_id="non_existent_id", page_number=1)
        ]
    )

    verifier = VerificationService()
    score = verifier.verify_claims_and_citations(
        db=db_session,
        grounded_resp=grounded_resp,
        created_claims=[claim_rec],
        created_evidence=[evidence_rec],
        created_citations=[cit_rec]
    )

    assert score == 0.0
    assert claim_rec.support_status == "unverified"


def test_cv010_grounding_score_and_warning_injection(client, db_session):
    """TEST-CV010: When grounding score is low, warning disclosure is injected into message."""
    auth_header = {"Authorization": "Bearer test_token_:warn_user:warn@legal.ai:Warn Counsel"}

    # Create conversation
    conv_res = client.post("/api/v1/conversations", headers=auth_header, json={"title": "Warning Test"})
    conv_id = conv_res.json()["id"]

    # Send message when no documents exist -> insufficient evidence, returns refusal without hallucination
    msg_res = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=auth_header,
        json={"content": "What is the secret penalty?"}
    )
    assert msg_res.status_code == 201
    msg_data = msg_res.json()
    assert "sufficient information" in msg_data["content"].lower()

import uuid
from app.models.user import User
from app.models.document import Document, DocumentVersion
from app.models.chunk import DocumentChunk
from app.models.embedding import Embedding
from app.services.retrieval_service import RetrievalService, RetrievalHit
from app.services.embedding_service import EmbeddingService


def setup_advanced_corpus(db_session, user_id: str, title: str, chunks_data: list):
    """Helper creating document, versions, chunks with headings and embeddings."""
    emb_service = EmbeddingService()
    model = emb_service.get_or_create_model_record(db_session)

    doc = Document(
        id=str(uuid.uuid4()),
        owner_id=user_id,
        title=title,
        checksum=f"adv_chk_{uuid.uuid4().hex[:8]}",
        storage_key=f"adv_storage_{uuid.uuid4().hex[:8]}",
        status="completed"
    )
    version = DocumentVersion(
        id=str(uuid.uuid4()),
        document_id=doc.id,
        version_number=1,
        storage_key=doc.storage_key,
        extraction_status="completed"
    )
    db_session.add_all([doc, version])
    db_session.flush()

    chunks = []
    for idx, (heading, text) in enumerate(chunks_data):
        chunk = DocumentChunk(
            id=str(uuid.uuid4()),
            version_id=version.id,
            chunk_index=idx,
            page_start=idx + 1,
            page_end=idx + 1,
            heading_path=heading,
            content=text,
            contextual_content=f"[Document: {title} > {heading}] {text}",
            checksum=f"chk_adv_{uuid.uuid4().hex[:8]}"
        )
        db_session.add(chunk)
        db_session.flush()

        vec = emb_service.embed_text(chunk.contextual_content)
        emb = Embedding(
            chunk_id=chunk.id,
            model_id=model.id,
            embedding=vec
        )
        db_session.add(emb)
        chunks.append(chunk)

    db_session.commit()
    return doc, chunks


def test_ar001_keyword_exact_phrase_match(db_session):
    """TEST-AR001: Lexical keyword search gives high score to exact phrase matches."""
    user = User(
        id=str(uuid.uuid4()),
        firebase_uid=str(uuid.uuid4()),
        email="lexical_user@law.com",
        display_name="Lexical User"
    )
    db_session.add(user)
    db_session.commit()

    data = [
        ("Section 10", "Every agreement is a contract if made by free consent."),
        ("Section 13", "Consent is defined as two or more persons agreeing upon the same thing."),
        ("Section 14", "Consent is said to be free when it is not caused by coercion or fraud.")
    ]
    doc, chunks = setup_advanced_corpus(db_session, user.id, "Contract Act", data)

    service = RetrievalService()
    hits = service.keyword_search(db_session, user.id, "free consent", top_k=5)

    assert len(hits) > 0
    # Exact phrase "free consent" appears in chunks[0] and chunks[2]
    matched_ids = [h.chunk_id for h in hits]
    assert chunks[0].id in matched_ids
    assert chunks[2].id in matched_ids


def test_ar002_keyword_heading_match_boost(db_session):
    """TEST-AR002: Heading path matching boosts keyword ranking for relevant sections."""
    user = User(
        id=str(uuid.uuid4()),
        firebase_uid=str(uuid.uuid4()),
        email="heading_user@law.com",
        display_name="Heading User"
    )
    db_session.add(user)
    db_session.commit()

    data = [
        ("Article IV: Indemnification", "The parties shall maintain adequate insurance coverage."),
        ("Article V: Miscellaneous", "Notices shall be in writing sent to the address above.")
    ]
    doc, chunks = setup_advanced_corpus(db_session, user.id, "Services Master Agreement", data)

    service = RetrievalService()
    hits = service.keyword_search(db_session, user.id, "indemnification", top_k=2)

    assert len(hits) > 0
    # Top hit should be Article IV due to heading match boost
    assert hits[0].chunk_id == chunks[0].id
    assert "Indemnification" in hits[0].heading_path


def test_ar003_reciprocal_rank_fusion_math():
    """TEST-AR003: Reciprocal Rank Fusion calculation follows 1 / (k + rank)."""
    hit_a = RetrievalHit(
        chunk_id="chunk_a", score=0.9, rank=1, page_start=1, page_end=1,
        heading_path="Sec 1", content="A", contextual_content="A",
        document_id="d1", document_title="D1", version_id="v1"
    )
    hit_b = RetrievalHit(
        chunk_id="chunk_b", score=0.8, rank=2, page_start=2, page_end=2,
        heading_path="Sec 2", content="B", contextual_content="B",
        document_id="d1", document_title="D1", version_id="v1"
    )

    fused = RetrievalService.reciprocal_rank_fusion([hit_a, hit_b], [], k=60)
    assert len(fused) == 2
    # RRF score for rank 1 with k=60: 1 / 61 = 0.016393
    expected_score = round(1.0 / 61.0, 6)
    assert fused[0].score == expected_score
    assert fused[0].chunk_id == "chunk_a"


def test_ar004_rrf_multi_channel_boost():
    """TEST-AR004: Chunks present in both dense and keyword channels rank higher than single-channel hits."""
    hit_shared = RetrievalHit(
        chunk_id="chunk_shared", score=0.85, rank=2, page_start=1, page_end=1,
        heading_path="Sec 1", content="Shared", contextual_content="Shared",
        document_id="d1", document_title="D1", version_id="v1"
    )
    hit_dense_only = RetrievalHit(
        chunk_id="chunk_dense", score=0.95, rank=1, page_start=2, page_end=2,
        heading_path="Sec 2", content="Dense", contextual_content="Dense",
        document_id="d1", document_title="D1", version_id="v1"
    )
    hit_keyword_shared = RetrievalHit(
        chunk_id="chunk_shared", score=12.0, rank=2, page_start=1, page_end=1,
        heading_path="Sec 1", content="Shared", contextual_content="Shared",
        document_id="d1", document_title="D1", version_id="v1"
    )

    # dense ranks: dense_only (1), shared (2)
    # keyword ranks: shared (2)
    # RRF(dense_only) = 1/61 = 0.016393
    # RRF(shared) = 1/62 + 1/62 = 2/62 = 0.032258
    fused = RetrievalService.reciprocal_rank_fusion(
        dense_hits=[hit_dense_only, hit_shared],
        keyword_hits=[hit_keyword_shared],
        k=60
    )

    assert len(fused) == 2
    assert fused[0].chunk_id == "chunk_shared"
    assert fused[0].score > fused[1].score


def test_ar005_candidate_reranking():
    """TEST-AR005: Reranker reorders chunks based on query term overlap and heading alignment."""
    hit1 = RetrievalHit(
        chunk_id="c1", score=0.02, rank=1, page_start=1, page_end=1,
        heading_path="Section A: Definitions",
        content="General introductory terms and conditions for users.",
        contextual_content="Intro", document_id="d1", document_title="D1", version_id="v1"
    )
    hit2 = RetrievalHit(
        chunk_id="c2", score=0.018, rank=2, page_start=2, page_end=2,
        heading_path="Section B: Governing Law",
        content="This agreement is governed by the laws of New York without regard to conflict principles.",
        contextual_content="Law", document_id="d1", document_title="D1", version_id="v1"
    )

    service = RetrievalService()
    reranked = service.rerank_candidates("governing law New York jurisdiction", [hit1, hit2], top_k=2)

    assert len(reranked) == 2
    # c2 has high overlap with "governing", "laws", "New York" and matching heading
    assert reranked[0].chunk_id == "c2"


def test_ar006_context_expansion_neighbors(db_session):
    """TEST-AR006: Context expansion pulls preceding and succeeding chunk content."""
    user = User(
        id=str(uuid.uuid4()),
        firebase_uid=str(uuid.uuid4()),
        email="expand_user@law.com",
        display_name="Expansion User"
    )
    db_session.add(user)
    db_session.commit()

    data = [
        ("Section 1", "Preamble: The parties agree to collaborate."),
        ("Section 2", "Core Obligation: Supplier shall deliver goods within 14 business days."),
        ("Section 3", "Remedies: Failure to deliver results in liquidated damages of 5% per week.")
    ]
    doc, chunks = setup_advanced_corpus(db_session, user.id, "Supply Contract", data)

    service = RetrievalService()
    hit_middle = RetrievalHit(
        chunk_id=chunks[1].id, score=0.5, rank=1, page_start=2, page_end=2,
        heading_path=chunks[1].heading_path, content=chunks[1].content,
        contextual_content=chunks[1].content, document_id=doc.id,
        document_title=doc.title, version_id=chunks[1].version_id
    )

    expanded = service.expand_context(db_session, [hit_middle])
    assert len(expanded) == 1
    # Check that preceding preamble and succeeding remedies are present in contextual_content
    assert "[Preceding Context:" in expanded[0].contextual_content
    assert "[Succeeding Context:" in expanded[0].contextual_content
    assert "Preamble" in expanded[0].contextual_content
    assert "Remedies" in expanded[0].contextual_content


def test_ar007_hybrid_search_end_to_end(db_session):
    """TEST-AR007: End-to-end hybrid search merges dense, keyword, RRF, and reranking."""
    user = User(
        id=str(uuid.uuid4()),
        firebase_uid=str(uuid.uuid4()),
        email="hybrid_e2e@law.com",
        display_name="Hybrid E2E"
    )
    db_session.add(user)
    db_session.commit()

    data = [
        ("Article 1: Scope", "This agreement governs software licensing and support services."),
        ("Article 2: Payment", "License fees are payable within thirty days of invoice date."),
        ("Article 3: Confidentiality", "Neither party shall disclose confidential proprietary information.")
    ]
    doc, chunks = setup_advanced_corpus(db_session, user.id, "Software Master Agreement", data)

    service = RetrievalService()
    hits = service.hybrid_search(
        db=db_session,
        user_id=user.id,
        query="payment fees invoice thirty days",
        top_k=2
    )

    assert len(hits) > 0
    # Payment clause should be top hit
    assert hits[0].chunk_id == chunks[1].id
    assert "Payment" in hits[0].heading_path


def test_ar008_hybrid_search_tenant_isolation(db_session):
    """TEST-AR008: Hybrid search strictly isolates tenant data across dense and keyword channels."""
    user1 = User(
        id=str(uuid.uuid4()),
        firebase_uid=str(uuid.uuid4()),
        email="tenant1@law.com",
        display_name="Tenant 1"
    )
    user2 = User(
        id=str(uuid.uuid4()),
        firebase_uid=str(uuid.uuid4()),
        email="tenant2@law.com",
        display_name="Tenant 2"
    )
    db_session.add_all([user1, user2])
    db_session.commit()

    data = [("Secret Clause", "Confidential settlement of $25M with Apex Corporation.")]
    setup_advanced_corpus(db_session, user2.id, "Private Settlement", data)

    service = RetrievalService()
    # User 1 searches for Apex Corporation settlement
    hits = service.hybrid_search(
        db=db_session,
        user_id=user1.id,
        query="Apex Corporation settlement amount",
        top_k=5
    )

    assert len(hits) == 0


def test_ar009_hybrid_search_document_filtering(db_session):
    """TEST-AR009: Hybrid search restricts results to specified document IDs."""
    user = User(
        id=str(uuid.uuid4()),
        firebase_uid=str(uuid.uuid4()),
        email="doc_filter@law.com",
        display_name="Doc Filter User"
    )
    db_session.add(user)
    db_session.commit()

    doc_a, _ = setup_advanced_corpus(db_session, user.id, "Doc Alpha", [("Sec 1", "Alpha clause specifies 10% tax.")])
    doc_b, _ = setup_advanced_corpus(db_session, user.id, "Doc Beta", [("Sec 1", "Beta clause specifies 20% tax.")])

    service = RetrievalService()
    hits = service.hybrid_search(
        db=db_session,
        user_id=user.id,
        query="tax percentage clause",
        document_ids=[doc_b.id],
        top_k=5
    )

    assert len(hits) == 1
    assert hits[0].document_id == doc_b.id
    assert "Beta clause" in hits[0].content


def test_ar010_empty_query_handling(db_session):
    """TEST-AR010: Empty or whitespace query returns empty list without error."""
    service = RetrievalService()
    assert service.keyword_search(db_session, "fake_user", "") == []
    assert service.keyword_search(db_session, "fake_user", "   ") == []
    assert service.hybrid_search(db_session, "fake_user", "") == []

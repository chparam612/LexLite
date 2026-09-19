import uuid
from app.models.user import User
from app.models.document import Document, DocumentVersion
from app.models.chunk import DocumentChunk
from app.models.conversation import Conversation, Message
from app.models.retrieval import RetrievalRun
from app.evaluation.rag_evaluator import RAGEvaluator, EvaluationSample
from app.workers.processing_worker import DocumentProcessingPipeline
from tests.conftest import create_sample_pdf_bytes


def test_e2e001_rag_benchmark_evaluation(db_session):
    """TEST-E2E001: Automated RAG benchmark achieves >=90% Faithfulness and generates scorecard."""
    user = User(
        id=str(uuid.uuid4()),
        firebase_uid=str(uuid.uuid4()),
        email="eval_user@legal.ai",
        display_name="Benchmark Lead"
    )
    db_session.add(user)
    db_session.commit()

    from tests.test_advanced_retrieval import setup_advanced_corpus
    contract_data = [
        ("Section 1: Term", "This Agreement commences on January 1, 2025 and expires December 31, 2027."),
        ("Section 2: Fees", "Consultant shall be paid $250 per hour payable net thirty days."),
        ("Section 3: IP Rights", "All work product and inventions created hereunder belong exclusively to Client.")
    ]
    doc, chunks = setup_advanced_corpus(db_session, user.id, "Consulting Master Services", contract_data)

    evaluator = RAGEvaluator()
    samples = [
        EvaluationSample(
            query="When does the agreement term expire?",
            expected_answer_keywords=["expires", "December 31, 2027"],
            expected_chunk_ids=[chunks[0].id]
        ),
        EvaluationSample(
            query="What are the consultant fees paid per hour?",
            expected_answer_keywords=["$250", "hour"],
            expected_chunk_ids=[chunks[1].id]
        ),
        EvaluationSample(
            query="Who owns the work product and inventions created?",
            expected_answer_keywords=["Client", "inventions"],
            expected_chunk_ids=[chunks[2].id]
        )
    ]

    metrics = evaluator.evaluate_benchmark(db_session, user.id, samples, top_k=3)

    assert metrics.total_samples == 3
    assert metrics.faithfulness_score >= 0.90
    assert metrics.answer_relevance_score >= 0.80
    assert metrics.context_recall >= 0.90
    assert metrics.average_latency_ms < 500.0

    report = evaluator.generate_markdown_report(metrics)
    assert "Faithfulness" in report
    assert "PASS" in report


def test_e2e002_complete_user_journey(client, db_session):
    """
    TEST-E2E002: Complete End-to-End User Journey from Registration to Citation Verification.
    1. Authenticate user
    2. Upload legal agreement
    3. Ingestion pipeline worker processes document
    4. Document status reaches 'completed'
    5. User creates research session
    6. User posts query and receives assistant answer
    7. Citations and claims verified
    8. Audit log confirmed
    9. Cleanup session
    """
    auth_header = {"Authorization": "Bearer test_token_:journey_user:journey@legal.ai:Journey Counsel"}

    # 1. Inspect user profile
    me_res = client.get("/api/v1/auth/me", headers=auth_header)
    assert me_res.status_code == 200
    user_info = me_res.json()
    assert user_info["email"] == "journey@legal.ai"

    # 2. Upload Document
    pdf_content = (
        "EMPLOYMENT AGREEMENT\n\n"
        "Section 1. Position and Duties.\n"
        "Employee shall serve as General Counsel reporting to the CEO.\n\n"
        "Section 2. Non-Compete Covenant.\n"
        "During employment and for twelve months thereafter, Employee shall not engage in competing legal services.\n\n"
        "Section 3. Governing Law.\n"
        "This agreement shall be governed by the laws of California."
    )
    pdf_bytes = create_sample_pdf_bytes(pdf_content)

    upload_res = client.post(
        "/api/v1/documents/upload",
        headers=auth_header,
        files={"file": ("employment_counsel.pdf", pdf_bytes, "application/pdf")},
        data={"title": "Executive Employment Agreement", "jurisdiction": "California"}
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document"]["id"]

    # 3. Synchronously execute ingestion pipeline in test database
    version = db_session.query(DocumentVersion).filter_by(document_id=doc_id).first()
    assert version is not None
    success = DocumentProcessingPipeline.process_document_version(db_session, version.id)
    assert success is True

    # 4. Verify Document Status
    doc_record = db_session.query(Document).filter_by(id=doc_id).first()
    assert doc_record.status == "completed"
    assert doc_record.page_count >= 1

    chunks = db_session.query(DocumentChunk).filter_by(version_id=version.id).all()
    assert len(chunks) >= 1

    # 5. Create Research Session / Conversation
    conv_res = client.post(
        "/api/v1/conversations",
        headers=auth_header,
        json={"title": "Executive Non-Compete Review", "document_ids": [doc_id]}
    )
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["id"]

    # 6. Post Query
    msg_res = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=auth_header,
        json={"content": "What is the non-compete restriction period?"}
    )
    assert msg_res.status_code == 201
    assistant_msg = msg_res.json()
    assert assistant_msg["role"] == "assistant"
    assert len(assistant_msg["citations"]) >= 1

    # 7. Verify Citation Details
    top_citation = assistant_msg["citations"][0]
    assert top_citation["page_number"] >= 1
    assert "twelve months" in top_citation["quoted_text"].lower() or "competing" in top_citation["quoted_text"].lower()

    # 8. Check Retrieval Audit Run
    retrieval_run = db_session.query(RetrievalRun).filter_by(message_id=assistant_msg["id"]).first()
    assert retrieval_run is not None
    assert retrieval_run.retrieval_method in ("dense", "hybrid")

    # 9. Cascade Deletion of Session
    del_res = client.delete(f"/api/v1/conversations/{conv_id}", headers=auth_header)
    assert del_res.status_code == 204
    assert db_session.query(Conversation).filter_by(id=conv_id).first() is None
    assert db_session.query(Message).filter_by(conversation_id=conv_id).count() == 0


def test_e2e003_multi_turn_history(client, db_session):
    """TEST-E2E003: Multi-turn conversational interaction records consecutive messages."""
    auth_header = {"Authorization": "Bearer test_token_:mt_user:mt@legal.ai:MultiTurn"}

    conv_res = client.post("/api/v1/conversations", headers=auth_header, json={"title": "Multi-Turn Session"})
    conv_id = conv_res.json()["id"]

    # Turn 1
    client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=auth_header,
        json={"content": "Question 1: What are the obligations?"}
    )

    # Turn 2
    client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=auth_header,
        json={"content": "Question 2: Are there exemptions?"}
    )

    # Fetch conversation details
    detail_res = client.get(f"/api/v1/conversations/{conv_id}", headers=auth_header)
    assert detail_res.status_code == 200
    messages = detail_res.json()["messages"]
    # 2 user messages + 2 assistant messages = 4 messages
    assert len(messages) == 4
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "user"
    assert messages[3]["role"] == "assistant"

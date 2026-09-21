from fastapi.testclient import TestClient
from app.services.demo_document_service import get_sample_rental_agreement_bytes
from app.workers.processing_worker import DocumentProcessingPipeline


def test_demo_001_valid_pdf_upload(client: TestClient, db_session):
    """DEMO-001: Upload valid synthetic rental agreement PDF and complete ingestion."""
    pdf_bytes = get_sample_rental_agreement_bytes()
    auth_header = {"Authorization": "Bearer test_token_:demo_judge:judge@legalai.example.com:Judge One"}

    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_header,
        files={"file": ("Sample_Residential_Rental_Agreement_Fictional_Demo.pdf", pdf_bytes, "application/pdf")},
        data={"title": "Sample Residential Rental Agreement — Fictional Demo", "jurisdiction": "State of New York"}
    )
    assert response.status_code == 201
    doc_data = response.json()["document"]
    doc_id = doc_data["id"]
    assert doc_data["page_count"] == 3

    # Run processing pipeline to completion
    detail_res = client.get(f"/api/v1/documents/{doc_id}", headers=auth_header)
    version_id = detail_res.json()["versions"][0]["id"]
    success = DocumentProcessingPipeline.process_document_version(db_session, version_id)
    assert success is True

    # Check status
    status_res = client.get(f"/api/v1/documents/{doc_id}/status", headers=auth_header)
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "completed"
    assert status_res.json()["progress_percentage"] == 100


def test_demo_002_grounded_clause_question(client: TestClient, db_session):
    """DEMO-002: Ask question about termination notice; receive grounded answer with citation."""
    auth_header = {"Authorization": "Bearer test_token_:demo_judge:judge@legalai.example.com:Judge One"}

    # Setup demo document via 1-click endpoint
    load_res = client.post("/api/v1/demo/load-sample", headers=auth_header)
    assert load_res.status_code == 201
    doc_id = load_res.json()["id"]

    # Create conversation attached to document
    conv_res = client.post(
        "/api/v1/conversations",
        headers=auth_header,
        json={"title": "Termination Notice Inquiry", "document_ids": [doc_id]}
    )
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["id"]

    # Send query
    msg_res = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=auth_header,
        json={"content": "What is the required termination notice period?"}
    )
    assert msg_res.status_code == 201
    data = msg_res.json()
    assert data["role"] == "assistant"
    assert len(data["citations"]) > 0
    assert data["citations"][0]["page_number"] in [1, 2, 3]
    assert data["processing_details"] is not None
    assert data["processing_details"]["retrieval_method"] is not None


def test_demo_003_different_dynamic_question(client: TestClient, db_session):
    """DEMO-003: Ask a different question about late rent; answer is grounded in late fee clause."""
    auth_header = {"Authorization": "Bearer test_token_:demo_judge:judge@legalai.example.com:Judge One"}

    load_res = client.post("/api/v1/demo/load-sample", headers=auth_header)
    doc_id = load_res.json()["id"]

    conv_res = client.post(
        "/api/v1/conversations",
        headers=auth_header,
        json={"title": "Late Payment Inquiry", "document_ids": [doc_id]}
    )
    conv_id = conv_res.json()["id"]

    msg_res = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=auth_header,
        json={"content": "What happens if rent is paid late?"}
    )
    assert msg_res.status_code == 201
    data = msg_res.json()
    assert data["role"] == "assistant"
    assert len(data["citations"]) > 0
    assert data["citations"][0]["page_number"] in [1, 2, 3]
    assert data["processing_details"] is not None


def test_demo_004_unsupported_out_of_scope_question(client: TestClient, db_session):
    """DEMO-004: Ask out-of-scope question; system must state documents lack evidence and avoid hallucination."""
    auth_header = {"Authorization": "Bearer test_token_:demo_judge:judge@legalai.example.com:Judge One"}

    # Conversation with no relevant documents
    conv_res = client.post(
        "/api/v1/conversations",
        headers=auth_header,
        json={"title": "Out-of-Scope Inquiry", "document_ids": []}
    )
    conv_id = conv_res.json()["id"]

    msg_res = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=auth_header,
        json={"content": "What is the punishment for murder under Indian law?"}
    )
    assert msg_res.status_code == 201
    content = msg_res.json()["content"].lower()
    assert "not contain sufficient information" in content or "insufficient" in content
    assert len(msg_res.json()["citations"]) == 0


def test_demo_005_invalid_file_upload_rejected(client: TestClient):
    """DEMO-005: Upload unsupported non-PDF file (.exe); must be rejected with validation error."""
    auth_header = {"Authorization": "Bearer test_token_:demo_judge:judge@legalai.example.com:Judge One"}

    fake_exe = b"MZ\x90\x00\x03\x00\x00\x00"
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_header,
        files={"file": ("malicious_payload.exe", fake_exe, "application/octet-stream")},
        data={"title": "Malware Executable"}
    )
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["error"]["message"]


def test_demo_006_empty_question_rejected(client: TestClient):
    """DEMO-006: Send whitespace-only question; must be rejected with clear message."""
    auth_header = {"Authorization": "Bearer test_token_:demo_judge:judge@legalai.example.com:Judge One"}

    conv_res = client.post(
        "/api/v1/conversations",
        headers=auth_header,
        json={"title": "Empty Test", "document_ids": []}
    )
    conv_id = conv_res.json()["id"]

    response = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=auth_header,
        json={"content": "   "}
    )
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["error"]["message"]


def test_demo_007_citation_inspection_fidelity(client: TestClient, db_session):
    """DEMO-007: Verify citation inspection contains document name, page, and quoted text."""
    auth_header = {"Authorization": "Bearer test_token_:demo_judge:judge@legalai.example.com:Judge One"}

    load_res = client.post("/api/v1/demo/load-sample", headers=auth_header)
    doc_id = load_res.json()["id"]

    conv_res = client.post(
        "/api/v1/conversations",
        headers=auth_header,
        json={"title": "Citation Inspection Test", "document_ids": [doc_id]}
    )
    conv_id = conv_res.json()["id"]

    msg_res = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=auth_header,
        json={"content": "What is the monthly rent amount?"}
    )
    assert msg_res.status_code == 201
    citations = msg_res.json()["citations"]
    assert len(citations) > 0
    cit = citations[0]
    assert cit["chunk_id"] is not None
    assert cit["page_number"] >= 1
    assert len(cit["quoted_text"]) > 0


def test_demo_008_dynamic_answer_divergence(client: TestClient, db_session):
    """DEMO-008: Verify different questions on same document produce dynamic, distinct responses."""
    auth_header = {"Authorization": "Bearer test_token_:demo_judge:judge@legalai.example.com:Judge One"}

    load_res = client.post("/api/v1/demo/load-sample", headers=auth_header)
    doc_id = load_res.json()["id"]

    conv_res = client.post(
        "/api/v1/conversations",
        headers=auth_header,
        json={"title": "Dynamic Divergence Test", "document_ids": [doc_id]}
    )
    conv_id = conv_res.json()["id"]

    # Question A: Notice
    msg_a = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=auth_header,
        json={"content": "What is the required termination notice period?"}
    )

    # Question B: Maintenance
    msg_b = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=auth_header,
        json={"content": "Who is responsible for heating and plumbing repairs?"}
    )

    assert msg_a.status_code == 201
    assert msg_b.status_code == 201
    # Ensure answers are not hardcoded identical strings
    assert msg_a.json()["content"] != msg_b.json()["content"]

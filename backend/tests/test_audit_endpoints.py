from fastapi import status
from tests.conftest import create_sample_pdf_bytes


def test_auth_verify_endpoint(client):
    """Verify POST /api/v1/auth/verify returns valid status and user profile."""
    auth_header = {"Authorization": "Bearer test_token_:audit_user:audit@legal.ai:Audit User"}
    res = client.post("/api/v1/auth/verify", headers=auth_header)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["status"] == "valid"
    assert data["user"]["email"] == "audit@legal.ai"


def test_auth_verify_unauthorized(client):
    """Verify POST /api/v1/auth/verify rejects unauthenticated requests."""
    res = client.post("/api/v1/auth/verify")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_direct_chat_endpoint(client):
    """Verify POST /api/v1/chat creates conversation on the fly if omitted and returns grounded response."""
    auth_header = {"Authorization": "Bearer test_token_:audit_user:audit@legal.ai:Audit User"}
    res = client.post(
        "/api/v1/chat",
        headers=auth_header,
        json={"content": "What is the penalty for late tax filing in India?"}
    )
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["role"] == "assistant"
    assert "conversation_id" in data
    assert "insufficient" in data["content"].lower() or "contain" in data["content"].lower()


def test_message_citations_endpoint(client):
    """Verify GET /api/v1/messages/{message_id}/citations returns citations list."""
    auth_header = {"Authorization": "Bearer test_token_:audit_user:audit@legal.ai:Audit User"}
    chat_res = client.post(
        "/api/v1/chat",
        headers=auth_header,
        json={"content": "What is the general contract law rule?"}
    )
    msg_id = chat_res.json()["id"]

    res = client.get(f"/api/v1/messages/{msg_id}/citations", headers=auth_header)
    assert res.status_code == status.HTTP_200_OK
    assert isinstance(res.json(), list)


def test_document_download_endpoint(client):
    """Verify GET /api/v1/documents/{document_id}/download streams the raw PDF bytes."""
    auth_header = {"Authorization": "Bearer test_token_:audit_user:audit@legal.ai:Audit User"}
    pdf_bytes = create_sample_pdf_bytes("Download Test Agreement")
    up_res = client.post(
        "/api/v1/documents/upload",
        headers=auth_header,
        files={"file": ("contract.pdf", pdf_bytes, "application/pdf")},
        data={"title": "Download Test Document"}
    )
    doc_id = up_res.json()["document"]["id"]

    dl_res = client.get(f"/api/v1/documents/{doc_id}/download", headers=auth_header)
    assert dl_res.status_code == status.HTTP_200_OK
    assert dl_res.headers["content-type"] == "application/pdf"
    assert len(dl_res.content) == len(pdf_bytes)

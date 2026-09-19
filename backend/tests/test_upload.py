import fitz
from fastapi import status
from app.utils.file_utils import sanitize_filename


def make_test_pdf(text: str = "Legal Service Agreement Clause 1") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_fv001_valid_pdf_accepted(client):
    """TEST-FV001: Valid PDF is accepted and document record is created."""
    pdf_data = make_test_pdf("Valid Contract Terms")
    auth_header = {"Authorization": "Bearer test_token_:user_fv1:fv1@law.com:Lawyer One"}

    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_header,
        files={"file": ("employment_agreement.pdf", pdf_data, "application/pdf")},
        data={"title": "Employment Agreement", "jurisdiction": "Delaware"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "uploaded"
    assert data["document"]["title"] == "Employment Agreement"
    assert data["document"]["page_count"] == 1
    assert data["document"]["file_size"] > 0
    assert len(data["document"]["checksum"]) == 64


def test_fv002_non_pdf_file_rejected(client):
    """TEST-FV002: Non-PDF file is rejected."""
    auth_header = {"Authorization": "Bearer test_token_:user_fv2:fv2@law.com:Lawyer Two"}
    fake_text = b"This is plain text, not a PDF."

    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_header,
        files={"file": ("notes.txt", fake_text, "text/plain")}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid file extension" in response.json()["error"]["message"]


def test_fv003_incorrect_mime_safely_inspected(client):
    """TEST-FV003: Incorrect MIME type with non-pdf payload is rejected."""
    auth_header = {"Authorization": "Bearer test_token_:user_fv3:fv3@law.com:Lawyer Three"}
    malicious_payload = b"<html><script>alert(1)</script></html>"

    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_header,
        files={"file": ("exploit.pdf", malicious_payload, "application/pdf")}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "magic bytes missing" in response.json()["error"]["message"].lower()


def test_fv004_empty_file_rejected(client):
    """TEST-FV004: Empty file (0 bytes) is rejected."""
    auth_header = {"Authorization": "Bearer test_token_:user_fv4:fv4@law.com:Lawyer Four"}

    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_header,
        files={"file": ("empty.pdf", b"", "application/pdf")}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "empty" in response.json()["error"]["message"].lower()


def test_fv005_corrupted_pdf_handled_gracefully(client):
    """TEST-FV005: Corrupted PDF bytes starting with %PDF- are rejected gracefully."""
    auth_header = {"Authorization": "Bearer test_token_:user_fv5:fv5@law.com:Lawyer Five"}
    corrupt_pdf = b"%PDF-1.4\nCorrupted binary garbage without xref or trailer"

    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_header,
        files={"file": ("corrupt.pdf", corrupt_pdf, "application/pdf")}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "corrupted" in response.json()["error"]["message"].lower()


def test_fv006_file_exceeding_size_limit_rejected(client, monkeypatch):
    """TEST-FV006: File exceeding size limit is rejected."""
    from app.core import config
    monkeypatch.setattr(config.settings, "MAX_UPLOAD_SIZE_MB", 1)  # Set limit to 1MB

    auth_header = {"Authorization": "Bearer test_token_:user_fv6:fv6@law.com:Lawyer Six"}
    oversized_data = b"%PDF-" + b"0" * (2 * 1024 * 1024)  # 2MB

    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_header,
        files={"file": ("large.pdf", oversized_data, "application/pdf")}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "exceeds maximum allowed limit" in response.json()["error"]["message"]


def test_fv007_path_traversal_filename_sanitized():
    """TEST-FV007: Filename containing path traversal characters is sanitized."""
    malicious_names = [
        "../../../../etc/passwd.pdf",
        "..\\..\\windows\\system32\\cmd.pdf",
        "/var/log/syslog.pdf",
        "nested/dir/document.pdf"
    ]
    for raw in malicious_names:
        clean = sanitize_filename(raw)
        assert "/" not in clean
        assert "\\" not in clean
        assert ".." not in clean
        assert clean.endswith(".pdf")


def test_fv008_special_characters_handled_safely():
    """TEST-FV008: Filename containing special characters is handled safely."""
    raw = "Contract #123 & Annexure (Final) [v2]!@#$%^.pdf"
    clean = sanitize_filename(raw)
    assert clean.endswith(".pdf")
    assert not any(c in clean for c in ["#", "@", "$", "%", "^", "!", "[", "]", "&"])


def test_fv009_duplicate_checksum_detected(client):
    """TEST-FV009: Duplicate file checksum is detected and safely reuses document."""
    pdf_data = make_test_pdf("Duplicate Agreement Testing")
    auth_header = {"Authorization": "Bearer test_token_:user_fv9:fv9@law.com:Lawyer Nine"}

    # Upload 1
    resp1 = client.post(
        "/api/v1/documents/upload",
        headers=auth_header,
        files={"file": ("doc_v1.pdf", pdf_data, "application/pdf")}
    )
    assert resp1.status_code == status.HTTP_201_CREATED
    doc_id_1 = resp1.json()["document"]["id"]

    # Upload 2 with identical content
    resp2 = client.post(
        "/api/v1/documents/upload",
        headers=auth_header,
        files={"file": ("doc_v2.pdf", pdf_data, "application/pdf")}
    )
    assert resp2.status_code == status.HTTP_201_CREATED
    doc_id_2 = resp2.json()["document"]["id"]

    assert doc_id_1 == doc_id_2


def test_fv011_unsupported_file_extension_rejected(client):
    """TEST-FV011: Unsupported file extension is rejected."""
    auth_header = {"Authorization": "Bearer test_token_:user_fv11:fv11@law.com:Lawyer Eleven"}
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_header,
        files={"file": ("script.py", b"print('hello')", "text/x-python")}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_fv012_upload_without_auth_rejected(client):
    """TEST-FV012: Upload without authentication is rejected with HTTP 401."""
    pdf_data = make_test_pdf("Unauthenticated Upload")
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("unauth.pdf", pdf_data, "application/pdf")}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_sec001_and_sec004_ownership_isolation(client):
    """TEST-SEC001 & TEST-SEC004: User A cannot retrieve or delete User B's document."""
    user_a_token = "test_token_:user_a_sec:user_a@law.com:Attorney A"
    user_b_token = "test_token_:user_b_sec:user_b@law.com:Attorney B"

    # User A uploads a document
    pdf_data = make_test_pdf("Confidential Client A File")
    resp_upload = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {user_a_token}"},
        files={"file": ("client_a.pdf", pdf_data, "application/pdf")}
    )
    assert resp_upload.status_code == status.HTTP_201_CREATED
    doc_id = resp_upload.json()["document"]["id"]

    # User B tries to view User A's document -> 403 Forbidden
    resp_get = client.get(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {user_b_token}"}
    )
    assert resp_get.status_code == status.HTTP_403_FORBIDDEN

    # User B tries to delete User A's document -> 403 Forbidden
    resp_del = client.delete(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {user_b_token}"}
    )
    assert resp_del.status_code == status.HTTP_403_FORBIDDEN

    # User A successfully retrieves and deletes their own document
    resp_owner_get = client.get(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {user_a_token}"}
    )
    assert resp_owner_get.status_code == status.HTTP_200_OK

    resp_owner_del = client.delete(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {user_a_token}"}
    )
    assert resp_owner_del.status_code == status.HTTP_204_NO_CONTENT

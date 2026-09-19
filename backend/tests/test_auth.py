from fastapi import status
from app.models.user import User


def test_a001_valid_token_accepted(client):
    """TEST-A001: Valid Firebase token is accepted."""
    token = "test_token_:user_valid_001:valid@legalai.example.com:Valid User"
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "valid@legalai.example.com"
    assert data["firebase_uid"] == "user_valid_001"
    assert data["display_name"] == "Valid User"


def test_a002_missing_token_returns_401(client):
    """TEST-A002: Missing authentication token returns HTTP 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Missing Authorization header" in response.json()["detail"]


def test_a003_invalid_token_returns_401(client):
    """TEST-A003: Invalid token returns HTTP 401."""
    # Malformed format (not Bearer)
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Basic some_basic_token"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Invalid token body
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_garbage_token"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_a004_expired_token_rejected(client):
    """TEST-A004: Expired token is rejected with HTTP 401."""
    token = "expired_token_12345"
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expired" in response.json()["detail"].lower()


def test_a005_user_record_created_on_first_auth(client, db_session):
    """TEST-A005: User record is created after first valid authentication."""
    uid = "first_time_user_999"
    email = "first_time@legalai.example.com"
    token = f"test_token_:{uid}:{email}:First Timer"

    # Verify user does not exist yet
    assert db_session.query(User).filter_by(firebase_uid=uid).first() is None

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK

    # Verify user now persisted in DB
    user = db_session.query(User).filter_by(firebase_uid=uid).first()
    assert user is not None
    assert user.email == email


def test_a006_existing_user_record_reused(client, db_session):
    """TEST-A006: Existing user record is reused instead of duplicated."""
    uid = "reuse_user_888"
    email = "reuse@legalai.example.com"
    token = f"test_token_:{uid}:{email}:Reused User"

    # First login
    resp1 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp1.status_code == status.HTTP_200_OK
    user_id_1 = resp1.json()["id"]

    # Second login with same UID
    resp2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == status.HTTP_200_OK
    user_id_2 = resp2.json()["id"]

    assert user_id_1 == user_id_2
    count = db_session.query(User).filter_by(firebase_uid=uid).count()
    assert count == 1


def test_a007_backend_identity_derived_from_token(client):
    """TEST-A007: Backend identity is derived from the verified token, not client input."""
    token = "test_token_:isolated_tenant_777:tenant777@firm.com:Managing Partner"
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["firebase_uid"] == "isolated_tenant_777"
    assert data["email"] == "tenant777@firm.com"

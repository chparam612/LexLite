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


def test_a008_register_user_success(client, db_session):
    """TEST-A008: Registering a new user creates record and returns valid JWT token."""
    payload = {
        "email": "new_counsel@legalai.example.com",
        "password": "StrongPassword2026!",
        "display_name": "Counsel Alexandra",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "new_counsel@legalai.example.com"
    assert data["user"]["display_name"] == "Counsel Alexandra"

    # Verify returned token authenticates with /api/v1/auth/me
    token = data["access_token"]
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == status.HTTP_200_OK
    assert me_resp.json()["email"] == "new_counsel@legalai.example.com"


def test_a009_register_duplicate_email_fails(client):
    """TEST-A009: Registering an already registered email returns HTTP 400."""
    payload = {
        "email": "duplicate_check@legalai.example.com",
        "password": "AnotherPassword123!",
        "display_name": "Original User",
    }
    # First registration succeeds
    resp1 = client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == status.HTTP_201_CREATED

    # Second registration with same email must fail with 400
    resp2 = client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in resp2.json()["detail"].lower()


def test_a010_login_user_success(client):
    """TEST-A010: Logging in with valid credentials returns JWT access token."""
    # Register first within this test's isolated transaction
    reg_payload = {
        "email": "login_test@legalai.example.com",
        "password": "StrongPassword2026!",
        "display_name": "Login Tester",
    }
    reg_resp = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == status.HTTP_201_CREATED

    # Login with the registered credentials
    login_payload = {
        "email": "login_test@legalai.example.com",
        "password": "StrongPassword2026!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login_test@legalai.example.com"


def test_a011_login_invalid_password_fails(client):
    """TEST-A011: Logging in with incorrect password returns HTTP 401."""
    reg_payload = {
        "email": "wrong_pwd_test@legalai.example.com",
        "password": "CorrectPassword123!",
        "display_name": "Password Tester",
    }
    reg_resp = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == status.HTTP_201_CREATED

    login_payload = {
        "email": "wrong_pwd_test@legalai.example.com",
        "password": "WrongPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid" in response.json()["detail"].lower()


def test_a012_demo_login_success(client):
    """TEST-A012: Instant demo login returns valid session for demo attorney."""
    response = client.post("/api/v1/auth/demo-login")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "attorney@legalai.example.com"

    # Verify demo token authenticates correctly
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"}
    )
    assert me_resp.status_code == status.HTTP_200_OK
    assert me_resp.json()["email"] == "attorney@legalai.example.com"

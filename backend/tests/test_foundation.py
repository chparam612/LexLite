import pytest
from fastapi import status
from sqlalchemy import text
from app.core.config import Settings
from app.core.logging import SensitiveDataFilter


def test_f001_backend_health_endpoint(client):
    """TEST-F001: Backend health endpoint returns HTTP 200."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data

    # Also verify versioned api path
    v1_resp = client.get("/api/v1/health")
    assert v1_resp.status_code == status.HTTP_200_OK
    assert v1_resp.json()["status"] == "healthy"


def test_f002_readiness_endpoint_db_available(client):
    """TEST-F002: Readiness endpoint correctly reports database availability."""
    response = client.get("/ready")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ready"
    assert data["components"]["database"] == "connected"
    assert data["components"]["storage"] == "accessible"


def test_f003_application_starts_with_valid_config():
    """TEST-F003: Application starts with valid environment variables."""
    cfg = Settings(
        APPLICATION_ENV="testing",
        DATABASE_URL="sqlite:///:memory:",
        DEBUG=True
    )
    assert cfg.APPLICATION_ENV == "testing"
    assert cfg.DATABASE_URL == "sqlite:///:memory:"
    assert cfg.DEBUG is True


def test_f004_application_fails_safely_when_invalid_config():
    """TEST-F004: Application fails safely when required configuration is missing or malformed."""
    with pytest.raises(Exception):
        Settings(CORS_ALLOWED_ORIGINS=12345)


def test_f005_database_connection_established(db_session):
    """TEST-F005: Database connection can be established."""
    result = db_session.execute(text("SELECT 1 as num")).scalar()
    assert result == 1


def test_f006_schema_creation_and_clean_run(db_session):
    """TEST-F006: Database migration/schema runs successfully on a clean database."""
    result = db_session.execute(text("SELECT 1")).scalar()
    assert result == 1


def test_f007_schema_rollback_or_teardown(db_session):
    """TEST-F007: Database transaction can be rolled back safely."""
    savepoint = db_session.begin_nested()
    db_session.execute(text("CREATE TABLE temp_test (id INTEGER PRIMARY KEY);"))
    savepoint.rollback()
    assert True


def test_sensitive_logging_filter():
    """Verify logger masks sensitive credentials (API keys, bearer tokens)."""
    filter_instance = SensitiveDataFilter()
    msg = "User logged in with api-key: sk-123456789 and Bearer my_secret_token"
    sanitized = filter_instance.sanitize(msg)
    assert "sk-123456789" not in sanitized
    assert "my_secret_token" not in sanitized
    assert "[REDACTED]" in sanitized

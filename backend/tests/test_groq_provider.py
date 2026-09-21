import json
import pytest
from unittest.mock import patch, MagicMock
import httpx

from app.core.config import settings
from app.core.exceptions import LegalAIException
from app.services.retrieval_service import RetrievalHit
from app.services.ai_provider import (
    GroqProvider,
    get_ai_provider,
    GroundedResponse,
)


@pytest.fixture
def sample_hits():
    return [
        RetrievalHit(
            chunk_id="chunk-rent-01",
            document_id="doc-lease-01",
            document_title="Residential Lease Agreement",
            content="Section 3.1: Monthly rent is $2,500.00 USD due on the first day of each calendar month.",
            heading_path="Rent and Payments",
            page_start=2,
            page_end=2,
            score=0.95,
            rank=1,
            contextual_content="Section 3.1: Monthly rent is $2,500.00 USD due on the first day of each calendar month.",
            version_id="v1"
        ),
        RetrievalHit(
            chunk_id="chunk-term-01",
            document_id="doc-lease-01",
            document_title="Residential Lease Agreement",
            content="Section 11.2: Tenant may terminate with 60 days advance written notice and payment of 2 months rent.",
            heading_path="Early Termination",
            page_start=4,
            page_end=4,
            score=0.88,
            rank=2,
            contextual_content=(
                "Section 11.2: Tenant may terminate with 60 days advance written notice "
                "and payment of 2 months rent."
            ),
            version_id="v1"
        )
    ]


def test_groq_001_unconfigured_key_falls_back_to_local(sample_hits):
    """GROQ-001: When GROQ_API_KEY is unset, provider falls back to local synthesis."""
    provider = GroqProvider(api_key="")
    assert provider.client_initialized is False

    resp = provider.generate_answer("What is the rent?", sample_hits)
    assert isinstance(resp, GroundedResponse)
    assert "$2,500" in resp.answer
    assert len(resp.claims) > 0


def test_groq_002_health_check():
    """GROQ-002: Health check returns False when unconfigured, True when 200."""
    unconfigured = GroqProvider(api_key="")
    assert unconfigured.health_check() is False

    configured = GroqProvider(api_key="gsk_valid_dummy_key_123")
    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        assert configured.health_check() is True

    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=401)
        assert configured.health_check() is False


def test_groq_003_successful_generation(sample_hits):
    """GROQ-003: Successful generation parses JSON schema into GroundedResponse."""
    provider = GroqProvider(api_key="gsk_valid_dummy_key_123")
    assert provider.client_initialized is True

    mock_llm_json = {
        "answer": "The monthly rent is $2,500 due on the first of each month.",
        "claims": [
            {
                "claim_text": "Monthly rent is $2,500.00 USD",
                "quote": "Monthly rent is $2,500.00 USD",
                "chunk_id": "chunk-rent-01",
                "page_number": 2
            }
        ],
        "confidence": "high",
        "missing_information": None,
        "uncertainty": None,
        "professional_review_recommended": True
    }

    mock_resp = MagicMock(
        status_code=200,
        json=lambda: {"choices": [{"message": {"content": json.dumps(mock_llm_json)}}]}
    )

    with patch("httpx.Client.post", return_value=mock_resp):
        resp = provider.generate_answer("How much is rent?", sample_hits)
        assert isinstance(resp, GroundedResponse)
        assert "$2,500" in resp.answer
        assert resp.confidence == "high"
        assert len(resp.claims) == 1
        assert resp.claims[0].page_number == 2


def test_groq_004_rate_limit_429(sample_hits):
    """GROQ-004: HTTP 429 raises LegalAIException with QUOTA_EXHAUSTED."""
    provider = GroqProvider(api_key="gsk_valid_dummy_key_123")

    mock_resp = MagicMock(status_code=429, text="Rate limit reached: requests per minute exceeded")

    with patch("httpx.Client.post", return_value=mock_resp):
        with pytest.raises(LegalAIException) as exc_info:
            provider.generate_answer("What is rent?", sample_hits)
        assert exc_info.value.code == "QUOTA_EXHAUSTED"
        assert exc_info.value.status_code == 429


def test_groq_005_auth_failed_401(sample_hits):
    """GROQ-005: HTTP 401 raises LegalAIException with AI_AUTH_FAILED."""
    provider = GroqProvider(api_key="gsk_invalid_key")

    mock_resp = MagicMock(status_code=401, text="Invalid API key provided")

    with patch("httpx.Client.post", return_value=mock_resp):
        with pytest.raises(LegalAIException) as exc_info:
            provider.generate_answer("What is rent?", sample_hits)
        assert exc_info.value.code == "AI_AUTH_FAILED"
        assert exc_info.value.status_code == 401


def test_groq_006_model_not_found_404(sample_hits):
    """GROQ-006: HTTP 404 raises LegalAIException with MODEL_NOT_FOUND."""
    provider = GroqProvider(api_key="gsk_valid_key", model_name="nonexistent-model")

    mock_resp = MagicMock(status_code=404, text="Model not found")

    with patch("httpx.Client.post", return_value=mock_resp):
        with pytest.raises(LegalAIException) as exc_info:
            provider.generate_answer("What is rent?", sample_hits)
        assert exc_info.value.code == "MODEL_NOT_FOUND"
        assert exc_info.value.status_code == 404


def test_groq_007_timeout_raises_503(sample_hits):
    """GROQ-007: TimeoutException raises LegalAIException with 503."""
    provider = GroqProvider(api_key="gsk_valid_key")

    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Connection timed out")):
        with pytest.raises(LegalAIException) as exc_info:
            provider.generate_answer("What is rent?", sample_hits)
        assert exc_info.value.status_code == 503
        assert exc_info.value.code == "AI_GENERATION_FAILED"


def test_groq_008_out_of_scope_query_no_network_call(sample_hits):
    """GROQ-008: Non-legal questions return out_of_scope response without calling Groq API."""
    provider = GroqProvider(api_key="gsk_valid_key")

    with patch("httpx.Client.post") as mock_post:
        resp = provider.generate_answer("How do I bake chocolate chip cookies?", sample_hits)
        assert mock_post.called is False
        assert "recipe" in resp.answer.lower() or "outside the legal domain" in resp.answer.lower()
        assert resp.confidence == "insufficient_evidence"


def test_groq_009_empty_hits_no_network_call():
    """GROQ-009: Empty hits return insufficient evidence without calling Groq API."""
    provider = GroqProvider(api_key="gsk_valid_key")

    with patch("httpx.Client.post") as mock_post:
        resp = provider.generate_answer("What is the rent?", [])
        assert mock_post.called is False
        assert resp.confidence == "insufficient_evidence"


def test_groq_010_factory_returns_groq_provider(monkeypatch):
    """GROQ-010: get_ai_provider returns GroqProvider when AI_PROVIDER=groq."""
    monkeypatch.setattr(settings, "AI_PROVIDER", "groq")
    prov = get_ai_provider()
    assert isinstance(prov, GroqProvider)

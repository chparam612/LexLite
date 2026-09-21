from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Dict, Any
from app.core.config import settings

router = APIRouter(prefix="/system", tags=["System Diagnostics"])


class SystemDiagnosticsResponse(BaseModel):
    ai_provider: str
    ai_model: str
    embedding_provider: str
    local_embedding_model: str
    vector_store: str
    database_mode: str
    storage_mode: str
    allow_paid_ai_fallback: bool
    max_output_tokens: int
    max_context_tokens: int
    is_free_tier: bool
    rate_limit_policy: Dict[str, Any]


@router.get("/diagnostics", response_model=SystemDiagnosticsResponse, status_code=status.HTTP_200_OK)
def get_system_diagnostics():
    """
    Administrative and judging diagnostics endpoint (Section 27H & 27I).
    Displays active AI provider, embedding strategy, vector store, and quota limits.
    Never exposes API keys or internal secrets.
    """
    return SystemDiagnosticsResponse(
        ai_provider=settings.AI_PROVIDER,
        ai_model=settings.GEMINI_MODEL,
        embedding_provider=settings.EMBEDDING_PROVIDER,
        local_embedding_model=settings.LOCAL_EMBEDDING_MODEL,
        vector_store=settings.VECTOR_STORE,
        database_mode=settings.DATABASE_MODE,
        storage_mode=settings.STORAGE_MODE,
        allow_paid_ai_fallback=settings.ALLOW_PAID_AI_FALLBACK,
        max_output_tokens=settings.MAX_OUTPUT_TOKENS,
        max_context_tokens=settings.MAX_CONTEXT_TOKENS,
        is_free_tier=True,
        rate_limit_policy={
            "tier": "Gemini Free Tier",
            "requests_per_minute": 15,
            "requests_per_day": 1500,
            "quota_exhaustion_behavior": "Graceful block with quota reset instructions (no paid fallback)",
        }
    )

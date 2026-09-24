from typing import List, Optional
from app.core.config import settings
from app.services.retrieval_service import RetrievalHit
from app.core.exceptions import LegalAIException
from app.services.ai_provider import (
    GroundedClaim,
    GroundedResponse,
    AIProvider,
    get_ai_provider,
    GeminiProvider,
    LocalLLMProvider,
)

__all__ = ["GenerationService", "GroundedResponse", "GroundedClaim"]


class GenerationService:
    """
    Unified Generation Service wrapping the Section 27 AIProvider interface.
    Defaults to free-first local or Gemini free tier.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        provider: Optional[AIProvider] = None
    ):
        if provider:
            self.provider = provider
            self.model_name = model_name or getattr(provider, "model_name", "custom")
            self.api_key = api_key or getattr(provider, "api_key", None)
        elif (settings.AI_PROVIDER or "").lower() == "groq":
            self.api_key = api_key or settings.GROQ_API_KEY
            self.model_name = model_name or settings.GROQ_MODEL
            from app.services.ai_provider import GroqProvider
            self.provider = GroqProvider(api_key=self.api_key, model_name=self.model_name)
        elif api_key and api_key not in ("demo-key-for-dev", "your-gemini-api-key-here", ""):
            self.api_key = api_key
            self.model_name = model_name or settings.GEMINI_MODEL
            self.provider = GeminiProvider(api_key=self.api_key, model_name=self.model_name)
        elif settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in ("demo-key-for-dev", "your-gemini-api-key-here", ""):
            self.api_key = settings.GEMINI_API_KEY
            self.model_name = model_name or settings.GEMINI_MODEL
            self.provider = GeminiProvider(api_key=self.api_key, model_name=self.model_name)
        else:
            self.provider = get_ai_provider()
            self.model_name = model_name or getattr(self.provider, "model_name", "default")
            self.api_key = api_key or getattr(self.provider, "api_key", None)

    def generate_grounded_answer(
        self,
        query: str,
        hits: List[RetrievalHit],
        conversation_history: Optional[List[dict]] = None
    ) -> GroundedResponse:
        """Delegate generation to active AIProvider with free-tier rate limit fallback."""
        try:
            return self.provider.generate_answer(
                query=query,
                hits=hits,
                conversation_history=conversation_history
            )
        except LegalAIException as e:
            if hits and e.code in ("QUOTA_EXHAUSTED", "AI_GENERATION_FAILED", "MODEL_NOT_FOUND", "AI_AUTH_FAILED"):
                local_provider = LocalLLMProvider()
                return local_provider.generate_answer(query, hits, conversation_history)
            raise

    def _build_context_xml(self, hits: List[RetrievalHit]) -> str:
        """Enclose retrieved chunks in secure XML tags with metadata attributes."""
        if hasattr(self.provider, "_build_context_xml"):
            return self.provider._build_context_xml(hits)
        gp = GeminiProvider(api_key=self.api_key, model_name=self.model_name)
        return gp._build_context_xml(hits)

    def classify_query(self, query: str) -> str:
        return self.provider.classify_query(query)

    def summarize_text(self, text: str, max_words: int = 150) -> str:
        return self.provider.summarize_text(text, max_words=max_words)

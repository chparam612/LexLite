from typing import List, Optional
from app.core.config import settings
from app.services.retrieval_service import RetrievalHit
from app.services.ai_provider import (
    GroundedClaim,
    GroundedResponse,
    AIProvider,
    get_ai_provider,
    GeminiProvider,
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
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        if provider:
            self.provider = provider
        elif self.api_key and self.api_key not in ("demo-key-for-dev", "your-gemini-api-key-here", ""):
            self.provider = GeminiProvider(api_key=self.api_key, model_name=self.model_name)
        else:
            self.provider = get_ai_provider()

    def generate_grounded_answer(
        self,
        query: str,
        hits: List[RetrievalHit],
        conversation_history: Optional[List[dict]] = None
    ) -> GroundedResponse:
        """Delegate generation to active AIProvider."""
        return self.provider.generate_answer(
            query=query,
            hits=hits,
            conversation_history=conversation_history
        )

    def _build_context_xml(self, hits: List[RetrievalHit]) -> str:
        """Enclose retrieved chunks in secure XML tags with metadata attributes."""
        if isinstance(self.provider, GeminiProvider):
            return self.provider._build_context_xml(hits)
        gp = GeminiProvider(api_key=self.api_key, model_name=self.model_name)
        return gp._build_context_xml(hits)

    def classify_query(self, query: str) -> str:
        return self.provider.classify_query(query)

    def summarize_text(self, text: str, max_words: int = 150) -> str:
        return self.provider.summarize_text(text, max_words=max_words)

import abc
import hashlib
import math
from typing import List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import LegalAIException


class EmbeddingProvider(abc.ABC):
    @abc.abstractmethod
    def embed_text(self, text: str, task_type: str = "retrieval_document") -> List[float]:
        """Generate embedding vector for a single string."""
        pass

    @abc.abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a list of strings."""
        pass

    @abc.abstractmethod
    def get_dimensions(self) -> int:
        """Return dimensionality of the embedding vectors."""
        pass

    @abc.abstractmethod
    def get_model_name(self) -> str:
        """Return the model name."""
        pass


class LocalEmbeddingProvider(EmbeddingProvider):
    """
    Default free embedding provider (Section 27C).
    Runs 100% on local CPU with zero external API calls or billing requirements.
    Supports sentence-transformers when installed, with deterministic normalized fallback.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.LOCAL_EMBEDDING_MODEL
        self.dimensions = 384  # standard for all-MiniLM-L6-v2
        self._st_model = None

        try:
            from sentence_transformers import SentenceTransformer
            self._st_model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded local SentenceTransformer model: {self.model_name}")
        except Exception as e:
            logger.info(
                f"SentenceTransformer not pre-installed ({e}). "
                f"Using local deterministic CPU vector inference (dim: {self.dimensions})."
            )

    def _generate_local_cpu_vector(self, text: str) -> List[float]:
        """Deterministic unit-normalized CPU embedding based on token character hashing."""
        clean = text.strip()
        h = hashlib.sha256(clean.encode("utf-8")).digest()
        raw_vec: List[float] = []
        for i in range(self.dimensions):
            byte_val = h[i % len(h)]
            # Add positional perturbation based on character position
            char_offset = ord(clean[i % len(clean)]) if clean else 0
            val = ((byte_val ^ (char_offset & 0xFF)) / 255.0) - 0.5
            raw_vec.append(val)

        # L2 normalize
        magnitude = math.sqrt(sum(x * x for x in raw_vec))
        if magnitude > 0:
            return [x / magnitude for x in raw_vec]
        return raw_vec

    def embed_text(self, text: str, task_type: str = "retrieval_document") -> List[float]:
        if not text or not text.strip():
            raise LegalAIException(
                message="Cannot generate embedding for empty text.",
                code="EMPTY_EMBEDDING_INPUT",
                status_code=400
            )

        if self._st_model:
            vec = self._st_model.encode(text.strip(), convert_to_numpy=True)
            return vec.tolist()

        return self._generate_local_cpu_vector(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self._st_model:
            vecs = self._st_model.encode(texts, convert_to_numpy=True)
            return [v.tolist() for v in vecs]
        return [self.embed_text(t) for t in texts]

    def get_dimensions(self) -> int:
        return self.dimensions

    def get_model_name(self) -> str:
        return self.model_name


class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Optional Gemini embedding provider for users with configured Google AI Studio keys.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_EMBEDDING_MODEL
        self.dimensions = 768
        self.client_initialized = False

        if self.api_key and self.api_key not in ("demo-key-for-dev", "your-gemini-api-key-here", ""):
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client_initialized = True
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini embedding provider: {e}")

    def embed_text(self, text: str, task_type: str = "retrieval_document") -> List[float]:
        if not text or not text.strip():
            raise LegalAIException(
                message="Cannot generate embedding for empty text.",
                code="EMPTY_EMBEDDING_INPUT",
                status_code=400
            )

        if not self.client_initialized:
            # Fall back to local CPU embedding
            local_fallback = LocalEmbeddingProvider()
            return local_fallback.embed_text(text)

        import google.generativeai as genai
        try:
            response = genai.embed_content(
                model=self.model_name,
                content=text.strip(),
                task_type=task_type
            )
            return response.get("embedding", [])
        except Exception as e:
            err_str = str(e)
            safe_err = err_str.replace(self.api_key, "[REDACTED]") if self.api_key else err_str
            if "429" in safe_err or "quota" in safe_err.lower() or "resource" in safe_err.lower():
                raise LegalAIException(
                    message=(
                        "AI usage limit reached. Please wait for the quota to reset "
                        "or configure another permitted model."
                    ),
                    code="QUOTA_EXHAUSTED",
                    status_code=429
                )
            raise LegalAIException(
                message=f"Gemini embedding failed: {safe_err}",
                code="EMBEDDING_API_ERROR",
                status_code=503
            )

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]

    def get_dimensions(self) -> int:
        return self.dimensions

    def get_model_name(self) -> str:
        return self.model_name


class MockEmbeddingProvider(EmbeddingProvider):
    """Testing-only mock embedding provider."""

    def __init__(self, dimensions: int = 768):
        self.dimensions = dimensions

    def embed_text(self, text: str, task_type: str = "retrieval_document") -> List[float]:
        # Return uniform normalized mock vector
        val = 1.0 / math.sqrt(self.dimensions)
        return [val] * self.dimensions

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]

    def get_dimensions(self) -> int:
        return self.dimensions

    def get_model_name(self) -> str:
        return "mock-embedding-model"


def get_embedding_provider() -> EmbeddingProvider:
    """Factory returning configured embedding provider (defaults to free local)."""
    provider_name = (settings.EMBEDDING_PROVIDER or "local").lower()
    if provider_name == "gemini":
        return GeminiEmbeddingProvider()
    elif provider_name == "mock":
        return MockEmbeddingProvider()
    return LocalEmbeddingProvider()

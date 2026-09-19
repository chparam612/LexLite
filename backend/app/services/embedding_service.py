import hashlib
import math
import time
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import LegalAIException
from app.models.chunk import DocumentChunk
from app.models.embedding import Embedding, EmbeddingModel

DEFAULT_DIMENSIONS = 768


class EmbeddingService:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_EMBEDDING_MODEL
        self.dimensions = DEFAULT_DIMENSIONS

        self.client_initialized = False
        if self.api_key and self.api_key not in ("demo-key-for-dev", "your-gemini-api-key-here", ""):
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client_initialized = True
                logger.info(f"Gemini Embedding client initialized with model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini embedding client: {e}")

    def _generate_synthetic_embedding(self, text: str) -> List[float]:
        """
        Deterministic, unit-normalized 768-dimensional fallback vector based on
        text hash. Used for testing and offline development when live Gemini API
        keys are not provided.
        """
        h = hashlib.sha256(text.encode("utf-8")).digest()
        raw_vec: List[float] = []
        for i in range(self.dimensions):
            byte_val = h[i % len(h)]
            float_val = (float(byte_val) / 255.0) - 0.5
            raw_vec.append(float_val)

        # L2 normalize
        magnitude = math.sqrt(sum(x * x for x in raw_vec))
        if magnitude > 0:
            return [x / magnitude for x in raw_vec]
        return raw_vec

    def embed_text(self, text: str, retries: int = 3) -> List[float]:
        """
        Generate embedding vector for a single text string.
        Rejects empty text and handles rate limits with exponential backoff.
        """
        if not text or not text.strip():
            raise LegalAIException(
                message="Cannot generate embedding for empty or whitespace-only text.",
                code="EMPTY_EMBEDDING_INPUT",
                status_code=400
            )

        clean_text = text.strip()

        if not self.client_initialized:
            # Deterministic fallback adapter
            return self._generate_synthetic_embedding(clean_text)

        import google.generativeai as genai

        for attempt in range(retries):
            try:
                response = genai.embed_content(
                    model=self.model_name,
                    content=clean_text,
                    task_type="retrieval_document"
                )
                embedding = response.get("embedding", [])
                if len(embedding) != self.dimensions:
                    logger.warning(
                        f"Embedding dimension mismatch: expected {self.dimensions}, got {len(embedding)}"
                    )
                return embedding

            except Exception as e:
                err_str = str(e)
                # Never log or expose API keys
                safe_err = err_str.replace(self.api_key, "[REDACTED]") if self.api_key else err_str

                if "429" in safe_err or "quota" in safe_err.lower() or "resource" in safe_err.lower():
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"Embedding rate limit. Retrying in {wait_time}s (Attempt {attempt+1}/{retries})"
                    )
                    time.sleep(wait_time)
                elif attempt == retries - 1:
                    logger.error(f"Gemini embedding API failed after {retries} attempts: {safe_err}")
                    raise LegalAIException(
                        message="Embedding service temporarily unavailable. Please try again later.",
                        code="EMBEDDING_API_ERROR",
                        status_code=503
                    )
                else:
                    time.sleep(1)

        return self._generate_synthetic_embedding(clean_text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a collection of texts."""
        embeddings: List[List[float]] = []
        for text in texts:
            embeddings.append(self.embed_text(text))
        return embeddings

    def get_or_create_model_record(self, db: Session) -> EmbeddingModel:
        """Fetch or persist the active embedding model metadata."""
        model_rec = db.query(EmbeddingModel).filter_by(
            model_name=self.model_name
        ).first()

        if not model_rec:
            model_rec = EmbeddingModel(
                provider="google",
                model_name=self.model_name,
                dimensions=self.dimensions,
                version="004",
                is_active=True
            )
            db.add(model_rec)
            db.commit()
            db.refresh(model_rec)
            logger.info(f"Registered new EmbeddingModel: {self.model_name} (dim: {self.dimensions})")

        return model_rec

    def generate_and_store_embeddings(self, db: Session, chunks: List[DocumentChunk]) -> int:
        """
        Generate embeddings for chunks using contextual content and persist them.
        Prevents duplicate embeddings for the same chunk and model.
        """
        if not chunks:
            return 0

        model_rec = self.get_or_create_model_record(db)
        stored_count = 0

        for chunk in chunks:
            # Check if embedding already exists for this chunk and model (idempotency)
            existing = db.query(Embedding).filter_by(
                chunk_id=chunk.id,
                model_id=model_rec.id
            ).first()

            if existing:
                continue

            # Use enriched contextual content for dense vector generation
            embedding_text = chunk.contextual_content or chunk.content
            vector = self.embed_text(embedding_text)

            emb = Embedding(
                chunk_id=chunk.id,
                model_id=model_rec.id,
                embedding=vector
            )
            db.add(emb)
            stored_count += 1

        db.commit()
        logger.info(f"Generated and persisted {stored_count} embeddings for model {model_rec.model_name}.")
        return stored_count

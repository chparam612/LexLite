from typing import List, Union, Any, Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    APPLICATION_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    # Database
    DATABASE_URL: str = "sqlite:///./legal_ai_dev.db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "legal_ai_db"
    POSTGRES_PORT: int = 5432

    # Storage
    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_DIR: str = "./storage/uploads"
    GOOGLE_CLOUD_PROJECT: str = "legal-ai-project"
    GOOGLE_CLOUD_STORAGE_BUCKET: str = "legal-ai-documents"
    GCS_BUCKET_NAME: Optional[str] = None

    # AI & Gemini
    GEMINI_API_KEY: str = "demo-key-for-dev"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"
    GEMINI_GENERATION_MODEL: str = "models/gemini-1.5-flash"
    RERANKER_MODEL: str = "models/text-embedding-004"

    # RAG Config
    MAX_UPLOAD_SIZE_MB: int = 25
    DENSE_TOP_K: int = 30
    KEYWORD_TOP_K: int = 30
    FUSION_TOP_K: int = 40
    RERANK_TOP_K: int = 10
    FINAL_CONTEXT_CHUNKS: int = 8
    MAX_CONTEXT_TOKENS: int = 12000
    PARENT_CONTEXT_ENABLED: bool = True
    CITATION_VERIFICATION_ENABLED: bool = True

    # Security & CORS
    CORS_ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000"
    ]
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if not v.startswith("["):
                return [i.strip() for i in v.split(",") if i.strip()]
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                raise ValueError("CORS_ALLOWED_ORIGINS JSON must be a list of strings")
            except Exception as e:
                raise ValueError(f"Invalid JSON for CORS_ALLOWED_ORIGINS: {e}")
        elif isinstance(v, list):
            return [str(i) for i in v]
        raise ValueError(f"CORS_ALLOWED_ORIGINS must be a list or string, got {type(v)}")

    @field_validator("MAX_UPLOAD_SIZE_MB")
    def validate_max_upload(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("MAX_UPLOAD_SIZE_MB must be greater than 0")
        return v

    @model_validator(mode="after")
    def sync_storage_bucket(self) -> "Settings":
        if self.GCS_BUCKET_NAME and not self.GOOGLE_CLOUD_STORAGE_BUCKET:
            self.GOOGLE_CLOUD_STORAGE_BUCKET = self.GCS_BUCKET_NAME
        elif self.GCS_BUCKET_NAME and self.GOOGLE_CLOUD_STORAGE_BUCKET == "legal-ai-documents":
            self.GOOGLE_CLOUD_STORAGE_BUCKET = self.GCS_BUCKET_NAME
        return self


settings = Settings()

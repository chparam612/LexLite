from typing import List, Union, Any, Optional
from pydantic import field_validator, model_validator, Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


def normalize_database_url(url: Any) -> str:
    """
    Normalize database connection URLs to ensure an explicit DBAPI driver (psycopg2) is used.
    Handles legacy 'postgres://' and bare 'postgresql://' connection strings (common on Render)
    by converting them to 'postgresql+psycopg2://' when '+psycopg2' or '+psycopg' is not present.
    """
    if not url:
        return "sqlite:///./legal_ai_dev.db"
    url_str = str(url).strip()
    if url_str.startswith("postgres://"):
        return url_str.replace("postgres://", "postgresql+psycopg2://", 1)
    if url_str.startswith("postgresql://") and not (
        "+psycopg2" in url_str or "+psycopg" in url_str
    ):
        return url_str.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url_str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    APPLICATION_ENV: str = "development"
    ENVIRONMENT: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
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
    STORAGE_MODE: str = "local"
    LOCAL_STORAGE_DIR: str = "./storage/uploads"
    GOOGLE_CLOUD_PROJECT: str = "legal-ai-project"
    GOOGLE_CLOUD_STORAGE_BUCKET: str = "legal-ai-documents"
    GCS_BUCKET_NAME: Optional[str] = None

    # AI Providers (Section 27 Free-First: Gemini, Groq, Local LLM)
    AI_PROVIDER: str = "gemini"  # "gemini", "groq", "local_llm", "mock"
    GEMINI_API_KEY: str = "demo-key-for-dev"
    GEMINI_MODEL: str = "gemini-flash-latest"
    GEMINI_GENERATION_MODEL: str = "models/gemini-flash-latest"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    EMBEDDING_PROVIDER: str = "local"  # "local", "gemini", "mock"
    LOCAL_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_STORE: str = "faiss"  # "faiss", "pgvector"
    DATABASE_MODE: str = "sqlite"  # "sqlite", "postgres"
    ALLOW_PAID_AI_FALLBACK: bool = False  # NEVER enable paid fallback automatically
    MAX_OUTPUT_TOKENS: int = 2048
    MAX_CONTEXT_TOKENS: int = 8000
    RERANKER_MODEL: str = "models/text-embedding-004"

    # RAG Config
    MAX_UPLOAD_SIZE_MB: int = 25
    DENSE_TOP_K: int = 30
    KEYWORD_TOP_K: int = 30
    FUSION_TOP_K: int = 40
    RERANK_TOP_K: int = 10
    FINAL_CONTEXT_CHUNKS: int = 8
    PARENT_CONTEXT_ENABLED: bool = True
    CITATION_VERIFICATION_ENABLED: bool = True

    # Security & CORS
    SECRET_KEY: str = "lexlite-production-secret-jwt-key-change-in-env-2026"
    JWT_SECRET_KEY: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("JWT_SECRET_KEY", "JWT_SECRET")
    )
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ALLOWED_ORIGINS: Union[List[str], str] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000"
        ],
        validation_alias=AliasChoices("CORS_ALLOWED_ORIGINS", "BACKEND_CORS_ORIGINS")
    )
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    @field_validator("DATABASE_URL", mode="before")
    def assemble_database_url(cls, v: Any) -> str:
        return normalize_database_url(v)

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
        if self.ENVIRONMENT and self.APPLICATION_ENV == "development":
            self.APPLICATION_ENV = self.ENVIRONMENT
        if self.GCS_BUCKET_NAME and not self.GOOGLE_CLOUD_STORAGE_BUCKET:
            self.GOOGLE_CLOUD_STORAGE_BUCKET = self.GCS_BUCKET_NAME
        elif self.GCS_BUCKET_NAME and self.GOOGLE_CLOUD_STORAGE_BUCKET == "legal-ai-documents":
            self.GOOGLE_CLOUD_STORAGE_BUCKET = self.GCS_BUCKET_NAME
        return self


settings = Settings()

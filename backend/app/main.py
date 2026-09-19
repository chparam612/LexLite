from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import (
    LegalAIException,
    legal_ai_exception_handler,
    generic_exception_handler
)
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.documents import router as documents_router


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        start_time = time.time()

        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"

        logger.info(
            f"{request.method} {request.url.path} responded {response.status_code} "
            f"in {process_time:.2f}ms [Correlation: {correlation_id}]"
        )
        return response


app_description = (
    "Enterprise AI-powered Legal Assistance and Access Platform utilizing Retrieval-Augmented Generation (RAG).\n\n"
    "**Legal Disclaimer:**\n"
    "This platform provides general legal information and document analysis for educational purposes. "
    "It does not provide legal advice, establish an attorney-client relationship, "
    "or replace consultation with a qualified legal professional."
)

app = FastAPI(
    title="LEGAL AI — ASSISTANCE & ACCESS",
    description=app_description,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
origins = settings.CORS_ALLOWED_ORIGINS
if isinstance(origins, str):
    origins = [origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID and Request Logging Middleware
app.add_middleware(CorrelationIdMiddleware)

# Register Exception Handlers
app.add_exception_handler(LegalAIException, legal_ai_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include Routers
# Root health & ready endpoints (for GCP Cloud Run / Kubernetes probes)
app.include_router(health_router, prefix="", tags=["System Probes"])

# Versioned API v1 routers
app.include_router(health_router, prefix="/api/v1", tags=["System Probes v1"])
app.include_router(auth_router, prefix="/api/v1", tags=["Authentication v1"])
app.include_router(documents_router, prefix="/api/v1", tags=["Documents v1"])

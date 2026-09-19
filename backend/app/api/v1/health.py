from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import os

from app.api.deps import get_db, check_db_health
from app.core.config import settings

router = APIRouter(tags=["Health & Readiness"])


@router.get("/health", status_code=status.HTTP_200_OK)
def get_health():
    """Liveness probe: returns 200 if application process is running."""
    return {
        "status": "healthy",
        "app_name": "LEGAL AI — ASSISTANCE & ACCESS",
        "version": "0.1.0",
        "environment": settings.APPLICATION_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
def get_readiness(response: Response, db: Session = Depends(get_db)):
    """Readiness probe: validates database and storage dependencies."""
    db_ok = check_db_health(db)

    # Check local storage directory readiness if local storage backend is configured
    storage_ok = True
    if settings.STORAGE_BACKEND == "local":
        try:
            os.makedirs(settings.LOCAL_STORAGE_DIR, exist_ok=True)
        except Exception:
            storage_ok = False

    is_ready = db_ok and storage_ok
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if is_ready else "unready",
        "components": {
            "database": "connected" if db_ok else "disconnected",
            "storage": "accessible" if storage_ok else "inaccessible"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.logging import logger
from app.schemas.user import TokenData

_firebase_app_initialized = False


def get_jwt_secret() -> str:
    """Retrieve active JWT secret with fallback."""
    return (
        getattr(settings, "JWT_SECRET_KEY", None)
        or getattr(settings, "SECRET_KEY", None)
        or "lexlite-production-secret-jwt-key-change-in-env-2026"
    )


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with random salt."""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000
    ).hex()
    return f"{salt}${pwd_hash}"


def verify_password(password: str, hashed: Optional[str]) -> bool:
    """Verify password against stored salt$hash with constant-time comparison."""
    if not hashed or "$" not in hashed:
        return False
    try:
        salt, pwd_hash = hashed.split("$", 1)
        test_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000
        ).hex()
        return secrets.compare_digest(pwd_hash, test_hash)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate signed HMAC-SHA256 JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=getattr(settings, "ACCESS_TOKEN_EXPIRE_DAYS", 7))
    )
    to_encode.update({"exp": expire})
    secret = get_jwt_secret()
    return jwt.encode(to_encode, secret, algorithm="HS256")


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate HMAC-SHA256 JWT access token."""
    try:
        secret = get_jwt_secret()
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Authentication token has expired.")
    except Exception:
        return None


def initialize_firebase():
    global _firebase_app_initialized
    if _firebase_app_initialized:
        return

    cred_path = getattr(settings, "GOOGLE_APPLICATION_CREDENTIALS", None)
    if cred_path and os.path.exists(cred_path):
        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            _firebase_app_initialized = True
            logger.info("Firebase Admin SDK initialized successfully with service account.")
        except Exception as e:
            logger.warning(f"Failed to initialize Firebase Admin with credentials: {e}")
    else:
        logger.info("No Firebase service account credentials found. Operating with fallback adapter.")


def verify_firebase_token(token: str) -> TokenData:
    """
    Verify bearer token. Supports:
    1. Native signed HMAC-SHA256 JWT tokens.
    2. Ephemeral demo tokens (test_token_:...).
    3. Firebase ID tokens via Admin SDK.
    """
    if not token or not token.strip():
        raise UnauthorizedError("Missing authentication token.")

    token = token.strip()

    # 1. First check if it is a native signed JWT token
    try:
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            uid = payload.get("sub")
            email = payload.get("email", f"{uid}@lexlite.ai")
            name = payload.get("name", payload.get("display_name"))
            return TokenData(uid=uid, email=email, display_name=name)
    except UnauthorizedError:
        raise
    except Exception:
        pass

    # Handle mock / test tokens for development and automated test suites
    if token.startswith("test_token_") or token.startswith("mock_token_"):
        if settings.APPLICATION_ENV.lower() == "production":
            logger.warning("Attempted use of test/mock token in production environment blocked.")
            raise UnauthorizedError("Test tokens are not permitted in production.")
        if "expired" in token:
            raise UnauthorizedError("Authentication token has expired.")
        parts = token.split(":")
        if len(parts) >= 3:
            uid = parts[1]
            email = parts[2]
            name = parts[3] if len(parts) > 3 else "Test User"
            return TokenData(uid=uid, email=email, display_name=name)
        elif len(parts) == 2:
            uid = parts[1]
            return TokenData(uid=uid, email=f"{uid}@legalai.example.com", display_name="Test User")
        else:
            raise UnauthorizedError("Invalid test token format.")

    if token.startswith("expired_"):
        raise UnauthorizedError("Authentication token has expired.")

    # Live Firebase Admin verification
    try:
        initialize_firebase()
        decoded = firebase_auth.verify_id_token(token)
        uid = decoded.get("uid")
        email = decoded.get("email", f"{uid}@firebase.user")
        name = decoded.get("name")
        return TokenData(uid=uid, email=email, display_name=name)
    except Exception as e:
        logger.warning(f"Firebase token verification failed: {e}")
        raise UnauthorizedError(f"Invalid authentication token: {str(e)}")

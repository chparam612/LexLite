import os
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.logging import logger
from app.schemas.user import TokenData

_firebase_app_initialized = False


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
    Verify Firebase ID Token. In production, uses Firebase Admin SDK.
    In testing / offline development, securely decodes mock/test tokens.
    """
    if not token or not token.strip():
        raise UnauthorizedError("Missing authentication token.")

    token = token.strip()

    # Handle mock / test tokens for development and automated test suites
    if token.startswith("test_token_") or token.startswith("mock_token_"):
        if settings.APPLICATION_ENV.lower() == "production" and _firebase_app_initialized:
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

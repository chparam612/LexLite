import os
from abc import ABC, abstractmethod
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import LegalAIException


class StorageService(ABC):
    @abstractmethod
    def upload_file(self, data: bytes, key: str) -> str:
        pass

    @abstractmethod
    def get_file(self, key: str) -> bytes:
        pass

    @abstractmethod
    def delete_file(self, key: str) -> bool:
        pass


class LocalFileStorageService(StorageService):
    def __init__(self, base_dir: str = None):
        self.base_dir = os.path.abspath(base_dir or settings.LOCAL_STORAGE_DIR)
        os.makedirs(self.base_dir, exist_ok=True)

    def _resolve_safe_path(self, key: str) -> str:
        clean_key = key.replace("\\", "/").lstrip("/")
        full_path = os.path.abspath(os.path.join(self.base_dir, clean_key))
        # Ensure path does not escape base_dir
        if not full_path.startswith(self.base_dir):
            raise LegalAIException(
                message="Security violation: Path traversal attempt blocked.",
                code="PATH_TRAVERSAL_DETECTED",
                status_code=400
            )
        return full_path

    def upload_file(self, data: bytes, key: str) -> str:
        safe_path = self._resolve_safe_path(key)
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, "wb") as f:
            f.write(data)
        logger.info(f"Stored file safely: {key} ({len(data)} bytes)")
        return key

    def get_file(self, key: str) -> bytes:
        safe_path = self._resolve_safe_path(key)
        if not os.path.exists(safe_path):
            raise LegalAIException(
                message=f"Storage object '{key}' not found.",
                code="OBJECT_NOT_FOUND",
                status_code=404
            )
        with open(safe_path, "rb") as f:
            return f.read()

    def delete_file(self, key: str) -> bool:
        safe_path = self._resolve_safe_path(key)
        if os.path.exists(safe_path):
            try:
                os.remove(safe_path)
                logger.info(f"Deleted storage object: {key}")
                return True
            except Exception as e:
                logger.warning(f"Failed to delete storage file {key}: {e}")
                return False
        return False


class GCSStorageService(StorageService):
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.client = None
        try:
            from google.cloud import storage
            self.client = storage.Client()
            self.bucket = self.client.bucket(bucket_name)
            logger.info(f"GCS Storage connected to bucket: {bucket_name}")
        except Exception as e:
            logger.warning(f"GCS client initialization failed ({e}). Falling back to local storage.")
            self.fallback = LocalFileStorageService()

    def upload_file(self, data: bytes, key: str) -> str:
        if self.client:
            blob = self.bucket.blob(key)
            blob.upload_from_string(data, content_type="application/pdf")
            return key
        return self.fallback.upload_file(data, key)

    def get_file(self, key: str) -> bytes:
        if self.client:
            blob = self.bucket.blob(key)
            return blob.download_as_bytes()
        return self.fallback.get_file(key)

    def delete_file(self, key: str) -> bool:
        if self.client:
            blob = self.bucket.blob(key)
            if blob.exists():
                blob.delete()
                return True
            return False
        return self.fallback.delete_file(key)


# Section 27D Aliases
StorageProvider = StorageService
LocalStorageProvider = LocalFileStorageService
GoogleCloudStorageProvider = GCSStorageService


def get_storage_service() -> StorageService:
    if settings.STORAGE_BACKEND.lower() == "gcs" and settings.GOOGLE_CLOUD_STORAGE_BUCKET:
        return GCSStorageService(settings.GOOGLE_CLOUD_STORAGE_BUCKET)
    return LocalFileStorageService(settings.LOCAL_STORAGE_DIR)


def get_storage_provider() -> StorageProvider:
    return get_storage_service()

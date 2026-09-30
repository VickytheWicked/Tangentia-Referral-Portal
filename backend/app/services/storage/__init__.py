from app.config import settings
from app.services.storage.base import StorageServiceInterface, StorageUploadResult
from app.services.storage.local_service import LocalStorageService


def get_storage_service() -> StorageServiceInterface:
    """
    Factory to resolve the appropriate CV document storage service implementation.
    Uses Azure Blob Storage in production ('blob' mode) or isolated local disk in development ('mock' mode).
    """
    storage_type = getattr(settings, "STORAGE_TYPE", "mock").lower()
    if storage_type == "blob" and settings.AZURE_STORAGE_CONNECTION_STRING:
        from app.services.storage.blob_service import BlobStorageService
        return BlobStorageService()
    return LocalStorageService()


get_cv_storage_service = get_storage_service

__all__ = [
    "StorageServiceInterface",
    "StorageUploadResult",
    "LocalStorageService",
    "get_storage_service",
    "get_cv_storage_service",
]

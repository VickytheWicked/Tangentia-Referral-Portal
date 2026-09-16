from app.config import settings
from app.services.sharepoint.base import SharePointServiceInterface, SharePointUploadResult
from app.services.sharepoint.graph_service import GraphSharePointService
from app.services.sharepoint.mock_service import MockSharePointService


def get_sharepoint_service() -> SharePointServiceInterface:
    """
    Factory to resolve the appropriate SharePoint service implementation.
    Uses real Microsoft Graph in production ('graph' mode), Azure Blob Storage ('blob' mode),
    or isolated mock in development ('mock' mode).
    """
    if settings.SHAREPOINT_STORAGE_TYPE == "graph" and settings.AZURE_CLIENT_ID and settings.SHAREPOINT_DRIVE_ID:
        return GraphSharePointService()
    if settings.SHAREPOINT_STORAGE_TYPE == "blob" and settings.AZURE_STORAGE_CONNECTION_STRING:
        from app.services.sharepoint.blob_service import BlobSharePointService
        return BlobSharePointService()
    return MockSharePointService()


__all__ = [
    "SharePointServiceInterface",
    "SharePointUploadResult",
    "GraphSharePointService",
    "MockSharePointService",
    "get_sharepoint_service",
]


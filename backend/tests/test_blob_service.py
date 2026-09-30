import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from app.services.storage.blob_service import BlobStorageService


@pytest.fixture
def mock_blob_env(monkeypatch):
    monkeypatch.setattr(
        "app.config.settings.AZURE_STORAGE_CONNECTION_STRING",
        "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=fake;EndpointSuffix=core.windows.net",
    )


@pytest.mark.asyncio
async def test_blob_download_cv_with_none_item_id_and_fallback(mock_blob_env):
    with patch("app.services.storage.blob_service.BlobServiceClient") as mock_bsc:
        service_client_instance = MagicMock()
        mock_bsc.from_connection_string.return_value = service_client_instance
        container_client = MagicMock()
        service_client_instance.get_container_client.return_value = container_client

        # Mock list_blobs
        mock_blob_item = MagicMock()
        mock_blob_item.name = "2026/REF-2026-000004_Salman-Khan_VP.pdf"
        container_client.list_blobs.return_value = [mock_blob_item]

        # Mock blob client
        blob_client = MagicMock()
        blob_client.download_blob.return_value.readall.return_value = b"%PDF-1.4 Mock Blob Content"
        container_client.get_blob_client.return_value = blob_client

        service = BlobStorageService()

        # item_id is None, referral_number is REF-2026-000004
        content, filename, content_type = await service.download_cv(
            drive_id=None,
            item_id=None,
            referral_number="REF-2026-000004",
            stored_filename="resume.pdf",
        )

        assert content == b"%PDF-1.4 Mock Blob Content"
        assert filename == "REF-2026-000004_Salman-Khan_VP.pdf"
        assert content_type == "application/pdf"


@pytest.mark.asyncio
async def test_blob_download_cv_not_found(mock_blob_env):
    with patch("app.services.storage.blob_service.BlobServiceClient") as mock_bsc:
        service_client_instance = MagicMock()
        mock_bsc.from_connection_string.return_value = service_client_instance
        container_client = MagicMock()
        service_client_instance.get_container_client.return_value = container_client
        container_client.list_blobs.return_value = []

        service = BlobStorageService()

        with pytest.raises(HTTPException) as exc_info:
            await service.download_cv(
                drive_id=None,
                item_id=None,
                referral_number="REF-2026-999999",
            )
        assert exc_info.value.status_code == 404

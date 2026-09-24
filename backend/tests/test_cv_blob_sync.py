import os
import pytest
from unittest.mock import MagicMock, patch
from app.cv_intelligence.blob_sync import (
    is_cv_blob_sync_enabled,
    download_cv_db_from_blob,
    upload_cv_db_to_blob,
    delete_cv_db_from_blob,
)


def test_cv_blob_sync_disabled_when_local(monkeypatch):
    monkeypatch.setattr("app.config.settings.CV_STORAGE_TYPE", "local")
    assert not is_cv_blob_sync_enabled()
    assert not download_cv_db_from_blob()
    assert not upload_cv_db_to_blob()
    assert not delete_cv_db_from_blob()


def test_cv_blob_sync_disabled_without_connection_string(monkeypatch):
    monkeypatch.setattr("app.config.settings.CV_STORAGE_TYPE", "blob")
    monkeypatch.setattr("app.config.settings.AZURE_STORAGE_CONNECTION_STRING", "")
    assert not is_cv_blob_sync_enabled()


def test_cv_blob_sync_enabled(monkeypatch):
    monkeypatch.setattr("app.config.settings.CV_STORAGE_TYPE", "blob")
    monkeypatch.setattr(
        "app.config.settings.AZURE_STORAGE_CONNECTION_STRING",
        "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=fake;EndpointSuffix=core.windows.net",
    )
    assert is_cv_blob_sync_enabled()


def test_download_cv_db_from_blob_success(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.CV_STORAGE_TYPE", "blob")
    monkeypatch.setattr(
        "app.config.settings.AZURE_STORAGE_CONNECTION_STRING",
        "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=fake;EndpointSuffix=core.windows.net",
    )

    dest_file = str(tmp_path / "cv_intelligence.db")
    with patch("azure.storage.blob.BlobServiceClient") as mock_bsc:
        client_instance = MagicMock()
        mock_bsc.from_connection_string.return_value = client_instance
        container_client = MagicMock()
        client_instance.get_container_client.return_value = container_client
        blob_client = MagicMock()
        container_client.get_blob_client.return_value = blob_client
        blob_client.download_blob.return_value.readall.return_value = b"SQLite format 3\x00mock"

        result = download_cv_db_from_blob(target_path=dest_file)
        assert result is True
        assert os.path.exists(dest_file)
        with open(dest_file, "rb") as f:
            assert f.read() == b"SQLite format 3\x00mock"


def test_upload_cv_db_to_blob_success(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.CV_STORAGE_TYPE", "blob")
    monkeypatch.setattr(
        "app.config.settings.AZURE_STORAGE_CONNECTION_STRING",
        "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=fake;EndpointSuffix=core.windows.net",
    )

    src_file = tmp_path / "cv_intelligence.db"
    src_file.write_bytes(b"SQLite format 3\x00mock data")

    with patch("azure.storage.blob.BlobServiceClient") as mock_bsc:
        client_instance = MagicMock()
        mock_bsc.from_connection_string.return_value = client_instance
        container_client = MagicMock()
        client_instance.get_container_client.return_value = container_client
        blob_client = MagicMock()
        container_client.get_blob_client.return_value = blob_client

        result = upload_cv_db_to_blob(source_path=str(src_file))
        assert result is True
        blob_client.upload_blob.assert_called_once()

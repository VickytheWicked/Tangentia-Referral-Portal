import os
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger("cv_intelligence.blob_sync")


def is_cv_blob_sync_enabled() -> bool:
    """Check if Azure Blob Storage persistence is enabled for CV Intelligence DB."""
    if settings.CV_STORAGE_TYPE.lower() == "blob":
        if not settings.AZURE_STORAGE_CONNECTION_STRING:
            logger.warning(
                "CV_STORAGE_TYPE is set to 'blob' but AZURE_STORAGE_CONNECTION_STRING is missing. "
                "Falling back to local SQLite storage."
            )
            return False
        return True
    return False


def _get_blob_client():
    """Retrieve Azure Blob Client for the cv_intelligence.db file."""
    from azure.storage.blob import BlobServiceClient

    blob_service = BlobServiceClient.from_connection_string(
        settings.AZURE_STORAGE_CONNECTION_STRING
    )
    container_name = settings.BLOB_DATA_CONTAINER
    blob_name = settings.BLOB_CV_INTELLIGENCE_NAME

    try:
        blob_service.create_container(container_name)
    except Exception:
        pass

    container_client = blob_service.get_container_client(container_name)
    return container_client.get_blob_client(blob_name)


def download_cv_db_from_blob(target_path: Optional[str] = None) -> bool:
    """
    Download cv_intelligence.db from Azure Blob Storage into local cache.
    Returns True if downloaded successfully, False if file was not found or disabled.
    """
    if not is_cv_blob_sync_enabled():
        return False

    db_path = target_path or settings.CV_INTELLIGENCE_DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    try:
        blob_client = _get_blob_client()
        download_stream = blob_client.download_blob()
        with open(db_path, "wb") as f:
            f.write(download_stream.readall())
        logger.info(f"Successfully restored cv_intelligence.db from Azure Blob Storage to {db_path}")
        return True
    except Exception as e:
        err_msg = str(e)
        if "BlobNotFound" in err_msg or "ResourceNotFound" in err_msg:
            logger.info("No existing cv_intelligence.db in Azure Blob Storage. A fresh one will be uploaded on first write.")
            return False
        logger.warning(f"Could not download cv_intelligence.db from Azure Blob Storage: {e}")
        return False


def upload_cv_db_to_blob(source_path: Optional[str] = None) -> bool:
    """
    Upload local cv_intelligence.db to Azure Blob Storage.
    Returns True if uploaded successfully, False otherwise.
    """
    if not is_cv_blob_sync_enabled():
        return False

    db_path = source_path or settings.CV_INTELLIGENCE_DB_PATH
    if not os.path.exists(db_path):
        logger.warning(f"Local cv_intelligence.db file does not exist at {db_path}. Skipping upload.")
        return False

    try:
        from azure.storage.blob import ContentSettings

        blob_client = _get_blob_client()
        with open(db_path, "rb") as f:
            blob_client.upload_blob(
                f,
                overwrite=True,
                content_settings=ContentSettings(content_type="application/x-sqlite3"),
            )
        logger.info(f"Successfully persisted cv_intelligence.db to Azure Blob Storage ({settings.BLOB_DATA_CONTAINER}/{settings.BLOB_CV_INTELLIGENCE_NAME})")
        return True
    except Exception as e:
        logger.error(f"Failed to persist cv_intelligence.db to Azure Blob Storage: {e}", exc_info=True)
        return False


def delete_cv_db_from_blob() -> bool:
    """
    Delete cv_intelligence.db from Azure Blob Storage (used during reset / purge).
    """
    if not is_cv_blob_sync_enabled():
        return False

    try:
        blob_client = _get_blob_client()
        blob_client.delete_blob()
        logger.info("Successfully deleted cv_intelligence.db from Azure Blob Storage.")
        return True
    except Exception as e:
        err_msg = str(e)
        if "BlobNotFound" in err_msg or "ResourceNotFound" in err_msg:
            return True
        logger.warning(f"Failed to delete cv_intelligence.db from Azure Blob Storage: {e}")
        return False

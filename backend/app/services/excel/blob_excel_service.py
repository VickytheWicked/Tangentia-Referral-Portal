import os
import logging
from typing import Dict, List, Any, Optional

from azure.storage.blob import BlobServiceClient, ContentSettings

from app.config import settings
from app.services.excel.local_excel_service import LocalExcelService

logger = logging.getLogger(__name__)

EXCEL_BLOB_NAME = "Tangentia_Referrals.xlsx"


class BlobExcelService(LocalExcelService):
    """
    Azure Blob Storage-backed Excel service.

    Extends LocalExcelService by syncing the .xlsx file to/from Azure Blob Storage.
    All openpyxl read/write logic is inherited — only the persistence layer changes:
      - On init: download workbook from blob → local temp path
      - After every write: upload local file back to blob
    """

    def __init__(self):
        if not settings.AZURE_STORAGE_CONNECTION_STRING:
            raise RuntimeError(
                "AZURE_STORAGE_CONNECTION_STRING is required when EXCEL_STORAGE_TYPE='blob'. "
                "Set it in your .env or App Service configuration."
            )
        self._blob_service = BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STRING
        )
        self._container_name = settings.BLOB_DATA_CONTAINER
        self._blob_name = EXCEL_BLOB_NAME

        # Ensure the container exists
        try:
            self._blob_service.create_container(self._container_name)
            logger.info(f"Created blob container: {self._container_name}")
        except Exception:
            pass

        # Use a local cache path for openpyxl operations
        local_cache_dir = os.path.dirname(settings.EXCEL_FILE_PATH)
        os.makedirs(local_cache_dir, exist_ok=True)
        local_path = os.path.join(local_cache_dir, EXCEL_BLOB_NAME)

        # Download existing workbook from blob (if it exists)
        self._download_from_blob(local_path)

        # Initialize parent with the local cached path
        super().__init__(file_path=local_path)

    def _get_blob_client(self):
        container = self._blob_service.get_container_client(self._container_name)
        return container.get_blob_client(self._blob_name)

    def _download_from_blob(self, local_path: str) -> bool:
        """Download the Excel workbook from blob to local cache. Returns True if file existed."""
        try:
            blob_client = self._get_blob_client()
            download_stream = blob_client.download_blob()
            with open(local_path, "wb") as f:
                f.write(download_stream.readall())
            logger.info(f"Downloaded Excel workbook from blob: {self._blob_name}")
            return True
        except Exception as e:
            if "BlobNotFound" in str(e) or "ResourceNotFound" in str(e):
                logger.info("No existing Excel workbook in blob — will create on first write.")
                return False
            logger.warning(f"Failed to download Excel from blob: {e}")
            return False

    def _upload_to_blob(self):
        """Upload the local Excel file back to blob storage."""
        try:
            blob_client = self._get_blob_client()
            with open(self.file_path, "rb") as f:
                blob_client.upload_blob(
                    f,
                    overwrite=True,
                    content_settings=ContentSettings(
                        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    ),
                )
            logger.info(f"Uploaded Excel workbook to blob: {self._blob_name}")
        except Exception as e:
            logger.error(f"Failed to upload Excel to blob: {e}", exc_info=True)

    # === Override write methods to sync back to blob after each mutation ===

    def initialize_workbook(self) -> None:
        super().initialize_workbook()
        self._upload_to_blob()

    def append_referral(self, referral_data: Dict[str, Any]) -> None:
        super().append_referral(referral_data)
        self._upload_to_blob()

    def update_referral_status(
        self,
        referral_id: str,
        referral_number: str,
        new_status: str,
        comment: Optional[str],
        changed_by: str,
    ) -> None:
        super().update_referral_status(referral_id, referral_number, new_status, comment, changed_by)
        self._upload_to_blob()

    def append_hr_note(
        self,
        referral_id: str,
        referral_number: str,
        note: str,
        created_by: str,
    ) -> None:
        super().append_hr_note(referral_id, referral_number, note, created_by)
        self._upload_to_blob()

    def save_job_position(self, job_data: Dict[str, Any]) -> None:
        super().save_job_position(job_data)
        self._upload_to_blob()

    def delete_referral(self, referral_id: str) -> None:
        super().delete_referral(referral_id)
        self._upload_to_blob()

    def save_user(self, user_data: Dict[str, Any]) -> None:
        super().save_user(user_data)
        self._upload_to_blob()

    def save_hired_record(self, hired_data: Dict[str, Any]) -> None:
        super().save_hired_record(hired_data)
        self._upload_to_blob()


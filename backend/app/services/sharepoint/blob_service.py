import uuid
import logging
import mimetypes
from datetime import datetime, timezone
from typing import Tuple, Optional

from azure.storage.blob import BlobServiceClient, ContentSettings
from fastapi import HTTPException, status

from app.config import settings
from app.services.sharepoint.base import SharePointServiceInterface, SharePointUploadResult

logger = logging.getLogger(__name__)


class BlobSharePointService(SharePointServiceInterface):
    """
    Azure Blob Storage implementation of the SharePoint document interface.
    Stores CV files in the configured blob container with year-based folder hierarchy.
    Drop-in replacement for MockSharePointService — same interface, durable cloud storage.
    """

    def __init__(self):
        if not settings.AZURE_STORAGE_CONNECTION_STRING:
            raise RuntimeError(
                "AZURE_STORAGE_CONNECTION_STRING is required when SHAREPOINT_STORAGE_TYPE='blob'. "
                "Set it in your .env or App Service configuration."
            )
        self._blob_service = BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STRING
        )
        self._container_name = settings.BLOB_CV_CONTAINER
        # Ensure the container exists
        try:
            self._blob_service.create_container(self._container_name)
            logger.info(f"Created blob container: {self._container_name}")
        except Exception:
            # Container already exists — this is fine
            pass

    def _get_container_client(self):
        return self._blob_service.get_container_client(self._container_name)

    async def upload_cv(
        self,
        file_bytes: bytes,
        filename: str,
        referral_number: str,
    ) -> SharePointUploadResult:
        year = str(datetime.now(timezone.utc).year)
        blob_name = f"{year}/{filename}"

        content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            content_type = "application/pdf"

        try:
            container = self._get_container_client()
            blob_client = container.get_blob_client(blob_name)
            blob_client.upload_blob(
                file_bytes,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type),
            )
        except Exception as e:
            logger.error(f"Azure Blob upload failed for {blob_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to upload CV to Azure Blob Storage.",
            )

        item_id = f"blob:{blob_name}"
        drive_id = f"blob:{self._container_name}"

        return SharePointUploadResult(
            drive_id=drive_id,
            item_id=item_id,
            file_id=item_id,
            web_url=blob_client.url,
            stored_filename=filename,
        )

    async def download_cv(
        self,
        drive_id: Optional[str] = None,
        item_id: Optional[str] = None,
        referral_number: Optional[str] = None,
        stored_filename: Optional[str] = None,
        original_filename: Optional[str] = None,
        candidate_name: Optional[str] = None,
    ) -> Tuple[bytes, str, str]:
        container = self._get_container_client()
        blob_name = None
        if item_id:
            blob_name = item_id.removeprefix("blob:")

        # Try direct download if blob_name is known
        if blob_name:
            try:
                blob_client = container.get_blob_client(blob_name)
                download_stream = blob_client.download_blob()
                file_bytes = download_stream.readall()
                filename = blob_name.split("/")[-1]
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = (
                        "application/pdf"
                        if filename.endswith(".pdf")
                        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                return file_bytes, filename, content_type
            except Exception as e:
                logger.warning(f"Direct Azure Blob download failed for {blob_name}: {e}. Trying fallback lookup.")

        # Fallback: search container for blob matching referral_number or stored_filename
        try:
            for b in container.list_blobs():
                name = b.name
                match = False
                if referral_number and referral_number in name:
                    match = True
                elif stored_filename and stored_filename != "resume.pdf" and (name.endswith(stored_filename) or stored_filename in name):
                    match = True

                if match:
                    blob_client = container.get_blob_client(name)
                    download_stream = blob_client.download_blob()
                    file_bytes = download_stream.readall()
                    filename = name.split("/")[-1]
                    content_type, _ = mimetypes.guess_type(filename)
                    if not content_type:
                        content_type = (
                            "application/pdf"
                            if filename.endswith(".pdf")
                            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    return file_bytes, filename, content_type
        except Exception as e:
            logger.error(f"Error searching blobs in container {self._container_name}: {e}")

        logger.error(f"CV blob not found in container {self._container_name} for item_id={item_id}, referral_number={referral_number}, stored_filename={stored_filename}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV document not found in Azure Blob Storage.",
        )

    async def delete_cv(
        self,
        drive_id: Optional[str] = None,
        item_id: Optional[str] = None,
    ) -> bool:
        if not item_id:
            return True
        blob_name = item_id.removeprefix("blob:")

        try:
            container = self._get_container_client()
            container.delete_blob(blob_name)
            logger.info(f"Deleted blob: {blob_name}")
        except Exception as e:
            logger.warning(f"Azure Blob delete failed for {blob_name}: {e}")
        return True

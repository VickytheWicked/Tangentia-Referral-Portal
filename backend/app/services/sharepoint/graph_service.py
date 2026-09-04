import logging
from datetime import datetime, timezone
from typing import Tuple
import msal
import httpx
from fastapi import HTTPException, status
from app.config import settings
from app.services.sharepoint.base import SharePointServiceInterface, SharePointUploadResult

logger = logging.getLogger(__name__)


class GraphSharePointService(SharePointServiceInterface):
    """
    Production Microsoft Graph API implementation for SharePoint Online document libraries.
    Authenticates via MSAL OAuth2 Client Credentials flow.
    """

    def __init__(self):
        self.tenant_id = settings.AZURE_TENANT_ID
        self.client_id = settings.AZURE_CLIENT_ID
        self.client_secret = settings.AZURE_CLIENT_SECRET
        self.site_id = settings.SHAREPOINT_SITE_ID
        self.drive_id = settings.SHAREPOINT_DRIVE_ID
        self.root_folder = settings.SHAREPOINT_ROOT_FOLDER or "Referral-CVs"
        
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["https://graph.microsoft.com/.default"]

        self._msal_app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority,
        )

    def _get_access_token(self) -> str:
        """Acquire application access token using MSAL client credentials flow"""
        result = self._msal_app.acquire_token_silent(self.scopes, account=None)
        if not result:
            result = self._msal_app.acquire_token_for_client(scopes=self.scopes)

        if "access_token" in result:
            return result["access_token"]
        
        error_msg = result.get("error_description") or result.get("error") or "Unknown authentication failure"
        logger.error(f"Failed to acquire Microsoft Graph token: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to authenticate with Microsoft Graph API for SharePoint access.",
        )

    async def upload_cv(
        self,
        file_bytes: bytes,
        filename: str,
        referral_number: str,
    ) -> SharePointUploadResult:
        """
        Upload CV to SharePoint document library:
        Path: /{root_folder}/{year}/{filename}
        """
        token = self._get_access_token()
        year = str(datetime.now(timezone.utc).year)
        
        # Target path in document library
        path = f"{self.root_folder}/{year}/{filename}"
        
        if self.site_id and self.drive_id:
            url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{self.drive_id}/root:/{path}:/content"
        elif self.drive_id:
            url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/root:/{path}:/content"
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SharePoint Drive ID is not configured.",
            )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.put(url, headers=headers, content=file_bytes)
            except Exception as e:
                logger.error(f"Network error communicating with Microsoft Graph: {e}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Network error uploading document to SharePoint.",
                )

        if response.status_code not in (200, 201):
            logger.error(f"Microsoft Graph upload failed [{response.status_code}]: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="SharePoint document library upload failed. File could not be stored.",
            )

        data = response.json()
        item_id = data.get("id", "")
        web_url = data.get("webUrl", "")
        drive_id = data.get("parentReference", {}).get("driveId", self.drive_id)

        return SharePointUploadResult(
            drive_id=drive_id,
            item_id=item_id,
            file_id=item_id,
            web_url=web_url,
            stored_filename=filename,
        )

    async def download_cv(
        self,
        drive_id: str,
        item_id: str,
    ) -> Tuple[bytes, str, str]:
        """Download CV binary stream from SharePoint via Microsoft Graph"""
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        # First get metadata for filename & MIME type
        meta_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}"
        content_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/content"

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            meta_res = await client.get(meta_url, headers=headers)
            if meta_res.status_code != 200:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File metadata not found in SharePoint.")
            
            meta_data = meta_res.json()
            filename = meta_data.get("name", "candidate_cv.pdf")
            content_type = meta_data.get("file", {}).get("mimeType", "application/pdf")

            content_res = await client.get(content_url, headers=headers)
            if content_res.status_code != 200:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Failed to retrieve file from SharePoint.")

            return content_res.content, filename, content_type

    async def delete_cv(
        self,
        drive_id: str,
        item_id: str,
    ) -> bool:
        """Rollback helper: delete uploaded item if downstream DB operations fail"""
        try:
            token = self._get_access_token()
            url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}"
            headers = {"Authorization": f"Bearer {token}"}

            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.delete(url, headers=headers)
                return res.status_code in (204, 404)
        except Exception as e:
            logger.warning(f"Failed to rollback/delete file in SharePoint {item_id}: {e}")
            return False

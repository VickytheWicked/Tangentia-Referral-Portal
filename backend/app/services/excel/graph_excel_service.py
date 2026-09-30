import logging
from typing import Dict, List, Any, Optional
import msal
import httpx
from fastapi import HTTPException, status

from app.config import settings
from app.services.excel.local_excel_service import LocalExcelService

logger = logging.getLogger(__name__)


class GraphExcelService(LocalExcelService):
    """
    Microsoft Excel Online implementation via Microsoft Graph API.
    Writes rows directly to cloud-hosted Excel Online workbooks,
    while maintaining a synchronized local Excel file cache for instant offline reads and export.
    """

    def __init__(self):
        super().__init__()
        self.tenant_id = settings.AZURE_TENANT_ID
        self.client_id = settings.AZURE_CLIENT_ID
        self.client_secret = settings.AZURE_CLIENT_SECRET
        self.drive_id = settings.EXCEL_DRIVE_ID
        self.item_id = settings.EXCEL_FILE_ITEM_ID
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["https://graph.microsoft.com/.default"]

        self._msal_app = None
        if self.client_id and self.client_secret:
            self._msal_app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority,
            )

    def _get_access_token(self) -> Optional[str]:
        """Acquire application access token using MSAL client credentials flow"""
        if not self._msal_app:
            return None
        result = self._msal_app.acquire_token_silent(self.scopes, account=None)
        if not result:
            result = self._msal_app.acquire_token_for_client(scopes=self.scopes)
        return result.get("access_token")

    def append_referral(self, referral_data: Dict[str, Any]) -> None:
        """Append referral to local Excel cache and push to Microsoft Excel Online"""
        # Always update local .xlsx cache first
        super().append_referral(referral_data)

        # Call Microsoft Graph Excel REST API if configured
        token = self._get_access_token()
        if not (token and self.drive_id and self.item_id):
            logger.info("Graph Excel credentials not fully set; updated local Excel workbook.")
            return

        endpoint = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/items/{self.item_id}/workbook/tables/Referrals/rows/add"
        row_values = [
            referral_data.get("referral_number", ""),
            referral_data.get("candidate_name", ""),
            referral_data.get("candidate_email", ""),
            referral_data.get("candidate_phone", ""),
            referral_data.get("referred_by_name", ""),
            referral_data.get("years_of_experience", 0.0),
            referral_data.get("relationship", ""),
            referral_data.get("position_title", ""),
            referral_data.get("status", "Submitted"),
            referral_data.get("id", ""),
            referral_data.get("position_id", ""),
            referral_data.get("referred_by_user_id", ""),
            referral_data.get("linkedin_url", "") or "",
            referral_data.get("github_url", "") or "",
            referral_data.get("original_filename", ""),
            referral_data.get("storage_file_url", "") or "",
            referral_data.get("referral_note", ""),
            referral_data.get("created_at", ""),
            referral_data.get("updated_at", ""),
        ]

        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"values": [row_values]},
                )
                if res.status_code in [200, 201]:
                    logger.info(f"Successfully synced referral {referral_data.get('referral_number')} to Microsoft Excel Online.")
                else:
                    logger.warning(f"Graph Excel API returned {res.status_code}: {res.text}")
        except Exception as e:
            logger.error(f"Failed to push row to Microsoft Excel Online via Graph API: {e}")

    def update_referral_status(
        self,
        referral_id: str,
        referral_number: str,
        new_status: str,
        comment: Optional[str],
        changed_by: str,
    ) -> None:
        """Update referral status in local cache and push to Microsoft Excel Online"""
        super().update_referral_status(
            referral_id, referral_number, new_status, comment, changed_by
        )

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class SharePointUploadResult:
    drive_id: str
    item_id: str
    file_id: str
    web_url: str
    stored_filename: str


class SharePointServiceInterface(ABC):
    """
    Abstract interface for SharePoint document library operations.
    Decouples business logic from Microsoft Graph API implementation.
    """

    @abstractmethod
    async def upload_cv(
        self,
        file_bytes: bytes,
        filename: str,
        referral_number: str,
    ) -> SharePointUploadResult:
        """
        Upload a CV document to the configured SharePoint document library.
        Returns metadata identifiers for database storage.
        """
        pass

    @abstractmethod
    async def download_cv(
        self,
        drive_id: str,
        item_id: str,
    ) -> Tuple[bytes, str, str]:
        """
        Download CV file bytes from SharePoint for authorized proxy streaming.
        Returns: (file_bytes, filename, content_type)
        """
        pass

    @abstractmethod
    async def delete_cv(
        self,
        drive_id: str,
        item_id: str,
    ) -> bool:
        """
        Delete a file from SharePoint (used for transactional rollback if database commit fails).
        """
        pass

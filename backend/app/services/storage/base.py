from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class StorageUploadResult:
    drive_id: str
    item_id: str
    file_id: str
    web_url: str
    stored_filename: str


class StorageServiceInterface(ABC):
    """
    Abstract interface for document and CV file storage operations.
    Decouples referral business logic from cloud or local storage providers.
    """

    @abstractmethod
    async def upload_cv(
        self,
        file_bytes: bytes,
        filename: str,
        referral_number: str,
    ) -> StorageUploadResult:
        """
        Upload a CV document to the configured storage repository.
        Returns metadata identifiers for database storage.
        """
        pass

    @abstractmethod
    async def download_cv(
        self,
        drive_id: Optional[str] = None,
        item_id: Optional[str] = None,
        referral_number: Optional[str] = None,
        stored_filename: Optional[str] = None,
        original_filename: Optional[str] = None,
        candidate_name: Optional[str] = None,
    ) -> Tuple[bytes, str, str]:
        """
        Download CV file bytes from storage for authorized proxy streaming.
        Returns: (file_bytes, filename, content_type)
        """
        pass

    @abstractmethod
    async def delete_cv(
        self,
        drive_id: Optional[str] = None,
        item_id: Optional[str] = None,
    ) -> bool:
        """
        Delete a file from storage (used for transactional rollback if database commit fails).
        """
        pass

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class ExcelServiceInterface(ABC):
    """
    Abstract interface for Microsoft Excel Online & local .xlsx workbook persistence.
    Decouples storage logic from Microsoft Graph API implementation.
    """

    @abstractmethod
    def initialize_workbook(self) -> None:
        """
        Ensure the Excel workbook exists with structured sheets and styled table headers.
        """
        pass

    @abstractmethod
    def load_all_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract all records from Excel sheets into structured dictionaries.
        Used on startup to populate the in-memory query engine.
        """
        pass

    @abstractmethod
    def append_referral(self, referral_data: Dict[str, Any]) -> None:
        """
        Append a new candidate referral row to the Referrals worksheet.
        """
        pass

    @abstractmethod
    def update_referral_status(
        self,
        referral_id: str,
        referral_number: str,
        new_status: str,
        comment: Optional[str],
        changed_by: str,
    ) -> None:
        """
        Update candidate status in Referrals worksheet and append audit entry in StatusHistory.
        """
        pass

    @abstractmethod
    def append_hr_note(
        self,
        referral_id: str,
        referral_number: str,
        note: str,
        created_by: str,
    ) -> None:
        """
        Append confidential internal note to HRNotes worksheet.
        """
        pass

    @abstractmethod
    def save_job_position(self, job_data: Dict[str, Any]) -> None:
        """
        Insert or update a job opening in JobPositions worksheet.
        """
        pass

    @abstractmethod
    def get_workbook_bytes(self) -> bytes:
        """
        Retrieve raw binary bytes of the Excel workbook for download/export.
        """
        pass

    @abstractmethod
    def delete_referral(self, referral_id: str) -> None:
        """
        Delete candidate referral and related entries from Microsoft Excel storage.
        """
        pass

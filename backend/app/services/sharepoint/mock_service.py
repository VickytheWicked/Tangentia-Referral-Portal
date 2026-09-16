import os
import uuid
import mimetypes
from datetime import datetime, timezone
from typing import Tuple, Optional
from fastapi import HTTPException, status
from app.config import settings
from app.services.sharepoint.base import SharePointServiceInterface, SharePointUploadResult


class MockSharePointService(SharePointServiceInterface):
    """
    Isolated local mock SharePoint storage service for development and offline testing.
    Maintains the exact same folder hierarchy ({root_folder}/{year}/{filename}) and API contract.
    """

    def __init__(self, storage_dir: str = None):
        self.base_dir = storage_dir or settings.LOCAL_STORAGE_DIR
        os.makedirs(self.base_dir, exist_ok=True)
        self.index_file = os.path.join(self.base_dir, "_index.json")

    def _load_index(self) -> dict:
        import json
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r") as fp:
                    return json.load(fp)
            except Exception:
                return {}
        return {}

    def _save_index(self, index: dict):
        import json
        try:
            with open(self.index_file, "w") as fp:
                json.dump(index, fp)
        except Exception:
            pass

    async def upload_cv(
        self,
        file_bytes: bytes,
        filename: str,
        referral_number: str,
    ) -> SharePointUploadResult:
        year = str(datetime.now(timezone.utc).year)
        target_dir = os.path.join(self.base_dir, year)
        os.makedirs(target_dir, exist_ok=True)

        file_path = os.path.join(target_dir, filename)
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        mock_item_id = f"mock-item-{uuid.uuid4()}"
        mock_drive_id = "mock-drive-tangentia-cvs"

        index = self._load_index()
        index[mock_item_id] = file_path
        self._save_index(index)

        return SharePointUploadResult(
            drive_id=mock_drive_id,
            item_id=mock_item_id,
            file_id=mock_item_id,
            web_url=f"https://tangentia.sharepoint.com/sites/hr/Referral-CVs/{year}/{filename}",
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
        index = self._load_index()
        if item_id:
            file_path = index.get(item_id)
            if file_path and os.path.exists(file_path):
                filename = os.path.basename(file_path)
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = "application/pdf" if filename.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                with open(file_path, "rb") as fp:
                    return fp.read(), filename, content_type

        # Match by referral_number or stored_filename
        for root, _, files in os.walk(self.base_dir):
            for f in files:
                if f.startswith("_") or f.startswith("."):
                    continue
                if not (f.lower().endswith(".pdf") or f.lower().endswith(".docx")):
                    continue
                match = False
                if referral_number and referral_number in f:
                    match = True
                elif stored_filename and stored_filename != "resume.pdf" and (f.endswith(stored_filename) or stored_filename in f):
                    match = True

                if match:
                    file_path = os.path.join(root, f)
                    content_type, _ = mimetypes.guess_type(f)
                    if not content_type:
                        content_type = "application/pdf" if f.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    with open(file_path, "rb") as fp:
                        return fp.read(), f, content_type

        # Fallback to any file in mock storage
        for root, _, files in os.walk(self.base_dir):
            for f in files:
                if f.startswith("_") or f.startswith("."):
                    continue
                if not (f.lower().endswith(".pdf") or f.lower().endswith(".docx")):
                    continue
                file_path = os.path.join(root, f)
                content_type, _ = mimetypes.guess_type(f)
                if not content_type:
                    content_type = "application/pdf" if f.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                with open(file_path, "rb") as fp:
                    return fp.read(), f, content_type

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV document not found in mock SharePoint storage.")

    async def delete_cv(
        self,
        drive_id: Optional[str] = None,
        item_id: Optional[str] = None,
    ) -> bool:
        if not item_id:
            return True
        index = self._load_index()
        if item_id in index:
            try:
                os.remove(index[item_id])
                del index[item_id]
                self._save_index(index)
            except Exception:
                pass
        return True

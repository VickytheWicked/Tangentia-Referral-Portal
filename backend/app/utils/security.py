import re
import os
from typing import Tuple
from fastapi import HTTPException, status
from app.config import settings

# Magic byte signatures
MAGIC_BYTES = {
    "pdf": b"%PDF-",
    "docx": b"PK\x03\x04",  # ZIP container header for DOCX
}


def sanitize_filename_component(text: str) -> str:
    """Sanitize string to be safe for filenames and URLs"""
    # Replace whitespace and punctuation with dashes
    text = re.sub(r"[^\w\s-]", "", text).strip()
    text = re.sub(r"[-\s]+", "-", text)
    return text[:40]  # limit component length


def generate_storage_filename(referral_number: str, candidate_name: str, position_title: str, original_filename: str) -> str:
    """
    Generate predictable, standardized storage filename:
    e.g. REF-2026-000123_Rahul-Sharma_Backend-Developer.pdf
    """
    _, ext = os.path.splitext(original_filename.lower())
    if ext not in settings.ALLOWED_EXTENSIONS:
        ext = ".pdf"

    cand_slug = sanitize_filename_component(candidate_name) or "Candidate"
    pos_slug = sanitize_filename_component(position_title) or "Position"

    return f"{referral_number}_{cand_slug}_{pos_slug}{ext}"


generate_cv_filename = generate_storage_filename


def validate_cv_file(filename: str, content: bytes) -> Tuple[str, str]:
    """
    Validate CV file extension, size, and magic byte headers.
    Returns (cleaned_extension, mime_type)
    """
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {max_mb} MB.",
        )

    _, ext = os.path.splitext(filename.lower())
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension '{ext}'. Only PDF and DOCX files are permitted.",
        )

    # Validate Magic Bytes
    if ext == ".pdf":
        if not content.startswith(MAGIC_BYTES["pdf"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match valid PDF document signature.",
            )
        mime = "application/pdf"
    elif ext == ".docx":
        if not content.startswith(MAGIC_BYTES["docx"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match valid DOCX document signature.",
            )
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        mime = "application/octet-stream"

    return ext, mime

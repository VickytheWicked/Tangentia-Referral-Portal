import re
import logging
from datetime import datetime, timezone
from typing import List, Tuple, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.referral import Referral, ReferralStatus
from app.models.job_position import JobPosition
from app.models.status_history import ReferralStatusHistory
from app.models.hr_note import HRNote
from app.models.user import User, UserRole
from app.schemas.referral import ReferralCreateForm
from app.schemas.duplicate import DuplicateCheckResponse, DuplicateMatch
from app.services.sharepoint.base import SharePointServiceInterface
from app.utils.security import validate_cv_file, generate_sharepoint_filename

logger = logging.getLogger(__name__)


def normalize_phone(phone: str) -> str:
    """Normalize phone string by keeping only digits"""
    return re.sub(r"\D", "", phone)


def generate_referral_number(db: Session) -> str:
    """Generate sequential unique referral code: REF-{YEAR}-{000001}"""
    current_year = datetime.now(timezone.utc).year
    year_prefix = f"REF-{current_year}-"

    # Count existing referrals for this year
    count = db.query(func.count(Referral.id)).filter(
        Referral.referral_number.like(f"{year_prefix}%")
    ).scalar() or 0

    next_sequence = count + 1
    return f"{year_prefix}{next_sequence:06d}"


def check_duplicate_candidate(
    db: Session,
    candidate_email: str,
    candidate_phone: str,
    candidate_name: str,
    position_id: str,
) -> DuplicateCheckResponse:
    """
    Check if a candidate with matching email, phone, or name+position already exists.
    Returns structured matches for employee review.
    """
    matches: List[DuplicateMatch] = []
    norm_email = candidate_email.lower().strip()
    norm_phone = normalize_phone(candidate_phone)
    norm_name = candidate_name.strip().lower()

    # Query all active referrals
    candidates = db.query(Referral).filter(
        Referral.status != ReferralStatus.WITHDRAWN.value
    ).all()

    for ref in candidates:
        reasons = []
        if ref.candidate_email.lower().strip() == norm_email:
            reasons.append("Matching Email Address")
        if norm_phone and normalize_phone(ref.candidate_phone) == norm_phone:
            reasons.append("Matching Phone Number")
        if ref.candidate_name.strip().lower() == norm_name and ref.position_id == position_id:
            reasons.append("Matching Name & Job Position")

        if reasons:
            referrer_name = ref.referred_by_name or (ref.referred_by.name if ref.referred_by else "Unknown Employee")
            pos_title = ref.position.title if ref.position else "General Position"
            matches.append(
                DuplicateMatch(
                    referral_id=ref.id,
                    referral_number=ref.referral_number,
                    candidate_name=ref.candidate_name,
                    candidate_email=ref.candidate_email,
                    position_title=pos_title,
                    status=ref.status,
                    referred_by_name=referrer_name,
                    created_at=ref.created_at.strftime("%Y-%m-%d"),
                    match_reason=", ".join(reasons),
                )
            )

    return DuplicateCheckResponse(
        is_duplicate=len(matches) > 0,
        matches=matches,
    )


async def create_referral_with_cv(
    db: Session,
    form_data: ReferralCreateForm,
    file: UploadFile,
    current_user: User,
    sharepoint_service: SharePointServiceInterface,
) -> Referral:
    """
    Atomic referral creation:
    1. Validate file format & magic bytes.
    2. Check position validity.
    3. Generate standardized filename.
    4. Upload CV to SharePoint document library.
    5. Save Referral and ReferralStatusHistory to PostgreSQL.
    6. Rollback SharePoint file if DB transaction fails.
    """
    if not form_data.candidate_consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate consent is mandatory before submitting a referral.",
        )

    # Check position exists
    position = db.query(JobPosition).filter(
        JobPosition.id == form_data.position_id,
        JobPosition.is_active == True,
    ).first()
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The selected job position is either invalid or no longer open.",
        )

    # Read and validate CV file
    file_bytes = await file.read()
    validate_cv_file(file.filename, file_bytes)

    # Generate atomic referral number & standardized SharePoint filename
    ref_number = generate_referral_number(db)
    stored_filename = generate_sharepoint_filename(
        referral_number=ref_number,
        candidate_name=form_data.candidate_name,
        position_title=position.title,
        original_filename=file.filename,
    )

    # Step 1: Upload to SharePoint
    upload_result = None
    try:
        upload_result = await sharepoint_service.upload_cv(
            file_bytes=file_bytes,
            filename=stored_filename,
            referral_number=ref_number,
        )
    except Exception as e:
        logger.error(f"SharePoint upload failed during referral creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Referral submission could not be completed. The CV could not be uploaded to SharePoint. Please try again.",
        )

    # Step 2: Save to Database
    try:
        referral_referrer = (form_data.referred_by_name.strip() if form_data.referred_by_name else None) or (current_user.name if current_user else "Employee")
        referral = Referral(
            referral_number=ref_number,
            candidate_name=form_data.candidate_name.strip(),
            candidate_email=form_data.candidate_email.lower().strip(),
            candidate_phone=form_data.candidate_phone.strip(),
            linkedin_url=form_data.linkedin_url.strip() if form_data.linkedin_url else None,
            github_url=form_data.github_url.strip() if form_data.github_url else None,
            years_of_experience=form_data.years_of_experience,
            relationship=form_data.relationship.strip(),
            referral_note=form_data.referral_note.strip(),
            position_id=position.id,
            referred_by_user_id=current_user.id,
            referred_by_name=referral_referrer,
            status=ReferralStatus.SUBMITTED.value,
            sharepoint_drive_id=upload_result.drive_id,
            sharepoint_item_id=upload_result.item_id,
            sharepoint_file_id=upload_result.file_id,
            sharepoint_file_url=upload_result.web_url,
            original_filename=file.filename,
            stored_filename=stored_filename,
            candidate_consent=True,
        )
        db.add(referral)
        db.flush()  # assign referral.id

        # Add initial audit history record
        history_entry = ReferralStatusHistory(
            referral_id=referral.id,
            old_status=None,
            new_status=ReferralStatus.SUBMITTED.value,
            changed_by_user_id=current_user.id,
            comment=f"Referral submitted by {referral_referrer}.",
        )
        db.add(history_entry)
        db.commit()
        db.refresh(referral)
        return referral

    except Exception as db_err:
        db.rollback()
        logger.error(f"Database commit failed, executing SharePoint rollback: {db_err}")
        # Clean up the file uploaded to SharePoint
        if upload_result and upload_result.item_id:
            await sharepoint_service.delete_cv(
                drive_id=upload_result.drive_id,
                item_id=upload_result.item_id,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save referral to database. Upload has been rolled back. Please try again.",
        )


def update_referral_status(
    db: Session,
    referral_id: str,
    new_status: str,
    comment: Optional[str],
    current_user: User,
) -> Referral:
    """
    Update referral status and write an audit history record.
    Restricted to HR Admins.
    """
    referral = db.query(Referral).filter(Referral.id == referral_id).first()
    if not referral:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found.")

    valid_statuses = [s.value for s in ReferralStatus]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{new_status}'. Allowed values: {', '.join(valid_statuses)}",
        )

    old_status = referral.status
    if old_status == new_status:
        return referral

    referral.status = new_status
    history = ReferralStatusHistory(
        referral_id=referral.id,
        old_status=old_status,
        new_status=new_status,
        changed_by_user_id=current_user.id,
        comment=comment or f"Status changed from {old_status} to {new_status} by {current_user.name}",
    )
    db.add(history)
    db.commit()
    db.refresh(referral)
    return referral


def withdraw_referral(
    db: Session,
    referral_id: str,
    current_user: User,
    comment: Optional[str] = None,
) -> Referral:
    """
    Allow referring employee to withdraw their referral if still in SUBMITTED status.
    """
    referral = db.query(Referral).filter(Referral.id == referral_id).first()
    if not referral:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found.")

    if referral.referred_by_user_id != current_user.id and current_user.role != UserRole.HR_ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only withdraw your own referrals.")

    if referral.status not in [ReferralStatus.SUBMITTED.value, ReferralStatus.UNDER_REVIEW.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Referral cannot be withdrawn once it has progressed to '{referral.status}'.",
        )

    old_status = referral.status
    referral.status = ReferralStatus.WITHDRAWN.value
    history = ReferralStatusHistory(
        referral_id=referral.id,
        old_status=old_status,
        new_status=ReferralStatus.WITHDRAWN.value,
        changed_by_user_id=current_user.id,
        comment=comment or f"Referral withdrawn by {current_user.name}.",
    )
    db.add(history)
    db.commit()
    db.refresh(referral)
    return referral


def add_hr_note(
    db: Session,
    referral_id: str,
    note_text: str,
    current_user: User,
) -> HRNote:
    """Add internal HR note to a candidate referral (HR only)"""
    referral = db.query(Referral).filter(Referral.id == referral_id).first()
    if not referral:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found.")

    hr_note = HRNote(
        referral_id=referral.id,
        created_by_user_id=current_user.id,
        note=note_text.strip(),
    )
    db.add(hr_note)
    db.commit()
    db.refresh(hr_note)
    return hr_note


async def get_referral_cv_bytes(
    db: Session,
    referral_id: str,
    current_user: User,
    sharepoint_service: SharePointServiceInterface,
) -> Tuple[bytes, str, str]:
    """
    Retrieve CV bytes from SharePoint.
    Enforces authorization: Must be HR Admin or the referring employee.
    """
    referral = db.query(Referral).filter(Referral.id == referral_id).first()
    if not referral:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found.")

    if current_user.role != UserRole.HR_ADMIN.value and referral.referred_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this candidate's CV.",
        )

    file_bytes, filename, content_type = await sharepoint_service.download_cv(
        drive_id=referral.sharepoint_drive_id,
        item_id=referral.sharepoint_item_id,
    )
    return file_bytes, referral.original_filename or filename, content_type

import re
import logging
from datetime import datetime, timezone
from typing import List, Tuple, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
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

    # Find maximum existing sequence number for this year
    all_numbers = db.query(Referral.referral_number).filter(
        Referral.referral_number.like(f"{year_prefix}%")
    ).all()
    max_seq = 0
    for (num,) in all_numbers:
        try:
            seq = int(num.split("-")[-1])
            if seq > max_seq:
                max_seq = seq
        except (ValueError, IndexError):
            pass
    next_sequence = max_seq + 1
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
    trimmed_email = candidate_email.strip()
    norm_email = trimmed_email.lower()
    trimmed_phone = candidate_phone.strip()
    norm_phone = normalize_phone(trimmed_phone)
    trimmed_name = candidate_name.strip()
    norm_name = trimmed_name.lower()

    # Query all active referrals
    candidates = db.query(Referral).filter(
        Referral.status != ReferralStatus.WITHDRAWN.value
    ).all()

    for ref in candidates:
        reasons = []
        ref_trimmed_email = (ref.candidate_email or "").strip()
        ref_norm_email = ref_trimmed_email.lower()
        if norm_email and ref_norm_email == norm_email:
            reasons.append(f"Matching Email Address: '{trimmed_email}' (existing candidate email: '{ref_trimmed_email}')")

        ref_trimmed_phone = (ref.candidate_phone or "").strip()
        ref_norm_phone = normalize_phone(ref_trimmed_phone)
        if norm_phone and ref_norm_phone and ref_norm_phone == norm_phone:
            reasons.append(f"Matching Phone Number: '{trimmed_phone}' (normalized digits: '{norm_phone}', existing candidate phone: '{ref_trimmed_phone}')")

        ref_trimmed_name = (ref.candidate_name or "").strip()
        ref_norm_name = ref_trimmed_name.lower()
        if norm_name and ref_norm_name == norm_name and ref.position_id == position_id:
            pos_title = ref.position.title if ref.position else "Target Position"
            reasons.append(f"Matching Name & Job Position: Name '{trimmed_name}' applied to '{pos_title}'")

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
                    match_reason="; ".join(reasons),
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
        referral_referrer_email = (str(form_data.referred_by_email).strip().lower() if form_data.referred_by_email else None) or (current_user.email if current_user else None)
        referral_referrer_phone = (str(form_data.referred_by_phone).strip() if form_data.referred_by_phone else None)
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
            referred_by_email=referral_referrer_email,
            referred_by_phone=referral_referrer_phone,
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

        # Write-through to Microsoft Excel
        try:
            from app.services.excel import get_excel_service
            excel_svc = get_excel_service()
            excel_svc.append_referral({
                "id": referral.id,
                "referral_number": referral.referral_number,
                "candidate_name": referral.candidate_name,
                "candidate_email": referral.candidate_email,
                "candidate_phone": referral.candidate_phone,
                "referred_by_name": referral.referred_by_name,
                "referred_by_email": referral.referred_by_email or current_user.email,
                "years_of_experience": referral.years_of_experience,
                "relationship": referral.relationship,
                "position_title": position.title if position else "N/A",
                "position_id": position.id,
                "referred_by_user_id": current_user.id,
                "status": referral.status,
                "linkedin_url": referral.linkedin_url,
                "github_url": referral.github_url,
                "original_filename": referral.original_filename,
                "sharepoint_file_url": referral.sharepoint_file_url,
                "referral_note": referral.referral_note,
                "created_at": referral.created_at.strftime("%Y-%m-%d %H:%M:%S") if referral.created_at else "",
                "updated_at": referral.updated_at.strftime("%Y-%m-%d %H:%M:%S") if referral.updated_at else "",
            })
        except Exception as excel_err:
            logger.warning(f"Excel write-through failed: {excel_err}")

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

    # If the candidate was hired, deactivate the position and auto-archive competing referrals
    if new_status == ReferralStatus.HIRED.value:
        position = db.query(JobPosition).filter(JobPosition.id == referral.position_id).first()
        if position and position.is_active:
            position.is_active = False
            try:
                from app.services.excel import get_excel_service
                get_excel_service().save_job_position({
                    "id": position.id,
                    "title": position.title,
                    "department": position.department,
                    "location": position.location,
                    "employment_type": position.employment_type,
                    "is_active": False,
                    "description": position.description,
                    "created_at": position.created_at.strftime("%Y-%m-%d %H:%M:%S") if position.created_at else "",
                })
            except Exception as pos_err:
                logger.warning(f"Failed to update deactivated position in Excel: {pos_err}")

        # Find and auto-archive all other active referrals for this position
        other_referrals = db.query(Referral).filter(
            Referral.position_id == referral.position_id,
            Referral.id != referral.id,
            Referral.status.notin_([ReferralStatus.HIRED.value, ReferralStatus.ARCHIVED.value]),
        ).all()

        pos_title = position.title if position else "Position"
        archive_reason = f"Position '{pos_title}' was filled by candidate {referral.candidate_name} (Hired). Automatically archived."

        for other_ref in other_referrals:
            other_old_status = other_ref.status
            other_ref.status = ReferralStatus.ARCHIVED.value
            other_hist = ReferralStatusHistory(
                referral_id=other_ref.id,
                old_status=other_old_status,
                new_status=ReferralStatus.ARCHIVED.value,
                changed_by_user_id=current_user.id,
                comment=archive_reason,
            )
            db.add(other_hist)
            try:
                from app.services.excel import get_excel_service
                get_excel_service().update_referral_status(
                    referral_id=other_ref.id,
                    referral_number=other_ref.referral_number,
                    new_status=ReferralStatus.ARCHIVED.value,
                    comment=archive_reason,
                    changed_by=current_user.name,
                )
            except Exception as other_err:
                logger.warning(f"Failed to write archived status to Excel for referral {other_ref.id}: {other_err}")

    db.commit()
    db.refresh(referral)

    # Write-through to Microsoft Excel
    try:
        from app.services.excel import get_excel_service
        excel_svc = get_excel_service()
        excel_svc.update_referral_status(
            referral_id=referral.id,
            referral_number=referral.referral_number,
            new_status=new_status,
            comment=comment,
            changed_by=current_user.name,
        )
        if new_status == ReferralStatus.HIRED.value:
            pos = referral.position
            excel_svc.save_hired_record({
                "id": referral.id,
                "referral_number": referral.referral_number,
                "candidate_name": referral.candidate_name,
                "candidate_email": referral.candidate_email,
                "position_id": referral.position_id,
                "position_title": pos.title if pos else "Unknown Position",
                "department": pos.department if pos else "General",
                "location": pos.location if pos else "Tangentia Office",
                "employment_type": pos.employment_type if pos else "Full-time",
                "referred_by_name": referral.referred_by_name or (referral.referred_by.name if referral.referred_by else "Employee"),
                "hired_at": referral.updated_at or referral.created_at,
                "status": "Hired",
            })
    except Exception as excel_err:
        logger.warning(f"Excel status update write-through failed: {excel_err}")

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

    # Write-through to Microsoft Excel
    try:
        from app.services.excel import get_excel_service
        get_excel_service().update_referral_status(
            referral_id=referral.id,
            referral_number=referral.referral_number,
            new_status=ReferralStatus.WITHDRAWN.value,
            comment=comment or f"Referral withdrawn by {current_user.name}.",
            changed_by=current_user.name,
        )
    except Exception as excel_err:
        logger.warning(f"Excel withdrawal write-through failed: {excel_err}")

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

    # Write-through to Microsoft Excel
    try:
        from app.services.excel import get_excel_service
        get_excel_service().append_hr_note(
            referral_id=referral.id,
            referral_number=referral.referral_number,
            note=note_text.strip(),
            created_by=current_user.name,
        )
    except Exception as excel_err:
        logger.warning(f"Excel HR note write-through failed: {excel_err}")

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

    if current_user.role != UserRole.HR_ADMIN.value and not settings.DEV_MODE and referral.referred_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this candidate's CV.",
        )

    file_bytes, filename, content_type = await sharepoint_service.download_cv(
        drive_id=referral.sharepoint_drive_id,
        item_id=referral.sharepoint_item_id,
        referral_number=referral.referral_number,
        stored_filename=referral.stored_filename,
        original_filename=referral.original_filename,
        candidate_name=referral.candidate_name,
    )
    return file_bytes, referral.original_filename or filename, content_type

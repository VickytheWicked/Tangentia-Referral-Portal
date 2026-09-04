import json
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Response
from fastapi.responses import StreamingResponse
import io
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.referral import Referral
from app.models.user import User, UserRole
from app.schemas.referral import (
    ReferralCreateForm,
    ReferralSummaryResponse,
    ReferralDetailResponse,
    ReferralWithdrawRequest,
)
from app.schemas.duplicate import DuplicateCheckRequest, DuplicateCheckResponse
from app.schemas.status_history import StatusHistoryResponse
from app.api.deps import get_current_user
from app.services.sharepoint import get_sharepoint_service
from app.services.referral_service import (
    check_duplicate_candidate,
    create_referral_with_cv,
    withdraw_referral,
    get_referral_cv_bytes,
)

router = APIRouter(prefix="/referrals", tags=["Referrals"])


def format_referral_summary(ref: Referral) -> ReferralSummaryResponse:
    return ReferralSummaryResponse(
        id=ref.id,
        referral_number=ref.referral_number,
        candidate_name=ref.candidate_name,
        candidate_email=ref.candidate_email,
        candidate_phone=ref.candidate_phone,
        years_of_experience=ref.years_of_experience,
        relationship=ref.relationship,
        status=ref.status,
        position_id=ref.position_id,
        position_title=ref.position.title if ref.position else "N/A",
        position_department=ref.position.department if ref.position else "N/A",
        referred_by_id=ref.referred_by_user_id,
        referred_by_name=ref.referred_by.name if ref.referred_by else "N/A",
        referred_by_email=ref.referred_by.email if ref.referred_by else "N/A",
        original_filename=ref.original_filename,
        created_at=ref.created_at,
        updated_at=ref.updated_at,
    )


@router.post("/check-duplicate", response_model=DuplicateCheckResponse)
async def api_check_duplicate(
    payload: DuplicateCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check if candidate matches an existing referral by email, phone, or name + position.
    """
    return check_duplicate_candidate(
        db=db,
        candidate_email=payload.candidate_email,
        candidate_phone=payload.candidate_phone,
        candidate_name=payload.candidate_name,
        position_id=payload.position_id,
    )


@router.post("", response_model=ReferralSummaryResponse, status_code=status.HTTP_201_CREATED)
async def submit_referral(
    candidate_name: str = Form(...),
    candidate_email: str = Form(...),
    candidate_phone: str = Form(...),
    linkedin_url: Optional[str] = Form(None),
    github_url: Optional[str] = Form(None),
    years_of_experience: float = Form(0.0),
    relationship: str = Form(...),
    referral_note: str = Form(...),
    position_id: str = Form(...),
    candidate_consent: bool = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a candidate referral with CV file.
    CV is uploaded to SharePoint document library via Microsoft Graph API.
    Metadata is saved to PostgreSQL.
    """
    form_data = ReferralCreateForm(
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        candidate_phone=candidate_phone,
        linkedin_url=linkedin_url,
        github_url=github_url,
        years_of_experience=years_of_experience,
        relationship=relationship,
        referral_note=referral_note,
        position_id=position_id,
        candidate_consent=candidate_consent,
    )

    sharepoint_svc = get_sharepoint_service()
    referral = await create_referral_with_cv(
        db=db,
        form_data=form_data,
        file=file,
        current_user=current_user,
        sharepoint_service=sharepoint_svc,
    )

    return format_referral_summary(referral)


@router.get("", response_model=List[ReferralSummaryResponse])
async def list_my_referrals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all referrals submitted by the authenticated employee.
    Employees can NEVER view referrals submitted by other users.
    """
    referrals = (
        db.query(Referral)
        .filter(Referral.referred_by_user_id == current_user.id)
        .order_by(Referral.created_at.desc())
        .all()
    )
    return [format_referral_summary(r) for r in referrals]


@router.get("/{referral_id}", response_model=ReferralDetailResponse)
async def get_referral_detail(
    referral_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed referral information.
    Restricted to the referring employee or HR Admins.
    HR Notes are stripped for regular employees.
    """
    ref = db.query(Referral).filter(Referral.id == referral_id).first()
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found.")

    is_hr = current_user.role == UserRole.HR_ADMIN.value
    if not is_hr and ref.referred_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this referral.",
        )

    summary = format_referral_summary(ref)
    
    # Map status history
    history_responses = [
        StatusHistoryResponse(
            id=h.id,
            referral_id=h.referral_id,
            old_status=h.old_status,
            new_status=h.new_status,
            changed_by_user_id=h.changed_by_user_id,
            changed_by_name=h.changed_by.name if h.changed_by else "System",
            comment=h.comment,
            created_at=h.created_at,
        )
        for h in ref.status_history
    ]

    # HR Notes: ONLY visible to HR Admins
    hr_notes_responses = []
    if is_hr:
        hr_notes_responses = [
            {
                "id": n.id,
                "referral_id": n.referral_id,
                "created_by_user_id": n.created_by_user_id,
                "created_by_name": n.created_by.name if n.created_by else "HR Team",
                "note": n.note,
                "created_at": n.created_at,
                "updated_at": n.updated_at,
            }
            for n in ref.hr_notes
        ]

    return ReferralDetailResponse(
        **summary.model_dump(),
        linkedin_url=ref.linkedin_url,
        github_url=ref.github_url,
        referral_note=ref.referral_note,
        candidate_consent=ref.candidate_consent,
        position=ref.position,
        status_history=history_responses,
        hr_notes=hr_notes_responses,
    )


@router.put("/{referral_id}/withdraw", response_model=ReferralSummaryResponse)
async def api_withdraw_referral(
    referral_id: str,
    payload: Optional[ReferralWithdrawRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Allow employee to withdraw their referral if still under initial status.
    """
    comment = payload.comment if payload else None
    ref = withdraw_referral(db, referral_id, current_user, comment=comment)
    return format_referral_summary(ref)


@router.get("/{referral_id}/cv")
async def download_cv_file(
    referral_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Securely stream candidate CV from SharePoint.
    Only authorized for HR Admin or the referring employee.
    Does not expose Microsoft Graph credentials or tokens to the frontend.
    """
    sharepoint_svc = get_sharepoint_service()
    content_bytes, filename, content_type = await get_referral_cv_bytes(
        db=db,
        referral_id=referral_id,
        current_user=current_user,
        sharepoint_service=sharepoint_svc,
    )

    return StreamingResponse(
        io.BytesIO(content_bytes),
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )


@router.get("/{referral_id}/status-history", response_model=List[StatusHistoryResponse])
async def get_referral_history(
    referral_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get audit trail of referral status transitions"""
    ref = db.query(Referral).filter(Referral.id == referral_id).first()
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found.")

    if current_user.role != UserRole.HR_ADMIN.value and ref.referred_by_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return [
        StatusHistoryResponse(
            id=h.id,
            referral_id=h.referral_id,
            old_status=h.old_status,
            new_status=h.new_status,
            changed_by_user_id=h.changed_by_user_id,
            changed_by_name=h.changed_by.name if h.changed_by else "System",
            comment=h.comment,
            created_at=h.created_at,
        )
        for h in ref.status_history
    ]

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models.referral import Referral, ReferralStatus
from app.models.job_position import JobPosition
from app.models.user import User, UserRole
from app.schemas.referral import (
    ReferralSummaryResponse,
    ReferralStatusUpdate,
)
from app.schemas.hr_note import HRNoteCreate, HRNoteResponse
from app.cv_intelligence.database import get_cv_db
from app.cv_intelligence.service import CVIntelligenceService
from app.api.deps import require_hr_admin
from app.api.referrals import format_referral_summary
from app.services.referral_service import update_referral_status, add_hr_note

router = APIRouter(prefix="/hr/referrals", tags=["HR Referral Administration"])


@router.get("", response_model=List[ReferralSummaryResponse])
async def list_all_referrals(
    status_filter: Optional[str] = Query(None, alias="status"),
    position_id: Optional[str] = Query(None, alias="position_id"),
    department: Optional[str] = Query(None, alias="department"),
    referrer_id: Optional[str] = Query(None, alias="referrer_id"),
    search: Optional[str] = Query(None, alias="search"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    hr_user: User = Depends(require_hr_admin),
):
    """
    Search and filter all referrals across the enterprise.
    Restricted strictly to HR Admins.
    """
    query = db.query(Referral).outerjoin(Referral.position).outerjoin(Referral.referred_by)

    if status_filter:
        query = query.filter(Referral.status == status_filter)

    if position_id:
        query = query.filter(Referral.position_id == position_id)

    if department:
        query = query.filter(JobPosition.department == department)

    if referrer_id:
        query = query.filter(Referral.referred_by_user_id == referrer_id)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Referral.referral_number.ilike(term),
                Referral.candidate_name.ilike(term),
                Referral.candidate_email.ilike(term),
                Referral.candidate_phone.ilike(term),
                Referral.referred_by_name.ilike(term),
                User.name.ilike(term),
                JobPosition.title.ilike(term),
            )
        )

    referrals = query.order_by(Referral.created_at.desc()).offset(offset).limit(limit).all()
    return [format_referral_summary(r) for r in referrals]


@router.put("/{referral_id}/status", response_model=ReferralSummaryResponse)
async def api_update_status(
    referral_id: str,
    payload: ReferralStatusUpdate,
    db: Session = Depends(get_db),
    hr_user: User = Depends(require_hr_admin),
):
    """Change candidate referral status and log audit trail entry (HR Admin only)"""
    ref = update_referral_status(
        db=db,
        referral_id=referral_id,
        new_status=payload.status,
        comment=payload.comment,
        current_user=hr_user,
    )
    return format_referral_summary(ref)


@router.put("/{referral_id}/archive", response_model=ReferralSummaryResponse)
async def api_archive_referral(
    referral_id: str,
    comment: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    hr_user: User = Depends(require_hr_admin),
):
    """
    Archive a candidate referral record as historical documentation.
    Can be applied from any status (including Rejected or Withdrawn).
    """
    ref = update_referral_status(
        db=db,
        referral_id=referral_id,
        new_status=ReferralStatus.ARCHIVED.value,
        comment=comment or f"Referral archived by {hr_user.name}.",
        current_user=hr_user,
    )
    return format_referral_summary(ref)


@router.delete("/{referral_id}", status_code=status.HTTP_200_OK)
async def api_delete_referral(
    referral_id: str,
    db: Session = Depends(get_db),
    cv_db: Session = Depends(get_cv_db),
    hr_user: User = Depends(require_hr_admin),
):
    """
    Permanently delete candidate referral and its audit trail, HR notes, and Excel records.
    Restricted strictly to HR Admins.
    """
    ref = db.query(Referral).filter(Referral.id == referral_id).first()
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found.")

    ref_num = ref.referral_number
    cand_name = ref.candidate_name
    sp_drive_id = ref.sharepoint_drive_id
    sp_item_id = ref.sharepoint_item_id

    # Delete associated CV Intelligence data (candidate profile, job matches, and blob sync)
    try:
        CVIntelligenceService.delete_referral_cv_data(cv_db=cv_db, referral_id=referral_id)
    except Exception as cv_err:
        logger.warning(f"Failed to delete CV intelligence data for referral {referral_id}: {cv_err}")

    # Delete CV file from storage (SharePoint / Azure Blob / local) if applicable
    try:
        if sp_drive_id and sp_item_id:
            from app.services.sharepoint import get_sharepoint_service
            sp_service = get_sharepoint_service()
            await sp_service.delete_cv(
                drive_id=sp_drive_id,
                item_id=sp_item_id,
            )
    except Exception as sp_err:
        logger.warning(f"Failed to delete CV file for referral {referral_id} from storage: {sp_err}")

    # Delete from database (cascades to status_history and hr_notes)
    db.delete(ref)
    db.commit()

    # Delete from Microsoft Excel
    try:
        from app.services.excel import get_excel_service
        get_excel_service().delete_referral(referral_id)
    except Exception as e:
        logger.warning(f"Failed to delete referral {referral_id} from Microsoft Excel storage: {e}")

    return {
        "message": f"Referral {ref_num} for {cand_name} has been permanently deleted.",
        "id": referral_id,
    }


@router.post("/{referral_id}/notes", response_model=HRNoteResponse, status_code=status.HTTP_201_CREATED)
async def api_create_hr_note(
    referral_id: str,
    payload: HRNoteCreate,
    db: Session = Depends(get_db),
    hr_user: User = Depends(require_hr_admin),
):
    """Add confidential internal HR note to a candidate referral (HR Admin only)"""
    note = add_hr_note(
        db=db,
        referral_id=referral_id,
        note_text=payload.note,
        current_user=hr_user,
    )
    return HRNoteResponse(
        id=note.id,
        referral_id=note.referral_id,
        created_by_user_id=note.created_by_user_id,
        created_by_name=hr_user.name,
        note=note.note,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


@router.get("/{referral_id}/notes", response_model=List[HRNoteResponse])
async def api_get_hr_notes(
    referral_id: str,
    db: Session = Depends(get_db),
    hr_user: User = Depends(require_hr_admin),
):
    """List internal HR notes for candidate referral (HR Admin only)"""
    ref = db.query(Referral).filter(Referral.id == referral_id).first()
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found.")

    return [
        HRNoteResponse(
            id=n.id,
            referral_id=n.referral_id,
            created_by_user_id=n.created_by_user_id,
            created_by_name=n.created_by.name if n.created_by else "HR Admin",
            note=n.note,
            created_at=n.created_at,
            updated_at=n.updated_at,
        )
        for n in ref.hr_notes
    ]


@router.get("/excel-export")
async def export_excel_workbook(
    hr_user: User = Depends(require_hr_admin),
):
    """Download the current live Microsoft Excel workbook (HR Admin only)"""
    from app.services.excel import get_excel_service
    excel_svc = get_excel_service()
    content = excel_svc.get_workbook_bytes()
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Excel workbook not found.")

    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="Tangentia_Referrals.xlsx"'},
    )

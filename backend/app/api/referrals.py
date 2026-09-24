import io
import json
import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

logger = logging.getLogger("referral_portal.referrals")

from app.config import settings
from app.database import get_db
from app.models.referral import Referral, ReferralStatus
from app.models.user import User, UserRole
from app.schemas.referral import (
    ReferralCreateForm,
    ReferralSummaryResponse,
    ReferralDetailResponse,
    ReferralWithdrawRequest,
    HiredHistoryResponse,
    CVExtractionPreviewResponse,
)
from app.schemas.duplicate import DuplicateCheckRequest, DuplicateCheckResponse
from app.schemas.status_history import StatusHistoryResponse
from app.api.deps import get_current_user, get_current_user_optional
from app.services.sharepoint import get_sharepoint_service
from app.services.referral_service import (
    check_duplicate_candidate,
    create_referral_with_cv,
    withdraw_referral,
    get_referral_cv_bytes,
)

router = APIRouter(prefix="/referrals", tags=["Referrals"])


def get_or_create_employee_user(
    db: Session,
    referred_by_name: Optional[str] = None,
    referred_by_email: Optional[str] = None,
) -> User:
    clean_email = (referred_by_email or "").strip().lower()
    clean_name = (referred_by_name or "").strip()

    if clean_email:
        if not clean_email.endswith("@tangentia.com"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee email must be an official @tangentia.com corporate email address.",
            )
        emp = db.query(User).filter(User.email == clean_email).first()
        if emp:
            if clean_name and (not emp.name or emp.name in ["Tangentia Employee", "Vansh Rupesh (Employee)"]):
                emp.name = clean_name
                db.commit()
            return emp

        # Create a new persistent user for this referring employee
        new_emp = User(
            id=f"user-emp-{uuid.uuid4().hex[:8]}",
            entra_user_id=f"emp-{uuid.uuid4().hex[:8]}",
            name=clean_name or "Tangentia Employee",
            email=clean_email,
            password="",
            role=UserRole.EMPLOYEE.value,
            department="General",
        )
        db.add(new_emp)
        db.commit()
        db.refresh(new_emp)

        # Write through to Excel Users worksheet
        try:
            from app.services.excel import get_excel_service
            get_excel_service().save_user({
                "id": new_emp.id,
                "name": new_emp.name,
                "email": new_emp.email,
                "password": "",
                "role": new_emp.role,
                "department": new_emp.department,
            })
        except Exception as e:
            logger.warning(f"Could not save referring employee {clean_email} to Excel Users: {e}")

        return new_emp

    # Fallback to default employee if no email provided
    emp = db.query(User).filter((User.id == "user-emp-001") | (User.email == "employee@tangentia.com")).first()
    if not emp:
        emp = User(
            id="user-emp-001",
            name=clean_name or "Tangentia Employee",
            email="employee@tangentia.com",
            role=UserRole.EMPLOYEE.value,
            department="Engineering",
        )
        db.add(emp)
        db.commit()
        db.refresh(emp)
    return emp


# Backward compatibility alias
get_or_create_default_employee = get_or_create_employee_user


def format_referral_summary(ref: Referral) -> ReferralSummaryResponse:
    referrer_name = ref.referred_by_name or (ref.referred_by.name if ref.referred_by else "N/A")
    referrer_email = ref.referred_by_email or (ref.referred_by.email if ref.referred_by else "N/A")
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
        referred_by_name=referrer_name,
        referred_by_email=referrer_email,
        referred_by_phone=ref.referred_by_phone,
        original_filename=ref.original_filename,
        created_at=ref.created_at,
        updated_at=ref.updated_at,
    )


@router.post("/check-duplicate", response_model=DuplicateCheckResponse)
async def api_check_duplicate(
    payload: DuplicateCheckRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Check if candidate matches an existing referral by email, phone, or name + position.
    Accessible to all employees without login.
    """
    return check_duplicate_candidate(
        db=db,
        candidate_email=payload.candidate_email,
        candidate_phone=payload.candidate_phone,
        candidate_name=payload.candidate_name,
        position_id=payload.position_id,
    )


@router.post("/extract-cv", response_model=CVExtractionPreviewResponse)
async def api_extract_cv_details(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Extract candidate information (name, email, phone, experience, linkedin, github)
    from an uploaded CV/resume file (PDF or DOCX) to autofill the referral form.
    Accessible to all employees submitting referrals.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No CV file uploaded.")

    ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""
    if ext not in ["pdf", "docx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{ext}'. Please upload a PDF (.pdf) or Word document (.docx).",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded CV file is empty (0 bytes).")
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CV file exceeds maximum allowable size of 10MB.")

    from app.cv_intelligence.text_extractor import extract_cv_text
    from app.cv_intelligence.extractor import get_cv_extractor, heuristic_cv_extract, is_valid_human_name

    try:
        cv_text = extract_cv_text(file_bytes=file_bytes, filename=file.filename, content_type=file.content_type)
    except Exception as e:
        logger.warning(f"Text extraction failed on uploaded CV: {e}")
        return CVExtractionPreviewResponse(
            success=False,
            found_fields=[],
            not_found_fields=["name", "email", "phone"],
            message=f"Could not read text from this file: {str(e)}",
        )

    try:
        extractor = get_cv_extractor()
        extracted = extractor.extract(cv_text)
    except Exception as ex:
        logger.info(f"Gemini CV extraction unavailable ({ex}), using heuristic parser.")
        extracted = heuristic_cv_extract(cv_text)

    # Sanity checks on name
    cand_name = extracted.candidate_name
    if cand_name and not is_valid_human_name(cand_name):
        cand_name = None

    # Track found vs not found fields
    found = []
    not_found = []

    if cand_name:
        found.append("name")
    else:
        not_found.append("name")

    if extracted.email:
        found.append("email")
    else:
        not_found.append("email")

    if extracted.phone:
        found.append("phone")
    else:
        not_found.append("phone")

    years_val = extracted.years_of_experience if extracted.years_of_experience and extracted.years_of_experience > 0 else None

    return CVExtractionPreviewResponse(
        success=True,
        candidate_name=cand_name,
        candidate_email=extracted.email,
        candidate_phone=extracted.phone,
        years_of_experience=years_val,
        linkedin_url=extracted.linkedin_url,
        github_url=extracted.github_url,
        skills=extracted.skills,
        found_fields=found,
        not_found_fields=not_found,
    )


@router.post("", response_model=ReferralSummaryResponse, status_code=status.HTTP_201_CREATED)
async def submit_referral(
    candidate_name: str = Form(...),
    candidate_email: str = Form(...),
    candidate_phone: str = Form(...),
    referred_by: Optional[str] = Form(None),
    referred_by_name: Optional[str] = Form(None),
    referred_by_email: Optional[str] = Form(None),
    employee_email: Optional[str] = Form(None),
    referred_by_phone: Optional[str] = Form(None),
    employee_phone: Optional[str] = Form(None),
    linkedin_url: Optional[str] = Form(None),
    github_url: Optional[str] = Form(None),
    years_of_experience: float = Form(0.0),
    relationship: str = Form(...),
    referral_note: str = Form(...),
    position_id: str = Form(...),
    candidate_consent: bool = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Submit a candidate referral with CV file without requiring employee login.
    Uses the submitted employee details (name, email, phone) as the referrer identity.
    Strictly enforces @tangentia.com for employee email.
    """
    ref_by_name = (referred_by_name or referred_by or "").strip() or None
    ref_by_email = (referred_by_email or employee_email or "").strip().lower() or None
    ref_by_phone = (referred_by_phone or employee_phone or "").strip() or None

    # Strictly enforce @tangentia.com for employee email
    effective_emp_email = ref_by_email or (current_user.email.strip().lower() if current_user and current_user.email else None) or "employee@tangentia.com"
    if not effective_emp_email.endswith("@tangentia.com"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee email must be an official @tangentia.com corporate email address.",
        )

    form_data = ReferralCreateForm(
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        candidate_phone=candidate_phone,
        referred_by_name=ref_by_name,
        referred_by_email=effective_emp_email,
        referred_by_phone=ref_by_phone,
        linkedin_url=linkedin_url,
        github_url=github_url,
        years_of_experience=years_of_experience,
        relationship=relationship,
        referral_note=referral_note,
        position_id=position_id,
        candidate_consent=candidate_consent,
    )

    effective_user = current_user or get_or_create_employee_user(
        db,
        referred_by_name=ref_by_name,
        referred_by_email=effective_emp_email,
    )
    sharepoint_svc = get_sharepoint_service()
    referral = await create_referral_with_cv(
        db=db,
        form_data=form_data,
        file=file,
        current_user=effective_user,
        sharepoint_service=sharepoint_svc,
    )

    return format_referral_summary(referral)


@router.get("", response_model=List[ReferralSummaryResponse])
async def list_my_referrals(
    referred_by: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    List referrals in employee workspace.
    Returns all submitted candidate referrals.
    """
    query = db.query(Referral).outerjoin(Referral.position).outerjoin(Referral.referred_by)
    if referred_by:
        query = query.filter(Referral.referred_by_name.ilike(f"%{referred_by.strip()}%"))
    referrals = query.order_by(Referral.created_at.desc()).all()
    return [format_referral_summary(r) for r in referrals]


@router.get("/hired-history", response_model=List[HiredHistoryResponse])
async def list_hired_history(
    position_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Get history of candidates hired for specific positions.
    Accessible to both HR and Employees.
    """
    query = db.query(Referral).outerjoin(Referral.position).filter(
        Referral.status == ReferralStatus.HIRED.value
    )
    if position_id:
        query = query.filter(Referral.position_id == position_id)

    hired_refs = query.order_by(Referral.updated_at.desc()).all()
    results = []
    for r in hired_refs:
        pos = r.position
        results.append(
            HiredHistoryResponse(
                id=r.id,
                referral_number=r.referral_number,
                candidate_name=r.candidate_name,
                position_id=r.position_id,
                position_title=pos.title if pos else "Unknown Position",
                department=pos.department if pos else "General",
                location=pos.location if pos else "Tangentia Office",
                employment_type=pos.employment_type if pos else "Full-time",
                referred_by_name=r.referred_by_name or (r.referred_by.name if r.referred_by else "Employee"),
                hired_at=r.updated_at or r.created_at,
                status="Hired",
            )
        )
    return results


@router.get("/hired-history/excel-export")
async def export_hired_history_excel(
    position_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Download standalone Microsoft Excel (.xlsx) workbook containing Hired Referral History.
    Accessible to both HR and Employees.
    """
    query = db.query(Referral).outerjoin(Referral.position).filter(
        Referral.status == ReferralStatus.HIRED.value
    )
    if position_id:
        query = query.filter(Referral.position_id == position_id)

    hired_refs = query.order_by(Referral.updated_at.desc()).all()

    from app.services.excel.local_excel_service import generate_hired_history_workbook_bytes

    content = generate_hired_history_workbook_bytes(hired_refs)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="Tangentia_Hired_History.xlsx"'},
    )


@router.get("/{referral_id}", response_model=ReferralDetailResponse)

async def get_referral_detail(
    referral_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Get detailed referral information.
    HR Notes are stripped for non-HR users.
    """
    ref = db.query(Referral).filter(Referral.id == referral_id).first()
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found.")

    is_hr = current_user is not None and current_user.role == UserRole.HR_ADMIN.value

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
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Allow employee to withdraw their referral if still under initial status.
    """
    effective_user = current_user or get_or_create_default_employee(db)
    comment = payload.comment if payload else None
    ref = withdraw_referral(db, referral_id, effective_user, comment=comment)
    return format_referral_summary(ref)


@router.get("/{referral_id}/cv")
async def download_cv_file(
    referral_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Securely stream candidate CV.
    """
    effective_user = current_user or get_or_create_default_employee(db)
    sharepoint_svc = get_sharepoint_service()
    content_bytes, filename, content_type = await get_referral_cv_bytes(
        db=db,
        referral_id=referral_id,
        current_user=effective_user,
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
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get audit trail of referral status transitions"""
    ref = db.query(Referral).filter(Referral.id == referral_id).first()
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found.")

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

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job_position import JobPosition
from app.models.user import User
from app.schemas.job_position import JobPositionCreate, JobPositionUpdate, JobPositionResponse
from app.api.deps import get_current_user, require_hr_admin

router = APIRouter(prefix="/jobs", tags=["Job Openings"])


@router.get("", response_model=List[JobPositionResponse])
async def list_job_positions(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List job positions.
    Employees see only active jobs; HR can view inactive/archived jobs as well.
    """
    query = db.query(JobPosition)
    if not include_inactive or current_user.role != "hr_admin":
        query = query.filter(JobPosition.is_active == True)
    
    return query.order_by(JobPosition.created_at.desc()).all()


@router.get("/{job_id}", response_model=JobPositionResponse)
async def get_job_position(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(JobPosition).filter(JobPosition.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job position not found.")
    return job


@router.post("", response_model=JobPositionResponse, status_code=status.HTTP_201_CREATED)
async def create_job_position(
    payload: JobPositionCreate,
    db: Session = Depends(get_db),
    hr_user: User = Depends(require_hr_admin),
):
    """Create a new job opening (HR Admin only)"""
    job = JobPosition(
        title=payload.title.strip(),
        department=payload.department.strip(),
        description=payload.description.strip(),
        location=payload.location.strip(),
        employment_type=payload.employment_type.strip(),
        is_active=payload.is_active,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        from app.services.excel import get_excel_service
        get_excel_service().save_job_position({
            "id": job.id,
            "title": job.title,
            "department": job.department,
            "location": job.location,
            "employment_type": job.employment_type,
            "is_active": job.is_active,
            "description": job.description,
            "created_at": job.created_at.strftime("%Y-%m-%d %H:%M:%S") if job.created_at else "",
        })
    except Exception as e:
        logger.warning(f"Excel job sync failed: {e}")

    return job


@router.put("/{job_id}", response_model=JobPositionResponse)
async def update_job_position(
    job_id: str,
    payload: JobPositionUpdate,
    db: Session = Depends(get_db),
    hr_user: User = Depends(require_hr_admin),
):
    """Update job opening details or toggle active status (HR Admin only)"""
    job = db.query(JobPosition).filter(JobPosition.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job position not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(job, key, value.strip() if isinstance(value, str) else value)

    db.commit()
    db.refresh(job)

    try:
        from app.services.excel import get_excel_service
        get_excel_service().save_job_position({
            "id": job.id,
            "title": job.title,
            "department": job.department,
            "location": job.location,
            "employment_type": job.employment_type,
            "is_active": job.is_active,
            "description": job.description,
            "created_at": job.created_at.strftime("%Y-%m-%d %H:%M:%S") if job.created_at else "",
        })
    except Exception as e:
        logger.warning(f"Excel job sync failed: {e}")

    return job

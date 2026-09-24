import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.referral import Referral
from app.api.deps import require_hr_admin
from app.cv_intelligence.database import get_cv_db
from app.cv_intelligence.service import CVIntelligenceService
from app.cv_intelligence.schemas import (
    OpeningSuggestionsResponse,
    CandidateProfileDetailResponse,
)

logger = logging.getLogger("cv_intelligence")

router = APIRouter(prefix="/cv-intelligence", tags=["CV Intelligence & HR Suggestions"])


def verify_feature_enabled():
    """Ensure CV Intelligence feature flag is active."""
    if not settings.CV_INTELLIGENCE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV Intelligence feature is currently disabled on this instance.",
        )


@router.get("/status")
async def get_feature_status():
    """
    Public health/status check for CV Intelligence feature.
    Does NOT leak API key or sensitive data.
    """
    return {
        "enabled": settings.CV_INTELLIGENCE_ENABLED,
        "provider": settings.CV_LLM_PROVIDER,
        "model": settings.CV_LLM_MODEL,
        "has_api_key": bool(settings.GEMINI_API_KEY),
    }


@router.get("/suggestions", response_model=List[OpeningSuggestionsResponse])
async def get_hr_suggestions(
    db: Session = Depends(get_db),
    cv_db: Session = Depends(get_cv_db),
    hr_user: User = Depends(require_hr_admin),
):
    """
    Retrieve explainable candidate match suggestions organized around active job openings.
    Accessible strictly to HR Admins.
    """
    verify_feature_enabled()
    return CVIntelligenceService.get_suggestions_by_openings(db, cv_db)


@router.get("/candidates/{referral_id}", response_model=CandidateProfileDetailResponse)
async def get_candidate_intelligence_detail(
    referral_id: str,
    db: Session = Depends(get_db),
    cv_db: Session = Depends(get_cv_db),
    hr_user: User = Depends(require_hr_admin),
):
    """
    Retrieve full structured candidate profile, explainable match breakdown, and CV reference.
    Strictly for HR Admins.
    """
    verify_feature_enabled()
    try:
        return CVIntelligenceService.get_candidate_profile_detail(db, cv_db, referral_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


@router.post("/process/{referral_id}", response_model=CandidateProfileDetailResponse)
async def process_single_candidate_cv(
    referral_id: str,
    force: bool = False,
    db: Session = Depends(get_db),
    cv_db: Session = Depends(get_cv_db),
    hr_user: User = Depends(require_hr_admin),
):
    """
    Extract structured candidate profile from original CV using Gemini 3.5 Flash,
    evaluate job match against target opening, and persist derived intelligence in cv_intelligence.db.
    """
    verify_feature_enabled()
    try:
        await CVIntelligenceService.process_referral_cv(
            db=db,
            cv_db=cv_db,
            referral_id=referral_id,
            force_reprocess=force,
        )
        return CVIntelligenceService.get_candidate_profile_detail(db, cv_db, referral_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.error(f"Error processing CV for referral {referral_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CV extraction encountered an error: {str(e)}",
        )


@router.post("/process-opening/{position_id}")
async def process_all_candidates_for_opening(
    position_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    cv_db: Session = Depends(get_cv_db),
    hr_user: User = Depends(require_hr_admin),
):
    """
    Process all pending candidate CVs for a specified job opening.
    Executes in background to prevent request timeouts.
    """
    verify_feature_enabled()
    referrals = db.query(Referral).filter(Referral.position_id == position_id).all()
    if not referrals:
        return {"processed": 0, "message": "No referrals found for this position."}

    ref_ids = [r.id for r in referrals]

    async def _batch_process(ids: List[str]):
        from app.database import SessionLocal
        from app.cv_intelligence.database import CVSessionLocal

        b_db = SessionLocal()
        b_cv_db = CVSessionLocal()
        try:
            for rid in ids:
                try:
                    await CVIntelligenceService.process_referral_cv(b_db, b_cv_db, rid)
                except Exception as ex:
                    logger.warning(f"Batch processing failed for referral {rid}: {ex}")
        finally:
            b_db.close()
            b_cv_db.close()

    background_tasks.add_task(_batch_process, ref_ids)

    return {
        "status": "processing_started",
        "position_id": position_id,
        "candidate_count": len(ref_ids),
        "message": f"Queued {len(ref_ids)} candidate CV(s) for extraction.",
    }

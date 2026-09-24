import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.api.deps import require_hr_admin
from app.cv_intelligence.database import get_cv_db
from app.historical_suggestions.schemas import HistoricalSuggestionsResponse
from app.historical_suggestions.matcher import HistoricalMatcher

logger = logging.getLogger("historical_suggestions")

router = APIRouter(prefix="/historical-suggestions", tags=["Historical Referral Suggestions"])


def verify_historical_feature_enabled():
    """Ensure Historical Referral Search feature flag is active."""
    if not settings.HISTORICAL_REFERRAL_SEARCH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Historical Referral Suggestions feature is currently disabled.",
        )


@router.get("/status")
async def get_feature_status():
    """
    Status check for Historical Referral Suggestions feature.
    Does NOT leak secrets.
    """
    return {
        "enabled": settings.HISTORICAL_REFERRAL_SEARCH_ENABLED,
        "default_threshold": settings.HISTORICAL_MATCH_THRESHOLD,
    }


@router.get("/positions/{position_id}", response_model=HistoricalSuggestionsResponse)
async def get_historical_suggestions_for_position(
    position_id: str,
    threshold: Optional[float] = Query(None, description="Optional custom minimum relevance threshold (0.0 to 1.0)"),
    db: Session = Depends(get_db),
    cv_db: Session = Depends(get_cv_db),
    hr_user: User = Depends(require_hr_admin),
):
    """
    Retrieve relevant historical archived candidate suggestions for an active job position.
    Accessible strictly to authenticated HR Admins.
    """
    verify_historical_feature_enabled()
    try:
        return HistoricalMatcher.find_historical_suggestions(
            db=db,
            cv_db=cv_db,
            position_id=position_id,
            threshold=threshold,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.error(f"Error finding historical suggestions for position {position_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving historical candidate suggestions.",
        )

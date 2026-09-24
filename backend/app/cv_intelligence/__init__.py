"""
CV Intelligence & HR Suggestions Module
Isolated, additive module for structured candidate extraction and job match suggestions.
"""

from app.cv_intelligence.database import init_cv_db, get_cv_db
from app.cv_intelligence.models import CandidateProfile, JobMatch, ExtractionStatus

__all__ = [
    "init_cv_db",
    "get_cv_db",
    "CandidateProfile",
    "JobMatch",
    "ExtractionStatus",
]

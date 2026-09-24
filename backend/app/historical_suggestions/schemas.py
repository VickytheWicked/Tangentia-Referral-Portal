from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class HistoricalCandidateItem(BaseModel):
    """
    Structured representation of a historical archived candidate surfaced for HR review.
    Preserves all original referral provenance (position, referral number, referrer, dates).
    """
    referral_id: str
    referral_number: str
    candidate_name: str
    candidate_email: str
    candidate_phone: Optional[str] = None
    
    # Original Referral Provenance (MUST never be altered or attributed to current job)
    original_position_id: str
    original_position_title: str
    original_referral_date: Optional[str] = None
    referred_by_name: str
    original_status: str = "Archived"
    
    # Relevance & Matching Assessment
    relevance_category: str  # "Strong Relevance", "Good Relevance", "Potential Relevance"
    relevance_score: float   # 0.0 - 1.0 (used internally for ranking & thresholding)
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    experience_summary: str
    relevance_reasons: List[str] = Field(default_factory=list)  # Explainable bullets with ✓ and •
    fit_narrative: Optional[str] = None
    
    # Candidate profile data
    years_of_experience: float = 0.0
    skills: List[str] = Field(default_factory=list)
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[Dict[str, Any]] = Field(default_factory=list)
    
    # CV file access
    original_filename: str


class HistoricalSuggestionsResponse(BaseModel):
    """
    Response schema returning historical archived candidates relevant to an active job opening.
    """
    current_position_id: str
    current_position_title: str
    threshold_applied: float
    total_archived_evaluated: int
    total_relevant_found: int
    suggestions: List[HistoricalCandidateItem] = Field(default_factory=list)

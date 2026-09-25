import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.cv_intelligence.database import CVBase


class ExtractionStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MatchLevel(str, Enum):
    STRONG_MATCH = "Strong Match"
    GOOD_MATCH = "Good Match"
    POTENTIAL_MATCH = "Potential Match"


class CandidateProfile(CVBase):
    __tablename__ = "candidate_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    referral_id = Column(String(36), unique=True, index=True, nullable=False)
    
    # Candidate Personal Info
    candidate_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    
    # Professional Profile
    years_of_experience = Column(Float, default=0.0, nullable=False)
    skills = Column(JSON, default=list, nullable=False)
    education = Column(JSON, default=list, nullable=False)
    experience = Column(JSON, default=list, nullable=False)
    projects = Column(JSON, default=list, nullable=False)
    certifications = Column(JSON, default=list, nullable=False)
    
    # Extraction Lifecycle
    extraction_status = Column(String(50), default=ExtractionStatus.PENDING.value, nullable=False)
    extraction_error = Column(Text, nullable=True)
    extracted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships within cv_intelligence.db
    job_matches = relationship("JobMatch", back_populates="candidate_profile", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CandidateProfile {self.candidate_name} ({self.extraction_status}) for Referral {self.referral_id}>"


class JobMatch(CVBase):
    __tablename__ = "job_matches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_profile_id = Column(String(36), ForeignKey("candidate_profiles.id"), nullable=False, index=True)
    position_id = Column(String(36), index=True, nullable=False)
    
    # Matching categorization
    match_level = Column(String(50), nullable=False)  # Strong Match, Good Match, Potential Match
    matched_skills = Column(JSON, default=list, nullable=False)
    missing_skills = Column(JSON, default=list, nullable=False)
    experience_match = Column(String(255), nullable=True)
    explanation = Column(JSON, default=list, nullable=False)  # List of explainable bullets
    fit_summary = Column(Text, nullable=True)  # 1-2 sentence human-readable LLM fit narrative

    # Evidence-Based Requirement Analysis (new — additive only)
    # Stores serialised OverallAnalysis JSON from requirement_analyzer.py
    requirement_analysis = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships within cv_intelligence.db
    candidate_profile = relationship("CandidateProfile", back_populates="job_matches")

    def __repr__(self):
        return f"<JobMatch Profile={self.candidate_profile_id} Position={self.position_id} Level={self.match_level}>"

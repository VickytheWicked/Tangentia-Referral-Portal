import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship as orm_relationship
from app.database import Base


class ReferralStatus(str, Enum):
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    SHORTLISTED = "Shortlisted"
    INTERVIEW = "Interview"
    SELECTED = "Selected"
    HIRED = "Hired"
    REJECTED = "Rejected"
    WITHDRAWN = "Withdrawn"


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    referral_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # Candidate Information
    candidate_name = Column(String(255), nullable=False)
    candidate_email = Column(String(255), index=True, nullable=False)
    candidate_phone = Column(String(50), index=True, nullable=False)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    years_of_experience = Column(Float, default=0.0, nullable=False)
    relationship = Column(String(100), nullable=False)
    referral_note = Column(Text, nullable=False)

    # Job & Referrer
    position_id = Column(String(36), ForeignKey("job_positions.id"), nullable=False)
    referred_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Status
    status = Column(String(50), default=ReferralStatus.SUBMITTED.value, nullable=False)

    # SharePoint Metadata
    sharepoint_drive_id = Column(String(255), nullable=True)
    sharepoint_item_id = Column(String(255), nullable=True)
    sharepoint_file_id = Column(String(255), nullable=True)
    sharepoint_file_url = Column(String(1000), nullable=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)

    # Consent
    candidate_consent = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    position = orm_relationship("JobPosition", back_populates="referrals")
    referred_by = orm_relationship("User", back_populates="referrals", foreign_keys=[referred_by_user_id])
    status_history = orm_relationship("ReferralStatusHistory", back_populates="referral", cascade="all, delete-orphan", order_by="ReferralStatusHistory.created_at.desc()")
    hr_notes = orm_relationship("HRNote", back_populates="referral", cascade="all, delete-orphan", order_by="HRNote.created_at.desc()")

    def __repr__(self):
        return f"<Referral {self.referral_number} - {self.candidate_name} ({self.status})>"

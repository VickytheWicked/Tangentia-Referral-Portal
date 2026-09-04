from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.schemas.job_position import JobPositionResponse
from app.schemas.status_history import StatusHistoryResponse
from app.schemas.hr_note import HRNoteResponse


class ReferralCreateForm(BaseModel):
    candidate_name: str = Field(..., min_length=2, max_length=255)
    candidate_email: EmailStr
    candidate_phone: str = Field(..., min_length=7, max_length=50)
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    years_of_experience: float = Field(default=0.0, ge=0.0, le=50.0)
    relationship: str = Field(..., min_length=2, max_length=100)
    referral_note: str = Field(..., min_length=10, max_length=5000)
    position_id: str
    candidate_consent: bool = Field(..., description="Must be true")


class ReferralStatusUpdate(BaseModel):
    status: str
    comment: Optional[str] = Field(None, description="Optional note for status transition")


class ReferralWithdrawRequest(BaseModel):
    comment: Optional[str] = Field(None, description="Optional reason for withdrawal")


class ReferralSummaryResponse(BaseModel):
    id: str
    referral_number: str
    candidate_name: str
    candidate_email: str
    candidate_phone: str
    years_of_experience: float
    relationship: str
    status: str
    position_id: str
    position_title: Optional[str] = None
    position_department: Optional[str] = None
    referred_by_id: str
    referred_by_name: Optional[str] = None
    referred_by_email: Optional[str] = None
    original_filename: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReferralDetailResponse(ReferralSummaryResponse):
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    referral_note: str
    candidate_consent: bool
    position: Optional[JobPositionResponse] = None
    status_history: List[StatusHistoryResponse] = []
    hr_notes: List[HRNoteResponse] = []  # Only populated for HR Admins!

    model_config = ConfigDict(from_attributes=True)

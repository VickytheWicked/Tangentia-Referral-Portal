from typing import List, Optional
from pydantic import BaseModel, EmailStr


class DuplicateCheckRequest(BaseModel):
    candidate_email: EmailStr
    candidate_phone: str
    candidate_name: str
    position_id: str


class DuplicateMatch(BaseModel):
    referral_id: str
    referral_number: str
    candidate_name: str
    candidate_email: str
    position_title: str
    status: str
    referred_by_name: str
    created_at: str
    match_reason: str


class DuplicateCheckResponse(BaseModel):
    is_duplicate: bool
    matches: List[DuplicateMatch]

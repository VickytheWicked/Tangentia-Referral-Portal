from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class HRNoteCreate(BaseModel):
    note: str = Field(..., min_length=1, max_length=5000, description="Internal HR note content")


class HRNoteResponse(BaseModel):
    id: str
    referral_id: str
    created_by_user_id: str
    created_by_name: Optional[str] = None
    note: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class StatusHistoryResponse(BaseModel):
    id: str
    referral_id: str
    old_status: Optional[str] = None
    new_status: str
    changed_by_user_id: str
    changed_by_name: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

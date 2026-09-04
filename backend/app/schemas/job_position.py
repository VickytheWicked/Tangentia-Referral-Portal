from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class JobPositionBase(BaseModel):
    title: str
    department: str
    description: str
    location: str
    employment_type: str = "Full-time"
    is_active: bool = True


class JobPositionCreate(JobPositionBase):
    pass


class JobPositionUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    is_active: Optional[bool] = None


class JobPositionResponse(JobPositionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

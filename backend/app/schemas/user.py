from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str
    department: Optional[str] = None


class UserCreate(UserBase):
    entra_user_id: str


class UserResponse(UserBase):
    id: str
    entra_user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

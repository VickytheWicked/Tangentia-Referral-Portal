import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, Enum):
    EMPLOYEE = "employee"
    HR_ADMIN = "hr_admin"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entra_user_id = Column(String(100), unique=True, index=True, nullable=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=True)
    role = Column(String(50), default=UserRole.EMPLOYEE.value, nullable=False)
    department = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    referrals = relationship("Referral", back_populates="referred_by", foreign_keys="Referral.referred_by_user_id")
    status_changes = relationship("ReferralStatusHistory", back_populates="changed_by")
    notes = relationship("HRNote", back_populates="created_by")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

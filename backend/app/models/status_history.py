import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class ReferralStatusHistory(Base):
    __tablename__ = "referral_status_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    referral_id = Column(String(36), ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False)
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    referral = relationship("Referral", back_populates="status_history")
    changed_by = relationship("User", back_populates="status_changes")

    def __repr__(self):
        return f"<ReferralStatusHistory {self.old_status} -> {self.new_status}>"

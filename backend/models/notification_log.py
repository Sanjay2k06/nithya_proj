"""
Notification Log SQLAlchemy Model.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from backend.db.base import Base


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String(36), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=True, index=True)
    channel = Column(String(30), nullable=False)  # console, telegram, email
    status = Column(String(20), nullable=False)  # DELIVERED, FAILED
    recipient = Column(String(255), nullable=True)
    message = Column(Text, nullable=True)
    evidence_path = Column(String(255), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    attempted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    error_code = Column(String(255), nullable=True)

    alert = relationship("Alert", back_populates="notification_logs")

"""
Alert SQLAlchemy Model.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from backend.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String(36), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=True, index=True)
    detection_id = Column(String(36), ForeignKey("detections.id", ondelete="SET NULL"), nullable=True, index=True)
    alert_type = Column(String(20), nullable=False, index=True)  # fire, smoke
    severity = Column(String(20), default="CRITICAL", nullable=False)  # CRITICAL, WARNING, INFO
    status = Column(String(20), default="ACTIVE", nullable=False, index=True)  # ACTIVE, ACKNOWLEDGED, CLOSED
    first_seen_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    notification_status = Column(String(20), default="PENDING", nullable=False)  # PENDING, DELIVERED, FAILED
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    camera = relationship("Camera", back_populates="alerts")
    detection = relationship("Detection", back_populates="alerts")
    notification_logs = relationship("NotificationLog", back_populates="alert", cascade="all, delete-orphan")

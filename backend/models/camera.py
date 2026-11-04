"""
Camera SQLAlchemy Model.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime
from sqlalchemy.orm import relationship

from backend.db.base import Base


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    source_type = Column(String(20), nullable=False, default="webcam")  # webcam, ip_camera, video_file
    source_reference = Column(String(255), nullable=False, default="0")  # Device ID 0, RTSP URL, or file path
    location_label = Column(String(150), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    status = Column(String(20), default="IDLE", nullable=False)  # IDLE, STREAMING, ERROR, OFFLINE
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    detections = relationship("Detection", back_populates="camera", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="camera", cascade="all, delete-orphan")

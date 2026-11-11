"""
Detection SQLAlchemy Model.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from backend.db.base import Base


class Detection(Base):
    __tablename__ = "detections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String(36), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=True, index=True)
    source_id = Column(String(128), nullable=True, index=True)
    source_type = Column(String(30), default="stream", nullable=False)  # stream, image_upload, video_upload
    predicted_class = Column(String(20), nullable=False, index=True)  # fire, smoke, normal
    confidence = Column(Float, nullable=False, index=True)
    probabilities_json = Column(JSON, nullable=False)
    frame_timestamp = Column(Float, nullable=False)
    inference_ms = Column(Float, nullable=False)
    model_version = Column(String(50), default="1.0.0", nullable=False)
    image_path = Column(String(255), nullable=True)
    heatmap_path = Column(String(255), nullable=True)
    temporal_state = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    camera = relationship("Camera", back_populates="detections")
    alerts = relationship("Alert", back_populates="detection")

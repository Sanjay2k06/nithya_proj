"""Persisted registry and runtime status for configured demo sources."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, String

from backend.db.base import Base


class MonitoringSource(Base):
    __tablename__ = "monitoring_sources"

    id = Column(String(128), primary_key=True)
    name = Column(String(255), nullable=False)
    source_type = Column(String(64), nullable=False)
    video_filename = Column(String(255), nullable=False)
    source_status = Column(String(20), nullable=False, default="AVAILABLE")
    playback_status = Column(String(20), nullable=False, default="STOPPED")
    processing_status = Column(String(20), nullable=False, default="STOPPED")
    last_processed_at = Column(DateTime(timezone=True), nullable=True)
    last_processed_video_seconds = Column(Float, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

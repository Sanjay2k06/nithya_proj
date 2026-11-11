"""Persisted source-associated environmental sensor readings."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, String

from backend.db.base import Base


class EnvironmentalReading(Base):
    __tablename__ = "environmental_readings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(128), nullable=False, index=True)
    temperature_c = Column(Float, nullable=True)
    humidity_percent = Column(Float, nullable=True)
    wind_speed_mps = Column(Float, nullable=True)
    wind_direction_degrees = Column(Float, nullable=True)
    smoke_sensor_value = Column(Float, nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

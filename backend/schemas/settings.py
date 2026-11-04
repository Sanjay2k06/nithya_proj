"""
Operational Settings Schemas.
"""

from typing import Optional
from pydantic import BaseModel, Field


class OperationalSettingsSchema(BaseModel):
    fire_threshold: float = Field(default=0.75, ge=0.1, le=1.0)
    smoke_threshold: float = Field(default=0.70, ge=0.1, le=1.0)
    temporal_window: int = Field(default=5, ge=1, le=30)
    temporal_required_positives: int = Field(default=3, ge=1, le=30)
    alert_cooldown_seconds: int = Field(default=60, ge=5, le=3600)
    max_upload_mb: int = Field(default=25, ge=1, le=100)
    max_video_seconds: int = Field(default=120, ge=5, le=600)
    model_demo_mode: bool = False


class OperationalSettingsUpdate(BaseModel):
    fire_threshold: Optional[float] = Field(default=None, ge=0.1, le=1.0)
    smoke_threshold: Optional[float] = Field(default=None, ge=0.1, le=1.0)
    temporal_window: Optional[int] = Field(default=None, ge=1, le=30)
    temporal_required_positives: Optional[int] = Field(default=None, ge=1, le=30)
    alert_cooldown_seconds: Optional[int] = Field(default=None, ge=5, le=3600)
    max_upload_mb: Optional[int] = Field(default=None, ge=1, le=100)
    max_video_seconds: Optional[int] = Field(default=None, ge=5, le=600)
    model_demo_mode: Optional[bool] = None

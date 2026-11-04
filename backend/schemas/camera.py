"""
Camera Pydantic Schemas.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CameraBase(BaseModel):
    name: str = Field(..., max_length=100)
    source_type: str = Field(default="webcam", description="webcam, ip_camera, or video_file")
    source_reference: str = Field(default="0", description="Camera index or RTSP URL")
    location_label: Optional[str] = Field(default=None, max_length=150)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    enabled: bool = True


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    source_type: Optional[str] = None
    source_reference: Optional[str] = None
    location_label: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    enabled: Optional[bool] = None
    status: Optional[str] = None


class CameraResponse(CameraBase):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

"""Response contracts for simulated CCTV monitoring."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class DemoSourceResponse(BaseModel):
    source_id: str
    name: str
    description: str
    file_name: str
    available: bool
    video_url: str
    source_type: str
    source_status: str = "AVAILABLE"
    playback_status: str = "STOPPED"
    processing_status: str = "STOPPED"
    last_processed_at: Optional[datetime] = None
    last_processed_video_seconds: Optional[float] = None


class DemoMonitoringStatusResponse(BaseModel):
    selected_source: Optional[DemoSourceResponse] = None
    is_monitoring: bool
    is_processing: bool
    latest_detection: Optional[Dict[str, Any]] = None
    last_processed_video_seconds: Optional[float] = None
    processing_delay_ms: Optional[float] = None
    processed_frames: int
    status: str
    error: Optional[str] = None

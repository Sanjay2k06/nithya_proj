"""
Prediction Request & Response Schemas.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ImagePredictionResponse(BaseModel):
    detection_id: Optional[str] = None
    source_id: Optional[str] = None
    predicted_class: str
    confidence: Optional[float] = None
    probabilities: Dict[str, float] = Field(default_factory=dict)
    inference_ms: float
    model_version: str
    analysis_provider: str = "firenet"
    analysis_text: Optional[str] = None
    analysis_evidence: list[str] = Field(default_factory=list)
    analysis_caveat: Optional[str] = None
    original_image_url: Optional[str] = None
    heatmap_image_url: Optional[str] = None
    temporally_verified: bool
    alert_triggered: bool
    alert_id: Optional[str] = None
    notification_status: Optional[str] = None
    status_label: str
    demo_mode: bool = False
    temporal_state: Dict[str, Any] = Field(default_factory=dict)
    processing_duration_ms: Optional[float] = None
    processing_delay_ms: Optional[float] = None
    visual_motion: Optional[Dict[str, float]] = None


class VideoTaskResponse(BaseModel):
    task_id: str
    status: str  # processing, completed, failed
    filename: str
    error: Optional[str] = None
    analysis_provider: str = "firenet"
    analysis_summary: Optional[str] = None
    frame_results: list[Dict[str, Any]] = Field(default_factory=list)
    total_frames: Optional[int] = None
    processed_frames: Optional[int] = None
    detections_count: Optional[int] = None
    alerts_count: Optional[int] = None
    created_at: str

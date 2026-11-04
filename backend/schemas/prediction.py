"""
Prediction Request & Response Schemas.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ImagePredictionResponse(BaseModel):
    detection_id: Optional[str] = None
    predicted_class: str
    confidence: float
    probabilities: Dict[str, float]
    inference_ms: float
    model_version: str
    original_image_url: Optional[str] = None
    heatmap_image_url: Optional[str] = None
    temporally_verified: bool
    alert_triggered: bool
    alert_id: Optional[str] = None
    status_label: str
    demo_mode: bool = False


class VideoTaskResponse(BaseModel):
    task_id: str
    status: str  # processing, completed, failed
    filename: str
    total_frames: Optional[int] = None
    processed_frames: Optional[int] = None
    detections_count: Optional[int] = None
    alerts_count: Optional[int] = None
    created_at: str

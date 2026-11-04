"""
Detection Response and Filtering Schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class DetectionResponse(BaseModel):
    id: str
    camera_id: Optional[str] = None
    camera_name: Optional[str] = None
    source_type: str
    predicted_class: str
    confidence: float
    probabilities_json: Dict[str, float]
    frame_timestamp: float
    inference_ms: float
    model_version: str
    image_path: Optional[str] = None
    heatmap_path: Optional[str] = None
    temporal_state: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedDetectionsResponse(BaseModel):
    items: List[DetectionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

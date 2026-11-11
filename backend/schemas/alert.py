"""
Alert Schemas.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AlertResponse(BaseModel):
    id: str
    camera_id: Optional[str] = None
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    camera_name: Optional[str] = None
    detection_id: Optional[str] = None
    alert_type: str
    severity: str
    status: str
    first_seen_at: datetime
    last_seen_at: datetime
    acknowledged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    notification_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertStatusUpdate(BaseModel):
    status: str = Field(..., description="'ACKNOWLEDGED' or 'CLOSED'")


class PaginatedAlertsResponse(BaseModel):
    items: List[AlertResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

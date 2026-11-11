"""Notification API response schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: str
    alert_id: Optional[str] = None
    channel: str
    status: str
    recipient: Optional[str] = None
    message: Optional[str] = None
    evidence_path: Optional[str] = None
    retry_count: int
    attempted_at: datetime
    delivered_at: Optional[datetime] = None
    error_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationHistoryResponse(BaseModel):
    items: List[NotificationResponse]
    total: int


class TelegramStatusResponse(BaseModel):
    enabled: bool
    configured: bool
    connection_status: str
    recipient_hint: Optional[str] = None
    total_messages: int
    delivered_messages: int
    failed_messages: int
    last_notification_time: Optional[datetime] = None
    last_notification_message: Optional[str] = None
    last_incident_id: Optional[str] = None

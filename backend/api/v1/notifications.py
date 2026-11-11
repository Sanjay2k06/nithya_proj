"""Telegram delivery status, tests, history, and manual retries."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.db.session import get_db
from backend.models.notification_log import NotificationLog
from backend.schemas.notification import (
    NotificationHistoryResponse,
    NotificationResponse,
    TelegramStatusResponse,
)
from backend.services.notification_service import notification_service

router = APIRouter()


def _recipient_hint(chat_id: Optional[str]) -> Optional[str]:
    if not chat_id:
        return None
    return f"{'*' * max(4, len(chat_id) - 4)}{chat_id[-4:]}"


@router.get("/telegram/status", response_model=TelegramStatusResponse, summary="Telegram configuration and delivery status")
def get_telegram_status(db: Session = Depends(get_db)):
    telegram_logs = db.query(NotificationLog).filter(NotificationLog.channel == "telegram")
    total_messages = telegram_logs.count()
    delivered_messages = telegram_logs.filter(NotificationLog.status == "DELIVERED").count()
    failed_messages = telegram_logs.filter(NotificationLog.status == "FAILED").count()
    last_notification = telegram_logs.order_by(desc(NotificationLog.attempted_at)).first()
    last_test = telegram_logs.filter(NotificationLog.alert_id.is_(None)).order_by(
        desc(NotificationLog.attempted_at)
    ).first()

    configured = bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID)
    if not settings.TELEGRAM_ENABLED:
        connection_status = "disabled"
    elif not configured:
        connection_status = "unconfigured"
    elif last_test is None:
        connection_status = "not_tested"
    else:
        connection_status = "connected" if last_test.status == "DELIVERED" else "error"

    return TelegramStatusResponse(
        enabled=settings.TELEGRAM_ENABLED,
        configured=configured,
        connection_status=connection_status,
        recipient_hint=_recipient_hint(settings.TELEGRAM_CHAT_ID),
        total_messages=total_messages,
        delivered_messages=delivered_messages,
        failed_messages=failed_messages,
        last_notification_time=last_notification.attempted_at if last_notification else None,
        last_notification_message=last_notification.message[:240] if last_notification and last_notification.message else None,
        last_incident_id=last_notification.alert_id if last_notification else None,
    )


@router.post("/telegram/test", response_model=NotificationResponse, summary="Send a real Telegram test message")
def test_telegram_connection(db: Session = Depends(get_db)):
    try:
        notification = notification_service.test_telegram(db)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return notification


@router.get("", response_model=NotificationHistoryResponse, summary="List Telegram notification attempts")
def list_notifications(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(NotificationLog).filter(NotificationLog.channel == "telegram")
    total = query.count()
    items = query.order_by(desc(NotificationLog.attempted_at)).offset(offset).limit(limit).all()
    return NotificationHistoryResponse(items=items, total=total)


@router.post("/{notification_id}/retry", response_model=NotificationResponse, summary="Retry a failed Telegram notification")
def retry_notification(notification_id: str, db: Session = Depends(get_db)):
    notification = db.get(NotificationLog, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found.")
    try:
        return notification_service.retry(db, notification)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

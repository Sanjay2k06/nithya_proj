"""
Abstract Notification Service and Delivery Providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import smtplib
from email.mime.text import MIMEText
import httpx
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.logging import logger
from backend.models.notification_log import NotificationLog


class BaseNotificationProvider(ABC):
    @abstractmethod
    def send(self, alert_payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Sends notification. Returns (success, error_code)."""
        pass


class ConsoleNotificationProvider(BaseNotificationProvider):
    def send(self, alert_payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        logger.info(
            f"\n"
            f"============================================================\n"
            f"[ALERT NOTIFICATION DISPATCHED]\n"
            f"Alert ID:       {alert_payload.get('alert_id')}\n"
            f"Type:           {alert_payload.get('alert_type', '').upper()}\n"
            f"Severity:       {alert_payload.get('severity')}\n"
            f"Camera:         {alert_payload.get('camera_name', 'Unknown')}\n"
            f"Location:       {alert_payload.get('location_label', 'Configured Site')}\n"
            f"Confidence:     {alert_payload.get('confidence', 0.0):.2%}\n"
            f"Status:         Temporally Verified Incident\n"
            f"Timestamp:      {alert_payload.get('timestamp')}\n"
            f"============================================================"
        )
        return True, None


class TelegramNotificationProvider(BaseNotificationProvider):
    def send(self, alert_payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
        if not token or not chat_id:
            return False, "TELEGRAM_CREDENTIALS_MISSING"

        msg = (
            f"🚨 FOREST FIRE INCIDENT ALERT\n"
            f"Type: {alert_payload.get('alert_type', '').upper()}\n"
            f"Severity: {alert_payload.get('severity')}\n"
            f"Camera: {alert_payload.get('camera_name')}\n"
            f"Confidence: {alert_payload.get('confidence', 0.0):.2%}"
        )
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(url, json={"chat_id": chat_id, "text": msg})
                if res.status_code == 200:
                    return True, None
                return False, f"TELEGRAM_HTTP_{res.status_code}"
        except Exception as e:
            return False, f"TELEGRAM_ERROR_{str(e)[:50]}"


class NotificationService:
    def __init__(self):
        provider_name = settings.NOTIFICATION_PROVIDER.lower()
        if provider_name == "telegram" and settings.TELEGRAM_BOT_TOKEN:
            self.provider = TelegramNotificationProvider()
        else:
            self.provider = ConsoleNotificationProvider()

    def dispatch(self, db: Session, alert_id: str, alert_payload: Dict[str, Any]) -> bool:
        channel_name = settings.NOTIFICATION_PROVIDER.lower()
        now = datetime.now(timezone.utc)
        success, error_code = self.provider.send(alert_payload)

        log = NotificationLog(
            alert_id=alert_id,
            channel=channel_name,
            status="DELIVERED" if success else "FAILED",
            attempted_at=now,
            delivered_at=now if success else None,
            error_code=error_code
        )
        db.add(log)
        db.commit()
        return success


notification_service = NotificationService()

"""Notification providers and incident-based delivery tracking."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.logging import logger
from backend.models.alert import Alert
from backend.models.detection import Detection
from backend.models.notification_log import NotificationLog


class BaseNotificationProvider(ABC):
    @abstractmethod
    def send(self, alert_payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Send a notification and return its delivery result."""


class ConsoleNotificationProvider(BaseNotificationProvider):
    def send(self, alert_payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        logger.info(
            "[ALERT NOTIFICATION DISPATCHED] alert=%s type=%s source=%s confidence=%.2f%%",
            alert_payload.get("alert_id"),
            str(alert_payload.get("alert_type", "")).upper(),
            alert_payload.get("source_name", "Unknown"),
            float(alert_payload.get("confidence", 0.0)) * 100,
        )
        return True, None


class UnavailableNotificationProvider(BaseNotificationProvider):
    def __init__(self, channel: str):
        self.channel = channel

    def send(self, alert_payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        return False, f"{self.channel.upper()}_PROVIDER_UNAVAILABLE"


class TelegramNotificationProvider(BaseNotificationProvider):
    def build_message(self, alert_payload: Dict[str, Any]) -> str:
        alert_type = str(alert_payload.get("alert_type", "")).lower()
        is_fire = alert_type == "fire"
        title = "FOREST FIRE EMERGENCY ALERT" if is_fire else "FOREST SURVEILLANCE ALERT"
        status = "VERIFIED FIRE DETECTED" if is_fire else "SMOKE DETECTED"
        verification_frames = alert_payload.get("verification_frames")
        verification = (
            f"Verified across {verification_frames} frames"
            if verification_frames is not None
            else "Temporally verified"
        )
        confidence = float(alert_payload.get("confidence", 0.0))

        return (
            f"{title}\n\n"
            f"Status: {status}\n"
            f"Incident ID: {alert_payload.get('incident_id', alert_payload.get('alert_id', 'Unavailable'))}\n"
            f"Detection Source: {alert_payload.get('source_type', 'Monitoring source')}\n"
            f"Detection Time: {alert_payload.get('timestamp', 'Unavailable')}\n"
            f"Classification: {alert_type.upper() or 'UNKNOWN'}\n"
            f"Confidence: {confidence:.1%}\n"
            f"Temporal Verification: {verification}\n"
            f"Source: {alert_payload.get('source_name', 'Unknown source')}\n"
            f"System Status: {alert_payload.get('system_status', 'Monitoring')}\n\n"
            "Please investigate the reported incident."
        )

    def send(self, alert_payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        if not settings.TELEGRAM_ENABLED:
            return False, "TELEGRAM_DISABLED"

        token = settings.TELEGRAM_BOT_TOKEN
        chat_ids = []
        if settings.TELEGRAM_CHAT_ID:
            chat_ids.append(str(settings.TELEGRAM_CHAT_ID))
        active_chat_file = Path(settings.MEDIA_ROOT).parent / "active_telegram_chat.txt"
        if active_chat_file.is_file():
            try:
                for line in active_chat_file.read_text(encoding="utf-8").splitlines():
                    cid = line.strip()
                    if cid and cid not in chat_ids:
                        chat_ids.append(cid)
            except Exception:
                pass

        if not token or not chat_ids:
            return False, "TELEGRAM_CREDENTIALS_MISSING"

        message = str(alert_payload.get("message") or self.build_message(alert_payload))
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        evidence_path = self._evidence_file(alert_payload.get("evidence_path"))

        any_success = False
        last_error = None

        for chat_id in chat_ids:
            try:
                with httpx.Client(timeout=25.0) as client:
                    if evidence_path is not None:
                        photo_url = f"https://api.telegram.org/bot{token}/sendPhoto"
                        with evidence_path.open("rb") as photo:
                            response = client.post(
                                photo_url,
                                data={"chat_id": chat_id, "caption": message[:1024]},
                                files={"photo": (evidence_path.name, photo, "image/jpeg")},
                            )
                    else:
                        response = client.post(
                            url,
                            json={"chat_id": chat_id, "text": message},
                        )
            except (httpx.RequestError, OSError) as exc:
                logger.warning("Telegram delivery request failed for chat %s (%s).", chat_id, type(exc).__name__)
                last_error = "TELEGRAM_NETWORK_ERROR"
                continue

            try:
                result = response.json()
            except ValueError:
                last_error = f"TELEGRAM_INVALID_RESPONSE_HTTP_{response.status_code}"
                continue

            if not response.is_success:
                description = result.get("description") if isinstance(result, dict) else None
                error = str(description or f"HTTP {response.status_code}")[:200]
                last_error = f"TELEGRAM_HTTP_{response.status_code}: {error}"
                continue
            if not isinstance(result, dict) or result.get("ok") is not True:
                description = result.get("description") if isinstance(result, dict) else None
                error = str(description or "Telegram API rejected the message")[:200]
                last_error = f"TELEGRAM_API_REJECTED: {error}"
                continue

            any_success = True

        if any_success:
            return True, None
        return False, last_error or "TELEGRAM_DELIVERY_FAILED"

    @staticmethod
    def _evidence_file(evidence_path: Any) -> Optional[Path]:
        if not isinstance(evidence_path, str) or not evidence_path:
            return None

        filename = Path(evidence_path).name
        if not filename:
            return None
        candidate = Path(settings.MEDIA_ROOT) / "originals" / filename
        if candidate.is_file():
            return candidate
        candidate_heat = Path(settings.MEDIA_ROOT) / "heatmaps" / filename
        if candidate_heat.is_file():
            return candidate_heat
        return None


class NotificationService:
    @staticmethod
    def _provider() -> BaseNotificationProvider:
        if settings.TELEGRAM_ENABLED or settings.NOTIFICATION_PROVIDER.lower() == "telegram":
            return TelegramNotificationProvider()
        if settings.NOTIFICATION_PROVIDER.lower() == "console":
            return ConsoleNotificationProvider()
        return UnavailableNotificationProvider(settings.NOTIFICATION_PROVIDER.lower())

    @staticmethod
    def _channel() -> str:
        if settings.TELEGRAM_ENABLED or settings.NOTIFICATION_PROVIDER.lower() == "telegram":
            return "telegram"
        return settings.NOTIFICATION_PROVIDER.lower()

    @staticmethod
    def _write_log(
        db: Session,
        *,
        alert_id: Optional[str],
        channel: str,
        success: bool,
        error_code: Optional[str],
        message: str,
        evidence_path: Optional[str] = None,
        retry_count: int = 0,
    ) -> NotificationLog:
        attempted_at = datetime.now(timezone.utc)
        log = NotificationLog(
            alert_id=alert_id,
            channel=channel,
            status="DELIVERED" if success else "FAILED",
            recipient=settings.TELEGRAM_CHAT_ID if channel == "telegram" else None,
            message=message,
            evidence_path=evidence_path,
            retry_count=retry_count,
            attempted_at=attempted_at,
            delivered_at=attempted_at if success else None,
            error_code=error_code,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def dispatch(
        self,
        db: Session,
        alert_id: str,
        alert_payload: Dict[str, Any],
        retry_count: int = 0,
    ) -> bool:
        provider = self._provider()
        channel = self._channel()
        message = (
            TelegramNotificationProvider().build_message(alert_payload)
            if channel == "telegram"
            else (
                f"{str(alert_payload.get('alert_type', '')).upper()} incident "
                f"from {alert_payload.get('source_name', 'Unknown source')}"
            )
        )
        success, error_code = provider.send(alert_payload)
        self._write_log(
            db,
            alert_id=alert_id,
            channel=channel,
            success=success,
            error_code=error_code,
            message=message,
            evidence_path=alert_payload.get("evidence_path"),
            retry_count=retry_count,
        )
        return success

    def test_telegram(self, db: Session) -> NotificationLog:
        if not settings.TELEGRAM_ENABLED:
            raise ValueError("TELEGRAM_DISABLED")
        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
            raise ValueError("TELEGRAM_CREDENTIALS_MISSING")

        message = "ForestWatch AI Telegram connection test. Notifications are configured."
        success, error_code = TelegramNotificationProvider().send({"message": message})
        return self._write_log(
            db,
            alert_id=None,
            channel="telegram",
            success=success,
            error_code=error_code,
            message=message,
        )

    def retry(self, db: Session, notification: NotificationLog) -> NotificationLog:
        if notification.channel != "telegram":
            raise ValueError("TELEGRAM_RETRY_UNSUPPORTED_CHANNEL")
        if notification.status != "FAILED":
            raise ValueError("NOTIFICATION_NOT_FAILED")
        if not settings.TELEGRAM_ENABLED:
            raise ValueError("TELEGRAM_DISABLED")
        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
            raise ValueError("TELEGRAM_CREDENTIALS_MISSING")

        payload: Dict[str, Any] = {
            "message": notification.message or "ForestWatch AI incident notification retry.",
            "evidence_path": notification.evidence_path,
        }
        if notification.alert_id:
            alert = db.get(Alert, notification.alert_id)
            if alert and alert.detection_id:
                detection = db.get(Detection, alert.detection_id)
                if detection:
                    payload["evidence_path"] = detection.image_path

        success, error_code = TelegramNotificationProvider().send(payload)
        result = self._write_log(
            db,
            alert_id=notification.alert_id,
            channel="telegram",
            success=success,
            error_code=error_code,
            message=str(payload["message"]),
            evidence_path=payload.get("evidence_path"),
            retry_count=notification.retry_count + 1,
        )
        if notification.alert_id:
            alert = db.get(Alert, notification.alert_id)
            if alert:
                alert.notification_status = result.status
                db.commit()
                db.refresh(result)
        return result


notification_service = NotificationService()

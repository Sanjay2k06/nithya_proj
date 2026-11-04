"""
Alert Lifecycle and Incident Management Service.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.repositories.alerts import AlertRepository
from backend.repositories.cameras import CameraRepository
from backend.services.notification_service import notification_service
from backend.models.alert import Alert


class AlertService:

    @staticmethod
    def process_incident(
        db: Session,
        alert_type: str,
        camera_id: Optional[str],
        detection_id: Optional[str],
        confidence: float
    ) -> Alert:
        severity = "CRITICAL" if alert_type == "fire" else "WARNING"

        # Check for existing active alert for this camera
        existing_alert = None
        if camera_id:
            existing_alert = AlertRepository.get_active_for_camera(db, camera_id, alert_type)

        now = datetime.now(timezone.utc)
        if existing_alert:
            existing_alert.last_seen_at = now
            existing_alert.detection_id = detection_id
            db.commit()
            db.refresh(existing_alert)
            return existing_alert

        # Create new incident
        new_alert = AlertRepository.create(
            db=db,
            alert_type=alert_type,
            severity=severity,
            camera_id=camera_id,
            detection_id=detection_id
        )

        # Lookup camera metadata
        camera_name = "Upload Source"
        location_label = "Unassigned Location"
        if camera_id:
            cam = CameraRepository.get_by_id(db, camera_id)
            if cam:
                camera_name = cam.name
                location_label = cam.location_label or "Field Station"

        payload = {
            "alert_id": new_alert.id,
            "alert_type": alert_type,
            "severity": severity,
            "camera_name": camera_name,
            "location_label": location_label,
            "confidence": confidence,
            "timestamp": now.isoformat()
        }

        # Dispatch notification
        dispatched = notification_service.dispatch(db, new_alert.id, payload)
        new_alert.notification_status = "DELIVERED" if dispatched else "FAILED"
        db.commit()
        db.refresh(new_alert)

        return new_alert

    @staticmethod
    def update_alert_status(db: Session, alert_id: str, new_status: str) -> Optional[Alert]:
        alert = AlertRepository.get_by_id(db, alert_id)
        if not alert:
            return None
        return AlertRepository.update_status(db, alert, new_status)

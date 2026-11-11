"""
Alert Lifecycle and Incident Management Service.
"""

from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.repositories.alerts import AlertRepository
from backend.repositories.cameras import CameraRepository
from backend.services.notification_service import notification_service
from backend.models.alert import Alert
from backend.models.detection import Detection
from backend.models.notification_log import NotificationLog


class AlertService:

    @staticmethod
    def process_incident(
        db: Session,
        alert_type: str,
        camera_id: Optional[str],
        detection_id: Optional[str],
        confidence: float,
        source_id: Optional[str] = None,
        source_name: Optional[str] = None,
    ) -> Alert:
        severity = "CRITICAL" if alert_type == "fire" else "WARNING"
        incident_source_id = source_id or camera_id

        existing_alert = None
        if camera_id:
            existing_alert = AlertRepository.get_active_for_camera(db, camera_id, alert_type)
        elif incident_source_id:
            existing_alert = AlertRepository.get_active_for_source(
                db,
                incident_source_id,
                alert_type,
            )

        now = datetime.now(timezone.utc)
        if existing_alert:
            existing_alert.last_seen_at = now
            existing_alert.detection_id = detection_id
            if source_name:
                existing_alert.source_name = source_name

            # Check if we should notify Telegram
            last_delivered = db.query(NotificationLog).filter(
                NotificationLog.alert_id == existing_alert.id,
                NotificationLog.status == "DELIVERED"
            ).order_by(NotificationLog.delivered_at.desc()).first()

            should_notify = False
            if existing_alert.notification_status != "DELIVERED":
                should_notify = True
            elif last_delivered is None or last_delivered.delivered_at is None:
                should_notify = True
            else:
                delivered_ts = (
                    last_delivered.delivered_at.replace(tzinfo=timezone.utc).timestamp()
                    if last_delivered.delivered_at.tzinfo is None
                    else last_delivered.delivered_at.timestamp()
                )
                if (now.timestamp() - delivered_ts) >= 45.0:
                    should_notify = True

            if should_notify and alert_type.lower() == "fire" and settings.TELEGRAM_ENABLED:
                detection = db.get(Detection, detection_id) if detection_id else None
                temporal_state = detection.temporal_state if detection and detection.temporal_state else {}
                verified_count_key = "positive_fire_count" if alert_type == "fire" else "positive_smoke_count"
                evidence = (detection.heatmap_path or detection.image_path) if detection else None
                payload = {
                    "alert_id": existing_alert.id,
                    "incident_id": existing_alert.id,
                    "detection_id": detection_id,
                    "source_id": incident_source_id,
                    "alert_type": alert_type,
                    "severity": severity,
                    "camera_name": source_name or "Active Camera",
                    "source_name": source_name or "Active Camera",
                    "confidence": confidence,
                    "timestamp": now.isoformat(),
                    "verification_frames": temporal_state.get(verified_count_key),
                    "evidence_path": evidence,
                }
                dispatched = notification_service.dispatch(db, existing_alert.id, payload)
                if dispatched:
                    existing_alert.notification_status = "DELIVERED"
            db.commit()
            db.refresh(existing_alert)
            return existing_alert

        # Create new incident
        new_alert = AlertRepository.create(
            db=db,
            alert_type=alert_type,
            severity=severity,
            camera_id=camera_id,
            detection_id=detection_id,
            source_id=incident_source_id,
            source_name=source_name,
        )

        # Lookup camera metadata
        camera_name = source_name or "Upload Source"
        location_label = "Unassigned Location"
        source_type = "upload"
        system_status = "Upload analysis"
        if camera_id:
            cam = CameraRepository.get_by_id(db, camera_id)
            if cam:
                camera_name = cam.name
                location_label = cam.location_label or "Field Station"
                source_type = cam.source_type
                system_status = cam.status
        elif source_name:
            system_status = "Simulated CCTV demonstration"

        detection = db.get(Detection, detection_id) if detection_id else None
        if detection and not camera_id:
            source_type = detection.source_type
            if incident_source_id:
                camera_name = f"{source_type.replace('_', ' ').title()} {incident_source_id[-8:]}"
        temporal_state = detection.temporal_state if detection and detection.temporal_state else {}
        verified_count_key = "positive_fire_count" if alert_type == "fire" else "positive_smoke_count"

        payload = {
            "alert_id": new_alert.id,
            "incident_id": new_alert.id,
            "detection_id": detection_id,
            "source_id": incident_source_id,
            "alert_type": alert_type,
            "severity": severity,
            "camera_name": camera_name,
            "source_name": camera_name,
            "source_type": source_type,
            "system_status": system_status,
            "location_label": location_label,
            "confidence": confidence,
            "timestamp": now.isoformat(),
            "verification_frames": temporal_state.get(verified_count_key),
            "evidence_path": (detection.heatmap_path or detection.image_path) if detection else None,
        }

        if alert_type.lower() == "fire" and settings.TELEGRAM_ENABLED:
            dispatched = notification_service.dispatch(db, new_alert.id, payload)
            new_alert.notification_status = "DELIVERED" if dispatched else "FAILED"
        elif alert_type.lower() == "fire":
            new_alert.notification_status = "PENDING"
        else:
            new_alert.notification_status = "NOT_APPLICABLE"
        db.commit()
        db.refresh(new_alert)

        return new_alert

    @staticmethod
    def update_alert_status(db: Session, alert_id: str, new_status: str) -> Optional[Alert]:
        alert = AlertRepository.get_by_id(db, alert_id)
        if not alert:
            return None
        return AlertRepository.update_status(db, alert, new_status)

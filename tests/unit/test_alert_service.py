"""
Unit Tests for Alert Service and Status Transitions.
"""

from backend.core.config import settings
from backend.models.alert import Alert
from backend.services.alert_service import AlertService
from backend.models.notification_log import NotificationLog
from backend.services.notification_service import notification_service


def test_alert_service_creation_and_severity(db_session):
    alert = AlertService.process_incident(
        db=db_session,
        alert_type="fire",
        camera_id=None,
        detection_id=None,
        confidence=0.92
    )

    assert alert.id is not None
    assert alert.alert_type == "fire"
    assert alert.severity == "CRITICAL"
    assert alert.status == "ACTIVE"
    assert alert.first_seen_at is not None


def test_alert_status_acknowledgement_and_closure(db_session):
    alert = AlertService.process_incident(
        db=db_session,
        alert_type="smoke",
        camera_id=None,
        detection_id=None,
        confidence=0.81
    )

    # Acknowledge
    ack = AlertService.update_alert_status(db_session, alert.id, "ACKNOWLEDGED")
    assert ack.status == "ACKNOWLEDGED"
    assert ack.acknowledged_at is not None

    # Close
    closed = AlertService.update_alert_status(db_session, alert.id, "CLOSED")
    assert closed.status == "CLOSED"
    assert closed.closed_at is not None


def test_upload_source_incident_updates_without_duplicate_notification(db_session, monkeypatch):
    dispatched_alerts = []
    monkeypatch.setattr(settings, "TELEGRAM_ENABLED", True)
    monkeypatch.setattr(
        notification_service,
        "dispatch",
        lambda db, alert_id, payload: dispatched_alerts.append(alert_id) or True,
    )
    first = AlertService.process_incident(
        db=db_session,
        alert_type="fire",
        camera_id=None,
        detection_id=None,
        confidence=0.92,
        source_id="video-task-1",
    )
    repeated = AlertService.process_incident(
        db=db_session,
        alert_type="fire",
        camera_id=None,
        detection_id=None,
        confidence=0.94,
        source_id="video-task-1",
    )
    separate = AlertService.process_incident(
        db=db_session,
        alert_type="fire",
        camera_id=None,
        detection_id=None,
        confidence=0.93,
        source_id="video-task-2",
    )

    assert repeated.id == first.id
    assert separate.id != first.id
    assert dispatched_alerts == [first.id, separate.id]


def test_incident_retains_demo_source_name(db_session, monkeypatch):
    payloads = []
    monkeypatch.setattr(settings, "TELEGRAM_ENABLED", True)
    monkeypatch.setattr(
        notification_service,
        "dispatch",
        lambda db, alert_id, payload: payloads.append(payload) or True,
    )

    incident = AlertService.process_incident(
        db=db_session,
        alert_type="fire",
        camera_id=None,
        detection_id=None,
        confidence=0.93,
        source_id="demo-cam02-fire",
        source_name="CAM 02 - FOREST FIRE",
    )

    assert incident.source_name == "CAM 02 - FOREST FIRE"
    assert payloads[0]["source_name"] == "CAM 02 - FOREST FIRE"


def test_repeated_demo_video_fire_does_not_notify_again_after_incident_closure(
    db_session,
    monkeypatch,
):
    dispatched_alerts = []
    monkeypatch.setattr(settings, "TELEGRAM_ENABLED", True)
    monkeypatch.setattr(
        notification_service,
        "dispatch",
        lambda db, alert_id, payload: dispatched_alerts.append(alert_id) or True,
    )
    first = AlertService.process_incident(
        db=db_session,
        alert_type="fire",
        camera_id=None,
        detection_id="frame-1",
        confidence=0.93,
        source_id="demo-cam02-fire",
        source_name="CAM 02 - FOREST FIRE",
    )
    AlertService.update_alert_status(db_session, first.id, "CLOSED")

    repeated = AlertService.process_incident(
        db=db_session,
        alert_type="fire",
        camera_id=None,
        detection_id="frame-looped",
        confidence=0.95,
        source_id="demo-cam02-fire",
        source_name="CAM 02 - FOREST FIRE",
    )

    assert repeated.id == first.id
    assert repeated.status == "CLOSED"
    assert db_session.query(Alert).count() == 1
    assert dispatched_alerts == [first.id]

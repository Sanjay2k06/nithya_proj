"""
Unit Tests for Alert Service and Status Transitions.
"""

from backend.services.alert_service import AlertService
from backend.repositories.alerts import AlertRepository


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

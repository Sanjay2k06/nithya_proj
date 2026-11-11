from backend.core.config import settings
from backend.models.notification_log import NotificationLog
from backend.services.alert_service import AlertService
from backend.services.notification_service import TelegramNotificationProvider, notification_service


class TelegramResponse:
    status_code = 200
    is_success = True

    def __init__(self, body):
        self.body = body

    def json(self):
        return self.body


class TelegramClient:
    response_body = {"ok": True, "result": {"message_id": 1}}
    requests = []

    def __init__(self, timeout):
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def post(self, url, json=None, data=None, files=None):
        self.requests.append({"url": url, "json": json, "data": data, "files": files})
        return TelegramResponse(self.response_body)


def enable_telegram(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_ENABLED", True)
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setattr(settings, "TELEGRAM_CHAT_ID", "test-chat")
    monkeypatch.setattr("backend.services.notification_service.httpx.Client", TelegramClient)
    TelegramClient.requests = []
    TelegramClient.response_body = {"ok": True, "result": {"message_id": 1}}


def test_telegram_requires_explicit_enablement(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_ENABLED", False)
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setattr(settings, "TELEGRAM_CHAT_ID", "test-chat")

    success, error = TelegramNotificationProvider().send({"message": "test"})

    assert not success
    assert error == "TELEGRAM_DISABLED"


def test_telegram_http_200_with_rejected_body_is_not_delivered(monkeypatch):
    enable_telegram(monkeypatch)
    TelegramClient.response_body = {"ok": False, "description": "Chat not found"}

    success, error = TelegramNotificationProvider().send({"message": "test"})

    assert not success
    assert error == "TELEGRAM_API_REJECTED: Chat not found"


def test_telegram_smoke_message_is_not_labeled_as_fire():
    message = TelegramNotificationProvider().build_message({
        "alert_type": "smoke",
        "confidence": 0.83,
        "incident_id": "incident-1",
        "verification_frames": 3,
    })

    assert "SMOKE DETECTED" in message
    assert "VERIFIED FIRE DETECTED" not in message
    assert "FOREST FIRE EMERGENCY ALERT" not in message


def test_telegram_test_and_history_record_real_result(monkeypatch, client, db_session):
    enable_telegram(monkeypatch)

    response = client.post("/api/v1/notifications/telegram/test")

    assert response.status_code == 200
    notification = response.json()
    assert notification["channel"] == "telegram"
    assert notification["status"] == "DELIVERED"
    assert notification["recipient"] == "test-chat"
    assert notification["alert_id"] is None

    history = client.get("/api/v1/notifications")
    assert history.status_code == 200
    assert history.json()["total"] == 1
    assert history.json()["items"][0]["id"] == notification["id"]

    status = client.get("/api/v1/notifications/telegram/status")
    assert status.status_code == 200
    assert status.json()["connection_status"] == "connected"
    assert status.json()["delivered_messages"] == 1
    assert "test-token" not in status.text


def test_telegram_test_endpoint_rejects_disabled_configuration(monkeypatch, client):
    monkeypatch.setattr(settings, "TELEGRAM_ENABLED", False)
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", None)
    monkeypatch.setattr(settings, "TELEGRAM_CHAT_ID", None)

    response = client.post("/api/v1/notifications/telegram/test")

    assert response.status_code == 409
    assert response.json()["detail"] == "TELEGRAM_DISABLED"


def test_enabled_telegram_without_credentials_is_failed_not_console_success(monkeypatch, db_session):
    monkeypatch.setattr(settings, "TELEGRAM_ENABLED", True)
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", None)
    monkeypatch.setattr(settings, "TELEGRAM_CHAT_ID", None)

    alert = AlertService.process_incident(
        db=db_session,
        alert_type="fire",
        camera_id=None,
        detection_id=None,
        confidence=0.91,
    )
    log = db_session.query(NotificationLog).filter_by(alert_id=alert.id).one()

    assert alert.notification_status == "FAILED"
    assert log.channel == "telegram"
    assert log.status == "FAILED"
    assert log.error_code == "TELEGRAM_CREDENTIALS_MISSING"


def test_unsupported_provider_is_not_reported_as_delivered(monkeypatch, db_session):
    monkeypatch.setattr(settings, "TELEGRAM_ENABLED", False)
    monkeypatch.setattr(settings, "NOTIFICATION_PROVIDER", "email")

    alert = AlertService.process_incident(
        db=db_session,
        alert_type="fire",
        camera_id=None,
        detection_id=None,
        confidence=0.78,
    )
    assert alert.notification_status == "PENDING"
    notification_service.dispatch(
        db_session,
        alert.id,
        {"alert_type": "fire", "confidence": 0.78, "source_name": "Test source"},
    )
    log = db_session.query(NotificationLog).filter_by(alert_id=alert.id).one()

    assert log.channel == "email"
    assert log.status == "FAILED"
    assert log.error_code == "EMAIL_PROVIDER_UNAVAILABLE"


def test_smoke_incident_does_not_send_an_emergency_notification(monkeypatch, db_session):
    enable_telegram(monkeypatch)

    alert = AlertService.process_incident(
        db=db_session,
        alert_type="smoke",
        camera_id=None,
        detection_id=None,
        confidence=0.84,
    )

    assert alert.notification_status == "NOT_APPLICABLE"
    assert db_session.query(NotificationLog).filter_by(alert_id=alert.id).count() == 0


def test_failed_notification_can_be_retried(monkeypatch, db_session):
    enable_telegram(monkeypatch)
    original = NotificationLog(
        channel="telegram",
        status="FAILED",
        recipient="test-chat",
        message="Retry this test",
        retry_count=0,
        error_code="TELEGRAM_NETWORK_ERROR",
    )
    db_session.add(original)
    db_session.commit()
    db_session.refresh(original)

    retried = notification_service.retry(db_session, original)

    assert retried.status == "DELIVERED"
    assert retried.retry_count == 1
    assert retried.message == original.message


def test_retry_endpoint_records_a_new_attempt(monkeypatch, client, db_session):
    enable_telegram(monkeypatch)
    original = NotificationLog(
        channel="telegram",
        status="FAILED",
        recipient="test-chat",
        message="Retry this notification",
        retry_count=0,
        error_code="TELEGRAM_NETWORK_ERROR",
    )
    db_session.add(original)
    db_session.commit()
    db_session.refresh(original)

    response = client.post(f"/api/v1/notifications/{original.id}/retry")

    assert response.status_code == 200
    assert response.json()["status"] == "DELIVERED"
    assert response.json()["retry_count"] == 1
    assert response.json()["id"] != original.id

"""
Integration Tests for Alert Triage and Status Transitions.
"""

from backend.repositories.alerts import AlertRepository


def test_alert_lifecycle_workflow(client, db_session):
    # 1. Create alert
    alert = AlertRepository.create(
        db=db_session,
        alert_type="fire",
        severity="CRITICAL"
    )

    # 2. List active alerts
    res = client.get("/api/v1/alerts?status=ACTIVE")
    assert res.status_code == 200
    data = res.json()
    assert any(a["id"] == alert.id for a in data["items"])

    # 3. Acknowledge alert
    res_ack = client.patch(f"/api/v1/alerts/{alert.id}/status", json={"status": "ACKNOWLEDGED"})
    assert res_ack.status_code == 200
    assert res_ack.json()["status"] == "ACKNOWLEDGED"

    # 4. Close alert
    res_close = client.patch(f"/api/v1/alerts/{alert.id}/status", json={"status": "CLOSED"})
    assert res_close.status_code == 200
    assert res_close.json()["status"] == "CLOSED"

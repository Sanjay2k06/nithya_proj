import threading
import time

import pytest

from backend.api.v1 import monitoring
from backend.services.demo_monitoring_service import demo_monitoring_service


class EmptySession:
    def close(self):
        pass


def _fake_gemini_analysis(image_bytes, mime_type, timeout_seconds):
    assert image_bytes
    assert mime_type == "image/jpeg"
    assert timeout_seconds == 60.0
    return {
        "classification": "normal",
        "observation": "No visible fire or smoke in this sampled frame.",
        "evidence": ["Forest canopy is visible."],
    }


def test_demo_source_inventory_uses_the_two_local_videos(client):
    response = client.get("/api/v1/monitoring/demo-sources")

    assert response.status_code == 200
    sources = {source["source_id"]: source for source in response.json()}
    assert sources["cam01-normal"]["file_name"] == "forest_normal.mp4"
    assert sources["cam02-fire"]["file_name"] == "forest_fire.mp4"
    assert sources["cam01-normal"]["available"] is True
    assert sources["cam02-fire"]["available"] is True
    assert all(source["source_type"] == "simulated_cctv" for source in sources.values())
    assert all(source["source_status"] == "AVAILABLE" for source in sources.values())


def test_monitoring_requires_gemini_configuration(client, monkeypatch):
    monkeypatch.setattr(monitoring.settings, "GEMINI_API_KEY", None)
    try:
        assert client.post("/api/v1/monitoring/demo-sources/start").status_code == 409
        assert client.post(
            "/api/v1/monitoring/demo-sources/select",
            json={"source_id": "cam01-normal"},
        ).status_code == 200

        response = client.post("/api/v1/monitoring/demo-sources/start")
        assert response.status_code == 503
        assert "gemini" in response.json()["detail"].lower()

        status = client.get("/api/v1/monitoring/demo-sources/status").json()
        assert status["status"] == "IDLE"
        assert status["is_monitoring"] is False
        assert status["latest_detection"] is None
    finally:
        demo_monitoring_service.stop()


@pytest.mark.parametrize(
    ("source_id", "expected_class"),
    [("cam01-normal", "normal"), ("cam02-fire", "fire")],
)
def test_backend_worker_decodes_video_and_publishes_frame_state(monkeypatch, source_id, expected_class):
    service = demo_monitoring_service
    processed = threading.Event()
    original_finish = service.finish_frame
    result = _fake_gemini_analysis(b"frame", "image/jpeg", 60.0)
    result["classification"] = expected_class

    def stop_after_first_frame(selected_source_id, stop_event, started_at):
        def finish_and_stop(result, video_timestamp_seconds, processing_delay_ms):
            original_finish(result, video_timestamp_seconds, processing_delay_ms)
            stop_event.set()
            processed.set()

        monkeypatch.setattr(service, "finish_frame", finish_and_stop)
        monitoring.process_demo_video(selected_source_id, stop_event, started_at)

    monkeypatch.setattr(service, "record_processed_frame", lambda *args: None)
    monkeypatch.setattr(monitoring, "SessionLocal", EmptySession)
    monkeypatch.setattr(
        monitoring.gemini_analysis_service,
        "analyze_image",
        lambda *args, **kwargs: result,
    )

    try:
        service.stop()
        service.select_source(source_id)
        service.start(stop_after_first_frame)
        assert processed.wait(timeout=10)

        deadline = time.monotonic() + 5
        while service.get_status()["status"] != "STOPPED" and time.monotonic() < deadline:
            time.sleep(0.02)
        status = service.get_status()
        assert status["status"] == "STOPPED"
        assert status["processed_frames"] == 1
        assert status["latest_detection"]["predicted_class"] == expected_class
        assert status["latest_detection"]["analysis_provider"] == "gemini"
        assert status["latest_detection"]["confidence"] is None
        assert status["latest_detection"]["alert_triggered"] is False
        assert status["latest_detection"]["temporally_verified"] is False
        assert status["selected_source"]["source_id"] == source_id
        assert status["last_processed_video_seconds"] is not None
    finally:
        service.finish_frame = original_finish
        service.stop()


def test_start_endpoint_runs_gemini_and_stop_clears_the_result(client, monkeypatch):
    service = demo_monitoring_service
    monkeypatch.setattr(monitoring.settings, "GEMINI_API_KEY", "unit-test-key")
    monkeypatch.setattr(monitoring, "SessionLocal", EmptySession)
    monkeypatch.setattr(service, "record_processed_frame", lambda *args: None)
    monkeypatch.setattr(monitoring.gemini_analysis_service, "analyze_image", _fake_gemini_analysis)

    try:
        service.stop()
        selected = client.post(
            "/api/v1/monitoring/demo-sources/select",
            json={"source_id": "cam02-fire"},
        )
        assert selected.status_code == 200

        started = client.post("/api/v1/monitoring/demo-sources/start")
        assert started.status_code == 200

        deadline = time.monotonic() + 10
        status = {}
        while time.monotonic() < deadline:
            status = client.get("/api/v1/monitoring/demo-sources/status").json()
            if status["processed_frames"] > 0:
                break
            time.sleep(0.02)
        assert status["status"] == "IN_PROGRESS"
        assert status["latest_detection"]["analysis_provider"] == "gemini"
        assert status["latest_detection"]["notification_status"] == "NOT_SENT"

        stopped = client.post("/api/v1/monitoring/demo-sources/stop")
        assert stopped.status_code == 200
        assert stopped.json()["status"] == "STOPPED"
        assert stopped.json()["latest_detection"] is None
        assert stopped.json()["last_processed_video_seconds"] is None
    finally:
        service.stop()
        service.select_source("cam01-normal")


def test_invalid_demo_source_video_returns_not_found(client, monkeypatch, tmp_path):
    missing_video = tmp_path / "missing-demo-video.mp4"
    monkeypatch.setattr(demo_monitoring_service, "get_video_path", lambda source_id: missing_video)
    assert client.get("/api/v1/monitoring/demo-sources/cam01-normal/video").status_code == 404


def test_video_decoder_errors_are_reported_and_release_the_capture(monkeypatch):
    service = demo_monitoring_service
    original_capture = monitoring.cv2.VideoCapture
    captures = []

    def track_capture(path):
        capture = original_capture(path)
        captures.append(capture)
        return capture

    def fail_inference(*args, **kwargs):
        raise RuntimeError("test inference failure")

    monkeypatch.setattr(monitoring.cv2, "VideoCapture", track_capture)
    monkeypatch.setattr(monitoring, "SessionLocal", EmptySession)
    monkeypatch.setattr(monitoring.gemini_analysis_service, "analyze_image", fail_inference)

    try:
        service.stop()
        service.select_source("cam01-normal")
        service.start(monitoring.process_demo_video)

        deadline = time.monotonic() + 10
        while service.get_status()["status"] != "ERROR" and time.monotonic() < deadline:
            time.sleep(0.02)
        status = service.get_status()
        assert status["status"] == "ERROR"
        assert "test inference failure" in status["error"]
        assert captures and captures[0].isOpened() is False
    finally:
        service.stop()
        service.select_source("cam01-normal")


def test_selecting_another_source_stops_the_active_backend_task(client):
    service = demo_monitoring_service

    def wait_for_stop(source_id, stop_event, started_at):
        stop_event.wait(timeout=10)

    try:
        service.stop()
        service.select_source("cam01-normal")
        service.start(wait_for_stop)

        response = client.post(
            "/api/v1/monitoring/demo-sources/select",
            json={"source_id": "cam02-fire"},
        )

        assert response.status_code == 200
        status = client.get("/api/v1/monitoring/demo-sources/status").json()
        assert status["selected_source"]["source_id"] == "cam02-fire"
        assert status["status"] == "IDLE"
        assert status["is_monitoring"] is False
    finally:
        service.stop()
        service.select_source("cam01-normal")

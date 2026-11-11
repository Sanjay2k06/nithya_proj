"""
Integration Tests for Prediction and Model APIs.
"""

import io
from pathlib import Path

import cv2
import numpy as np

from backend.services.prediction_service import prediction_service
from backend.core.config import settings
from backend.services.gemini_analysis_service import gemini_analysis_service


class StubTrainedEngine:
    is_loaded = True
    demo_mode = False
    device = "cpu"
    checkpoint_metadata = {"config": {"version": "test-checkpoint"}}

    @staticmethod
    def predict(frame_bgr, generate_explanation=True):
        return {
            "predicted_class": "normal",
            "confidence": 0.91,
            "probabilities": {"fire": 0.03, "smoke": 0.06, "normal": 0.91},
            "inference_ms": 4.2,
            "model_version": "test-checkpoint",
            "demo_mode": False,
            "blended_bgr": frame_bgr.copy(),
        }

def test_health_endpoint(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "database" in data
    assert "model_loaded" in data


def test_model_status_endpoint(client):
    res = client.get("/api/v1/model/status")
    assert res.status_code == 200
    data = res.json()
    assert data["model_name"] == "FireNetCNN"
    assert data["classes"] == ["fire", "smoke", "normal"]


def test_image_prediction_endpoint(client, monkeypatch):
    monkeypatch.setattr(prediction_service, "engine", StubTrainedEngine())

    # Create valid synthetic image in memory
    img = np.zeros((224, 224, 3), dtype=np.uint8)
    img[60:140, 60:140] = [30, 100, 255]  # flame patch
    _, img_encoded = cv2.imencode(".jpg", img)

    file_bytes = io.BytesIO(img_encoded.tobytes())
    files = {"file": ("test_frame.jpg", file_bytes, "image/jpeg")}

    res = client.post("/api/v1/predictions/image", files=files)
    assert res.status_code == 200
    data = res.json()

    assert "predicted_class" in data
    assert data["predicted_class"] in ["fire", "smoke", "normal"]
    assert "confidence" in data
    assert "inference_ms" in data
    assert "heatmap_image_url" in data
    assert data["detection_id"] is not None
    assert data["source_id"]

    second_res = client.post(
        "/api/v1/predictions/image",
        files={"file": ("test_frame.jpg", io.BytesIO(img_encoded.tobytes()), "image/jpeg")},
    )
    assert second_res.status_code == 200
    assert second_res.json()["source_id"] != data["source_id"]


def test_image_prediction_requires_loaded_trained_model(client, monkeypatch):
    monkeypatch.setattr(prediction_service, "engine", None)
    monkeypatch.setattr(prediction_service, "model_error", "Trained checkpoint missing.")
    img = np.zeros((224, 224, 3), dtype=np.uint8)
    _, img_encoded = cv2.imencode(".jpg", img)

    res = client.post(
        "/api/v1/predictions/image",
        files={"file": ("forest_normal.jpg", io.BytesIO(img_encoded.tobytes()), "image/jpeg")},
    )

    assert res.status_code == 503
    assert res.json()["detail"] == "Trained checkpoint missing."


def test_gemini_image_upload_is_informational_and_not_persisted(client, monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "unit-test-key")
    monkeypatch.setattr(
        gemini_analysis_service,
        "analyze_image",
        lambda image_bytes, mime_type: {
            "classification": "fire",
            "observation": "Visible flames.",
            "evidence": ["Orange flames among trees."],
        },
    )
    monkeypatch.setattr(
        prediction_service,
        "process_frame",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("FireNet must not run for Gemini.")),
    )
    image = np.zeros((128, 128, 3), dtype=np.uint8)
    _, encoded = cv2.imencode(".jpg", image)

    response = client.post(
        "/api/v1/predictions/image",
        data={"provider": "gemini"},
        files={"file": ("forest.jpg", io.BytesIO(encoded.tobytes()), "image/jpeg")},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["analysis_provider"] == "gemini"
    assert result["predicted_class"] == "fire"
    assert result["confidence"] is None
    assert result["detection_id"] is None
    assert result["alert_triggered"] is False
    assert result["notification_status"] == "NOT_SENT"
    assert "not persisted" in result["analysis_caveat"].lower()


def test_gemini_video_upload_requires_configured_key(client, monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", " ")
    video_path = Path(__file__).resolve().parents[2] / "image_fire" / "forest_normal.mp4"

    with video_path.open("rb") as video:
        response = client.post(
            "/api/v1/predictions/video",
            data={"provider": "gemini"},
            files={"file": ("forest_normal.mp4", video, "video/mp4")},
        )

    assert response.status_code == 503
    assert "GEMINI_API_KEY" in response.json()["detail"]


def test_video_upload_rejects_corrupt_video(client, monkeypatch):
    monkeypatch.setattr(prediction_service, "engine", None)
    response = client.post(
        "/api/v1/predictions/video",
        files={"file": ("corrupted.mp4", io.BytesIO(b"not a video"), "video/mp4")},
    )

    assert response.status_code == 400
    assert "corrupt" in response.json()["detail"].lower()


def test_video_upload_requires_loaded_trained_model(client, monkeypatch):
    monkeypatch.setattr(prediction_service, "engine", None)
    monkeypatch.setattr(prediction_service, "model_error", "Trained checkpoint missing.")
    video_path = Path(__file__).resolve().parents[2] / "image_fire" / "forest_normal.mp4"
    assert video_path.is_file()

    with video_path.open("rb") as video:
        response = client.post(
            "/api/v1/predictions/video",
            files={"file": ("forest_normal.mp4", video, "video/mp4")},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == "Trained checkpoint missing."


def test_invalid_image_upload_rejection(client):
    # Send text file disguised as image
    fake_file = io.BytesIO(b"Not an image file!")
    files = {"file": ("corrupted.jpg", fake_file, "image/jpeg")}

    res = client.post("/api/v1/predictions/image", files=files)
    assert res.status_code == 400
    assert "corrupt or invalid" in res.json()["detail"].lower()

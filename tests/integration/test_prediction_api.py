"""
Integration Tests for Prediction and Model APIs.
"""

import io
import cv2
import numpy as np


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


def test_image_prediction_endpoint(client):
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


def test_invalid_image_upload_rejection(client):
    # Send text file disguised as image
    fake_file = io.BytesIO(b"Not an image file!")
    files = {"file": ("corrupted.jpg", fake_file, "image/jpeg")}

    res = client.post("/api/v1/predictions/image", files=files)
    assert res.status_code == 400
    assert "corrupt or invalid" in res.json()["detail"].lower()

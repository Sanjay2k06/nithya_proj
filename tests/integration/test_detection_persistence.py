"""
Integration Tests for Detection Persistence and Query Filtering.
"""

from backend.repositories.detections import DetectionRepository


def test_detection_persistence_and_retrieval(client, db_session):
    # Insert detection record
    rec = DetectionRepository.create(
        db=db_session,
        detection_data={
            "camera_id": None,
            "source_type": "stream",
            "predicted_class": "fire",
            "confidence": 0.94,
            "probabilities_json": {"fire": 0.94, "smoke": 0.04, "normal": 0.02},
            "frame_timestamp": 123456789.0,
            "inference_ms": 11.5,
            "model_version": "1.0.0",
            "image_path": "/media/originals/test.jpg",
            "heatmap_path": "/media/heatmaps/test.jpg"
        }
    )

    # Query via API
    res = client.get(f"/api/v1/detections/{rec.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == rec.id
    assert data["predicted_class"] == "fire"
    assert data["confidence"] == 0.94


def test_paginated_detections_filtering(client, db_session):
    # Add multiple detections
    for i, c in enumerate(["fire", "smoke", "normal"]):
        DetectionRepository.create(
            db=db_session,
            detection_data={
                "camera_id": None,
                "source_type": "stream",
                "predicted_class": c,
                "confidence": 0.80 + i * 0.05,
                "probabilities_json": {c: 0.85},
                "frame_timestamp": 100.0 + i,
                "inference_ms": 10.0,
                "model_version": "1.0.0"
            }
        )

    # Filter by class
    res = client.get("/api/v1/detections?class_name=fire")
    assert res.status_code == 200
    data = res.json()
    assert all(item["predicted_class"] == "fire" for item in data["items"])

import torch
import pytest

from backend.core.config import settings
from backend.models.alert import Alert
from backend.services.alert_service import AlertService
from backend.services.prediction_service import PredictionService
from backend.services.prediction_service import prediction_service
from ml.checkpoints import load_model_from_checkpoint
from ml.inference import InferenceEngine


def test_missing_trained_checkpoint_does_not_create_a_demo_model(tmp_path):
    checkpoint = tmp_path / "missing-firenet.pt"

    with pytest.raises(FileNotFoundError, match="Trained checkpoint not found"):
        InferenceEngine(checkpoint_path=str(checkpoint), demo_mode=False)


@pytest.mark.parametrize(
    ("metadata", "error"),
    [
        (
            {"model_architecture": "FireNetCNN", "classes": ["normal", "fire", "smoke"]},
            "class order",
        ),
        (
            {"model_architecture": "ResNet18", "classes": ["fire", "smoke", "normal"]},
            "Expected a FireNet-CNN",
        ),
        (
            {
                "model_architecture": "FireNetCNN",
                "classes": ["fire", "smoke", "normal"],
                "config": {"num_classes": 4},
            },
            "exactly three output classes",
        ),
        (
            {
                "model_architecture": "FireNetCNN",
                "classes": ["fire", "smoke", "normal"],
                "config": {"image_size": [299, 299]},
            },
            "image size must be",
        ),
        (
            {
                "model_architecture": "FireNetCNN",
                "classes": ["fire", "smoke", "normal"],
                "config": {"in_channels": 1},
            },
            "three input channels",
        ),
    ],
)
def test_incompatible_checkpoint_metadata_is_rejected(tmp_path, metadata, error):
    checkpoint = tmp_path / "incompatible.pt"
    torch.save({**metadata, "model_state_dict": {}}, checkpoint)

    with pytest.raises(ValueError, match=error):
        load_model_from_checkpoint(str(checkpoint))


def test_prediction_service_does_not_fall_back_to_demo_inference(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MODEL_PATH", str(tmp_path / "missing-firenet.pt"))
    monkeypatch.setattr(settings, "MODEL_DEMO_MODE", False)

    service = PredictionService()

    assert service.engine is None
    assert service.model_error is not None
    assert "missing-firenet.pt" in service.model_error


def test_demo_mode_predictions_cannot_create_an_incident_or_send_notifications(
    db_session,
    dummy_bgr_frame,
    monkeypatch,
):
    class DemoEngine:
        demo_mode = True

        @staticmethod
        def predict(frame_bgr, generate_explanation=True):
            return {
                "predicted_class": "fire",
                "confidence": 0.99,
                "probabilities": {"fire": 0.99, "smoke": 0.005, "normal": 0.005},
                "inference_ms": 1.0,
                "demo_mode": True,
                "model_version": "demo",
            }

    def fail_if_dispatched(*args, **kwargs):
        raise AssertionError("Demo inference must not create incidents or dispatch Telegram.")

    monkeypatch.setattr(prediction_service, "engine", DemoEngine())
    monkeypatch.setattr(AlertService, "process_incident", fail_if_dispatched)
    stream_id = "demo-test-untrained-source"
    prediction_service.temporal_verifier.reset_camera(stream_id)
    try:
        result = None
        for _ in range(3):
            result = prediction_service.process_frame(
                db=db_session,
                frame_bgr=dummy_bgr_frame,
                source_type="simulated_cctv",
                source_id=stream_id,
                save_media=False,
            )

        assert result is not None
        assert result["temporal_state"]["is_temporally_verified"] is True
        assert result["alert_id"] is None
        assert result["alert_triggered"] is False
        assert db_session.query(Alert).count() == 0
    finally:
        prediction_service.temporal_verifier.reset_camera(stream_id)

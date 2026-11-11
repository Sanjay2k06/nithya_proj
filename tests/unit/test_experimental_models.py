import numpy as np
import pytest
import torch

from ml.experimental.attention import CBAM
from ml.experimental.progression import measure_optical_flow


def test_cbam_preserves_feature_shape_and_gradients():
    features = torch.rand(2, 32, 14, 14, requires_grad=True)
    output = CBAM(32)(features)

    assert output.shape == features.shape
    assert torch.isfinite(output).all()
    output.mean().backward()
    assert features.grad is not None


def test_optical_flow_reports_motion_without_spread_claims():
    previous = np.zeros((40, 40, 3), dtype=np.uint8)
    current = previous.copy()
    current[10:20, 12:22] = 255

    metrics = measure_optical_flow(previous, current)

    assert metrics["mean_displacement_px_per_sample"] >= 0
    assert 0 <= metrics["moving_pixel_percent"] <= 100


def test_optical_flow_rejects_mismatched_frames():
    with pytest.raises(ValueError, match="matching dimensions"):
        measure_optical_flow(np.zeros((10, 10), dtype=np.uint8), np.zeros((12, 10), dtype=np.uint8))

"""
Unit Tests for Grad-CAM Explainable AI Generation.
"""

import numpy as np
import torch
from ml.model import FireNetCNN
from ml.gradcam import GradCAM


def test_gradcam_heatmap_dimensions_and_values():
    model = FireNetCNN(num_classes=3)
    gradcam = GradCAM(model)

    dummy_tensor = torch.randn(1, 3, 224, 224)
    heatmap = gradcam.generate_heatmap(dummy_tensor, target_class_idx=0)

    assert isinstance(heatmap, np.ndarray)
    assert heatmap.shape == (224, 224), f"Expected (224, 224), got {heatmap.shape}"
    assert heatmap.min() >= 0.0 and heatmap.max() <= 1.0, "Heatmap must be normalized between 0 and 1"

    gradcam.close()


def test_gradcam_overlay_blending():
    orig_bgr = np.zeros((224, 224, 3), dtype=np.uint8)
    heatmap = np.ones((224, 224), dtype=np.float32) * 0.8

    blended = GradCAM.overlay_heatmap(orig_bgr, heatmap, alpha=0.5)

    assert blended.shape == (224, 224, 3)
    assert blended.dtype == np.uint8
    # Blended image should have non-zero pixels from the colormap
    assert blended.sum() > 0

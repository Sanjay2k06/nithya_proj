"""
Unit Tests for Preprocessing and Frame Transforms.
"""

import numpy as np
import pytest
import torch
from ml.transforms import preprocess_numpy_frame, get_train_transforms, get_eval_transforms


def test_preprocess_valid_bgr_frame():
    bgr_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    tensor = preprocess_numpy_frame(bgr_frame)

    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape == (1, 3, 224, 224)
    assert tensor.dtype == torch.float32


def test_preprocess_empty_frame_rejection():
    empty_frame = np.array([])
    with pytest.raises(ValueError):
        preprocess_numpy_frame(empty_frame)


def test_preprocess_none_frame_rejection():
    with pytest.raises(ValueError):
        preprocess_numpy_frame(None)

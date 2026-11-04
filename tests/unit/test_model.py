"""
Unit Tests for FireNetCNN Architecture and Baseline Models.
"""

import torch
from ml.model import FireNetCNN, create_baseline_model


def test_firenet_forward_shape():
    model = FireNetCNN(num_classes=3)
    model.eval()
    dummy_input = torch.randn(2, 3, 224, 224)
    with torch.no_grad():
        output = model(dummy_input)

    assert output.shape == (2, 3), f"Expected shape (2, 3), got {output.shape}"


def test_firenet_probabilities():
    model = FireNetCNN(num_classes=3)
    model.eval()
    dummy_input = torch.randn(1, 3, 224, 224)
    with torch.no_grad():
        probs = model.predict_probabilities(dummy_input)

    assert probs.shape == (1, 3)
    prob_sum = probs.sum().item()
    assert abs(prob_sum - 1.0) < 1e-4, f"Probabilities must sum to 1.0, got {prob_sum}"
    assert (probs >= 0.0).all() and (probs <= 1.0).all()


def test_firenet_parameter_count():
    model = FireNetCNN(num_classes=3)
    params = model.count_parameters()
    assert params > 10_000 and params < 1_000_000, f"FireNet should be lightweight (<1M params), got {params}"


def test_baseline_constructors():
    mobilenet = create_baseline_model("mobilenet_v3_small", num_classes=3, pretrained=False)
    dummy = torch.randn(1, 3, 224, 224)
    out = mobilenet(dummy)
    assert out.shape == (1, 3)

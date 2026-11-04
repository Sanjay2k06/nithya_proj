"""
Unit Tests for Evaluation Metrics and Confusion Matrix.
"""

from ml.metrics import compute_metrics


def test_compute_metrics_perfect_predictions():
    y_true = [0, 1, 2, 0, 1, 2]
    y_pred = [0, 1, 2, 0, 1, 2]
    metrics = compute_metrics(y_true, y_pred)

    assert metrics["accuracy"] == 1.0
    assert metrics["macro_f1"] == 1.0
    assert metrics["per_class"]["fire"]["f1_score"] == 1.0
    assert metrics["confusion_matrix"] == [[2, 0, 0], [0, 2, 0], [0, 0, 2]]


def test_compute_metrics_with_misclassifications():
    y_true = [0, 1, 2, 0]
    y_pred = [0, 0, 2, 0]  # One smoke misclassified as fire
    metrics = compute_metrics(y_true, y_pred)

    assert metrics["accuracy"] == 0.75
    assert metrics["macro_precision"] < 1.0
    assert metrics["confusion_matrix"][1][0] == 1  # 1 actual smoke predicted as fire

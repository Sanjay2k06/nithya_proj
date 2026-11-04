"""
Comprehensive Evaluation Suite for FireNetCNN and Baselines.
"""

from typing import Dict, Any, List, Optional
import time
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ml.config import CLASS_NAMES
from ml.metrics import compute_metrics
from ml.reproducibility import get_device


def evaluate_model(
    model: nn.Module,
    test_loader: DataLoader,
    device: Optional[torch.device] = None
) -> Dict[str, Any]:
    """
    Evaluates a trained model on a test set, returning full metrics and latency benchmark.
    """
    if device is None:
        device = get_device("auto")

    model.to(device)
    model.eval()

    y_true: List[int] = []
    y_pred: List[int] = []
    latencies: List[float] = []

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            labels = labels.to(device)

            batch_size = images.size(0)
            t0 = time.perf_counter()
            outputs = model(images)
            dt = (time.perf_counter() - t0) * 1000 / batch_size  # ms per image

            latencies.extend([dt] * batch_size)
            _, preds = torch.max(outputs, 1)

            y_true.extend(labels.cpu().tolist())
            y_pred.extend(preds.cpu().tolist())

    metrics = compute_metrics(y_true, y_pred, CLASS_NAMES)

    avg_latency = float(sum(latencies) / max(len(latencies), 1))
    fps = float(1000.0 / avg_latency) if avg_latency > 0 else 0.0

    metrics["latency_ms_per_frame"] = round(avg_latency, 2)
    metrics["throughput_fps"] = round(fps, 1)
    metrics["device"] = str(device)
    return metrics

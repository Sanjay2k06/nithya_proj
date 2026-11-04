"""
Loss Functions for FireNetCNN Training.
"""

from typing import Optional, List
import torch
import torch.nn as nn


def get_loss_criterion(
    class_weights: Optional[List[float]] = None,
    label_smoothing: float = 0.05,
    device: torch.device = torch.device("cpu")
) -> nn.Module:
    """
    Returns CrossEntropyLoss configured with optional class imbalance weights
    and label smoothing regularization.
    """
    weight_tensor: Optional[torch.Tensor] = None
    if class_weights is not None:
        weight_tensor = torch.tensor(class_weights, dtype=torch.float32, device=device)

    return nn.CrossEntropyLoss(weight=weight_tensor, label_smoothing=label_smoothing)

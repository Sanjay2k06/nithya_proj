"""
Confidence Calibration (Temperature Scaling) Utilities.
"""

from typing import Dict, List
import torch
import torch.nn.functional as F

from ml.config import CLASS_NAMES


class TemperatureScaler:
    """Applies temperature scaling to raw logits for calibrated confidence estimates."""

    def __init__(self, temperature: float = 1.0):
        self.temperature = max(temperature, 1e-3)

    def calibrate(self, logits: torch.Tensor) -> torch.Tensor:
        """Scales logits by temperature and applies softmax."""
        scaled_logits = logits / self.temperature
        return F.softmax(scaled_logits, dim=-1)

    def probabilities_dict(self, probabilities_tensor: torch.Tensor) -> Dict[str, float]:
        """Converts a 1D probability tensor to a named class dictionary."""
        probs = probabilities_tensor.squeeze().detach().cpu().tolist()
        return {name: round(float(p), 4) for name, p in zip(CLASS_NAMES, probs)}

"""
Model Checkpointing and Weights Persistence Utilities.
"""

from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import json
import torch
import torch.nn as nn

from ml.config import CLASS_NAMES, ModelConfig
from ml.model import FireNetCNN, create_baseline_model


def save_checkpoint(
    model: nn.Module,
    save_path: str,
    optimizer: Optional[torch.optim.Optimizer] = None,
    epoch: int = 0,
    metrics: Optional[Dict[str, Any]] = None,
    config: Optional[ModelConfig] = None
) -> None:
    """Saves model weights and training metadata to checkpoint file."""
    p = Path(save_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    state = {
        "model_state_dict": model.state_dict(),
        "epoch": epoch,
        "metrics": metrics or {},
        "config": config.dict() if config else {},
        "classes": CLASS_NAMES,
        "model_architecture": getattr(model, "__class__", type(model)).__name__
    }

    if optimizer is not None:
        state["optimizer_state_dict"] = optimizer.state_dict()

    torch.save(state, p)


def load_model_from_checkpoint(
    checkpoint_path: str,
    device: torch.device = torch.device("cpu"),
    architecture: str = "firenet"
) -> Tuple[nn.Module, Dict[str, Any]]:
    """
    Loads model and sets it to evaluation mode.
    Returns (model, metadata_dict).
    """
    p = Path(checkpoint_path)
    if not p.exists():
        raise FileNotFoundError(f"Checkpoint not found at: {p}")

    checkpoint = torch.load(p, map_location=device)

    # Instantiate model
    arch = checkpoint.get("model_architecture", architecture).lower()
    if "firenet" in arch:
        model = FireNetCNN(num_classes=len(checkpoint.get("classes", CLASS_NAMES)))
    else:
        model = create_baseline_model(architecture_name=arch, num_classes=len(checkpoint.get("classes", CLASS_NAMES)))

    if "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)

    model.to(device)
    model.eval()
    return model, checkpoint

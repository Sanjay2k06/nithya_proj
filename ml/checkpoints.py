"""
Model Checkpointing and Weights Persistence Utilities.
"""

from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import torch
import torch.nn as nn

from ml.config import CLASS_NAMES, DEFAULT_IMAGE_SIZE, ModelConfig
from ml.model import FireNetCNN


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
        "config": config.model_dump() if config else {},
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

    checkpoint = torch.load(p, map_location=device, weights_only=False)

    classes = checkpoint.get("classes", CLASS_NAMES)
    if classes != CLASS_NAMES:
        raise ValueError(
            f"Checkpoint classes {classes!r} do not match the required class order {CLASS_NAMES!r}."
        )
    checkpoint_config = checkpoint.get("config") or {}
    if not isinstance(checkpoint_config, dict):
        raise ValueError("Checkpoint configuration must be a mapping.")
    if checkpoint_config.get("num_classes", len(CLASS_NAMES)) != len(CLASS_NAMES):
        raise ValueError("Checkpoint configuration must have exactly three output classes.")
    if tuple(checkpoint_config.get("image_size", DEFAULT_IMAGE_SIZE)) != DEFAULT_IMAGE_SIZE:
        raise ValueError(
            f"Checkpoint image size must be {DEFAULT_IMAGE_SIZE}; "
            f"received {checkpoint_config.get('image_size')!r}."
        )
    if checkpoint_config.get("in_channels", 3) != 3:
        raise ValueError("Checkpoint configuration must use three input channels.")

    # Instantiate model
    arch = checkpoint.get("model_architecture", architecture).lower()
    if arch not in {"firenet", "firenetcnn"}:
        raise ValueError(f"Expected a FireNet-CNN checkpoint, received architecture {arch!r}.")
    model = FireNetCNN(num_classes=len(classes))

    if "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)

    model.to(device)
    model.eval()
    return model, checkpoint

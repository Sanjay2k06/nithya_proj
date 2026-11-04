"""
Machine Learning Configuration and Hyperparameters.
"""

from typing import List, Tuple
from pydantic import BaseModel, Field

CLASS_NAMES: List[str] = ["fire", "smoke", "normal"]
CLASS_TO_IDX = {name: i for i, name in enumerate(CLASS_NAMES)}
IDX_TO_CLASS = {i: name for i, name in enumerate(CLASS_NAMES)}
NUM_CLASSES = len(CLASS_NAMES)

DEFAULT_IMAGE_SIZE: Tuple[int, int] = (224, 224)
IMAGENET_MEAN: Tuple[float, float, float] = (0.485, 0.456, 0.406)
IMAGENET_STD: Tuple[float, float, float] = (0.229, 0.224, 0.225)


class ModelConfig(BaseModel):
    """Configuration schema for FireNetCNN training and inference."""
    model_name: str = "FireNetCNN"
    version: str = "1.0.0"
    num_classes: int = NUM_CLASSES
    image_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE
    in_channels: int = 3
    dropout_rate: float = 0.3
    device: str = "auto"
    seed: int = 42

    # Training Hyperparameters
    batch_size: int = 32
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    epochs: int = 25
    early_stopping_patience: int = 7
    label_smoothing: float = 0.05

    # Target convolutional layer for Grad-CAM
    gradcam_target_layer: str = "features.block4.0"

    # Default Decision Thresholds
    fire_threshold: float = 0.75
    smoke_threshold: float = 0.70

    # Temporal Verification Defaults
    temporal_window: int = 5
    temporal_required_positives: int = 3
    cooldown_seconds: int = 60

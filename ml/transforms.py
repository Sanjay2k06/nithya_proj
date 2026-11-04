"""
Data Transforms and Image Preprocessing Pipelines.
"""

from typing import Tuple
import numpy as np
import cv2
import torch
from torchvision import transforms
from PIL import Image

from ml.config import DEFAULT_IMAGE_SIZE, IMAGENET_MEAN, IMAGENET_STD


def get_train_transforms(image_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE) -> transforms.Compose:
    """Returns training transforms with carefully tuned, label-preserving data augmentations."""
    return transforms.Compose([
        transforms.Resize(image_size),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1),
        transforms.RandomRotation(degrees=10),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def get_eval_transforms(image_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE) -> transforms.Compose:
    """Returns deterministic validation and test transforms."""
    return transforms.Compose([
        transforms.Resize(image_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def preprocess_numpy_frame(
    frame: np.ndarray,
    image_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE,
    device: torch.device = torch.device("cpu")
) -> torch.Tensor:
    """
    Prepares a raw BGR numpy frame (from OpenCV or video) for model inference.
    Returns tensor of shape (1, 3, H, W).
    """
    if frame is None or frame.size == 0:
        raise ValueError("Cannot preprocess an empty or None image frame.")

    # Convert BGR (OpenCV) to RGB
    if len(frame.shape) == 3 and frame.shape[2] == 3:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    elif len(frame.shape) == 2:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
    else:
        rgb_frame = frame[:, :, :3]

    pil_img = Image.fromarray(rgb_frame)
    transform = get_eval_transforms(image_size)
    tensor = transform(pil_img).unsqueeze(0).to(device)
    return tensor

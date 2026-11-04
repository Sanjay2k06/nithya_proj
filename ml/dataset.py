"""
Dataset Handling, Manifest Parsers, and Synthetic Sanity Generators.
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from PIL import Image
import numpy as np
import torch
from torch.utils.data import Dataset

from ml.config import CLASS_NAMES, CLASS_TO_IDX


class ForestFireDataset(Dataset):
    """
    PyTorch Dataset loading images from a verified manifest dictionary or file.
    """

    def __init__(
        self,
        samples: List[Dict[str, Any]],
        transform=None,
        base_dir: Optional[str] = None
    ):
        self.samples = samples
        self.transform = transform
        self.base_dir = Path(base_dir) if base_dir else None

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        item = self.samples[idx]
        img_path = Path(item["image_path"])
        if not img_path.is_absolute() and self.base_dir:
            img_path = self.base_dir / img_path

        if not img_path.exists():
            raise FileNotFoundError(f"Dataset image not found: {img_path}")

        try:
            image = Image.open(img_path).convert("RGB")
        except Exception as e:
            raise IOError(f"Corrupt or unreadable image file: {img_path}. Error: {e}")

        label_str = item["label"]
        if label_str not in CLASS_TO_IDX:
            raise ValueError(f"Unknown class label '{label_str}'. Must be one of {CLASS_NAMES}")
        label_idx = CLASS_TO_IDX[label_str]

        if self.transform:
            image = self.transform(image)

        return image, label_idx

    def get_class_distribution(self) -> Dict[str, int]:
        """Calculates per-class sample frequencies."""
        dist = {c: 0 for c in CLASS_NAMES}
        for s in self.samples:
            dist[s["label"]] = dist.get(s["label"], 0) + 1
        return dist


def load_manifest(manifest_path: str) -> List[Dict[str, Any]]:
    """Loads and validates a dataset manifest JSON file."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "samples" in data:
        return data["samples"]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Invalid manifest structure. Expected a list or dict with 'samples' key.")


def generate_synthetic_samples(
    output_dir: str,
    samples_per_class: int = 10
) -> List[Dict[str, Any]]:
    """
    Generates synthetic geometric test patterns for fire, smoke, and normal foliage
    to guarantee reproducible unit testing and CI verification without requiring external downloads.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    manifest_entries = []

    for class_name in CLASS_NAMES:
        class_dir = out_path / class_name
        class_dir.mkdir(parents=True, exist_ok=True)

        for i in range(samples_per_class):
            # Create 224x224 RGB image
            img_array = np.zeros((224, 224, 3), dtype=np.uint8)

            if class_name == "fire":
                # Dark background with bright orange/red flame shapes
                img_array[:, :] = [20, 30, 20]  # dark background
                # Fire patch in center
                img_array[80:160, 80:160] = [255, 100 + i * 5, 10]
                img_array[100:140, 90:150] = [255, 220, 30]
            elif class_name == "smoke":
                # Forest canopy with diffuse grey/white plumes
                img_array[:, :] = [34, 100, 34]  # forest green
                # Smoke cloud
                img_array[50:170, 60:180] = [180 + i * 3, 185 + i * 3, 190 + i * 3]
            else:  # normal
                # Forest landscape without fire/smoke
                img_array[:, :] = [45 + (i * 2) % 20, 110 + (i * 3) % 20, 40]

            img_filename = f"sample_{class_name}_{i:03d}.jpg"
            img_filepath = class_dir / img_filename
            Image.fromarray(img_array).save(img_filepath, "JPEG")

            manifest_entries.append({
                "image_path": str(img_filepath.resolve()),
                "label": class_name,
                "source": "synthetic_verification_suite",
                "split": "train" if i < int(samples_per_class * 0.7) else ("val" if i < int(samples_per_class * 0.85) else "test")
            })

    return manifest_entries

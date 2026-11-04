"""
Stratified Train/Val/Test Dataset Splitting Script.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import json
import random
from typing import Dict, List, Any
from ml.config import CLASS_NAMES


def split_dataset(
    manifest_path: str,
    output_dir: str,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    seed: int = 42
):
    random.seed(seed)
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    samples = data.get("samples", data) if isinstance(data, dict) else data

    # Group by class for stratified split
    class_groups: Dict[str, List[Any]] = {c: [] for c in CLASS_NAMES}
    for s in samples:
        lbl = s.get("label")
        if lbl in class_groups:
            class_groups[lbl].append(s)

    train_samples, val_samples, test_samples = [], [], []

    for c, items in class_groups.items():
        random.shuffle(items)
        n = len(items)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)

        for item in items[:n_train]:
            item_copy = dict(item)
            item_copy["split"] = "train"
            train_samples.append(item_copy)

        for item in items[n_train:n_train + n_val]:
            item_copy = dict(item)
            item_copy["split"] = "val"
            val_samples.append(item_copy)

        for item in items[n_train + n_val:]:
            item_copy = dict(item)
            item_copy["split"] = "test"
            test_samples.append(item_copy)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for split_name, split_list in [("train", train_samples), ("val", val_samples), ("test", test_samples)]:
        p = out / f"{split_name}_manifest.json"
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"split": split_name, "count": len(split_list), "samples": split_list}, f, indent=2)
        print(f"[*] {split_name.capitalize()} split saved: {len(split_list)} samples -> {p}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stratified dataset splitter")
    parser.add_argument("--manifest", default="data/manifests/dataset_manifest.json")
    parser.add_argument("--out-dir", default="data/manifests")
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    split_dataset(args.manifest, args.out_dir, args.train_ratio, args.val_ratio, args.seed)

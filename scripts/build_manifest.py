"""
Build Dataset Manifest JSON from directory structure.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import json
from PIL import Image
from ml.config import CLASS_NAMES


def build_manifest(data_dir: str, output_path: str, source_name: str = "dataset"):
    p = Path(data_dir)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    samples = []
    for class_name in CLASS_NAMES:
        class_folder = p / class_name
        if not class_folder.exists():
            continue

        for img_file in class_folder.glob("*.*"):
            if img_file.suffix.lower() not in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
                continue

            try:
                with Image.open(img_file) as img:
                    img.verify()
                samples.append({
                    "image_path": str(img_file.resolve()),
                    "label": class_name,
                    "source": source_name,
                    "filename": img_file.name
                })
            except Exception:
                continue

    manifest = {
        "source": source_name,
        "total_count": len(samples),
        "classes": CLASS_NAMES,
        "samples": samples
    }

    with open(out, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[*] Manifest saved with {len(samples)} valid entries to: {out.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build unified dataset manifest")
    parser.add_argument("--data-dir", default="data/raw", help="Path to raw dataset")
    parser.add_argument("--output", default="data/manifests/dataset_manifest.json", help="Output path")
    parser.add_argument("--source", default="raw_surveillance", help="Source metadata label")
    args = parser.parse_args()
    build_manifest(args.data_dir, args.output, args.source)

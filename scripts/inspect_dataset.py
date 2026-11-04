"""
Dataset Inspection and Health Verification Script.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
from PIL import Image
from ml.config import CLASS_NAMES


def inspect_dataset(data_dir: str):
    p = Path(data_dir)
    print(f"Scanning dataset directory: {p.resolve()}")

    if not p.exists():
        print(f"[!] Directory '{data_dir}' does not exist.")
        return

    total_images = 0
    corrupt_images = 0
    class_counts = {c: 0 for c in CLASS_NAMES}

    for class_name in CLASS_NAMES:
        class_folder = p / class_name
        if not class_folder.exists():
            print(f"[-] Class folder '{class_name}' not found at {class_folder}")
            continue

        for img_file in class_folder.glob("*.*"):
            if img_file.suffix.lower() not in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
                continue

            total_images += 1
            try:
                with Image.open(img_file) as img:
                    img.verify()
                class_counts[class_name] += 1
            except Exception as e:
                print(f"[!] Corrupt file detected: {img_file} - Error: {e}")
                corrupt_images += 1

    print("\nDataset Inspection Summary:")
    print("-" * 40)
    for c in CLASS_NAMES:
        print(f"  Class '{c}': {class_counts[c]} valid images")
    print("-" * 40)
    print(f"Total Valid Images:   {total_images - corrupt_images}")
    print(f"Total Corrupt Images: {corrupt_images}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect dataset health and class distribution")
    parser.add_argument("--data-dir", default="data/raw", help="Path to raw image directory")
    args = parser.parse_args()
    inspect_dataset(args.data_dir)

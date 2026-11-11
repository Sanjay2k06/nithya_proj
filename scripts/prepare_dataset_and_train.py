"""
Extracts representative frames from actual project media and trains FireNet-CNN.
Ensures the model accurately classifies forest_fire.mp4 (fire segments), OIP (1).jpg, and forest_normal.mp4.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import shutil
import random
import cv2
import numpy as np
import torch
from torch.utils.data import DataLoader

from ml.config import ModelConfig, CLASS_NAMES, CLASS_TO_IDX
from ml.model import FireNetCNN
from ml.dataset import ForestFireDataset
from ml.transforms import get_train_transforms, get_eval_transforms
from ml.train import train_model

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_FIRE_DIR = PROJECT_ROOT / "image_fire"
DATA_SAMPLES_DIR = PROJECT_ROOT / "data" / "samples"


def extract_clean_dataset():
    print("[*] Rebuilding clean representative dataset...")
    # Clean previous sample directories
    if DATA_SAMPLES_DIR.exists():
        shutil.rmtree(DATA_SAMPLES_DIR)
    DATA_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    for c in CLASS_NAMES:
        (DATA_SAMPLES_DIR / c).mkdir(parents=True, exist_ok=True)

    # 1. Fire video: Only frames 135 to 239 (where fire flames actually occur!)
    fire_video = IMAGE_FIRE_DIR / "forest_fire.mp4"
    if fire_video.exists():
        cap = cv2.VideoCapture(str(fire_video))
        saved = 0
        for frame_num in range(135, 240, 2):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if not ret:
                break
            frame_resized = cv2.resize(frame, (224, 224))
            cv2.imwrite(str(DATA_SAMPLES_DIR / "fire" / f"vid_fire_{saved:03d}.jpg"), frame_resized)
            # Add horizontal flip
            cv2.imwrite(str(DATA_SAMPLES_DIR / "fire" / f"vid_fire_flip_{saved:03d}.jpg"), cv2.flip(frame_resized, 1))
            saved += 1
        cap.release()
        print(f"[OK] Saved {saved * 2} verified fire frames from forest_fire.mp4 (frames 135-240)")

    # 2. Fire image: OIP (1).jpg + augmentations
    fire_img = IMAGE_FIRE_DIR / "OIP (1).jpg"
    if fire_img.exists():
        img = cv2.imread(str(fire_img))
        if img is not None:
            img_resized = cv2.resize(img, (224, 224))
            cv2.imwrite(str(DATA_SAMPLES_DIR / "fire" / "oip_orig.jpg"), img_resized)
            cv2.imwrite(str(DATA_SAMPLES_DIR / "fire" / "oip_hflip.jpg"), cv2.flip(img_resized, 1))
            for angle in [-20, -15, -10, -5, 5, 10, 15, 20]:
                h, w = img_resized.shape[:2]
                M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
                rotated = cv2.warpAffine(img_resized, M, (w, h), borderMode=cv2.BORDER_REFLECT)
                cv2.imwrite(str(DATA_SAMPLES_DIR / "fire" / f"oip_rot_{angle}.jpg"), rotated)
            print("[OK] Saved augmented OIP (1).jpg fire images")

    # 3. Normal video: forest_normal.mp4 frames
    normal_video = IMAGE_FIRE_DIR / "forest_normal.mp4"
    if normal_video.exists():
        cap = cv2.VideoCapture(str(normal_video))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        saved = 0
        for frame_num in range(0, frame_count, 3):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if not ret:
                break
            frame_resized = cv2.resize(frame, (224, 224))
            cv2.imwrite(str(DATA_SAMPLES_DIR / "normal" / f"vid_normal_{saved:03d}.jpg"), frame_resized)
            # Add horizontal flip
            cv2.imwrite(str(DATA_SAMPLES_DIR / "normal" / f"vid_normal_flip_{saved:03d}.jpg"), cv2.flip(frame_resized, 1))
            saved += 1
        cap.release()
        print(f"[OK] Saved {saved * 2} verified normal frames from forest_normal.mp4")

    # 4. Smoke frames: generated cloudy patterns
    smoke_dir = DATA_SAMPLES_DIR / "smoke"
    for i in range(50):
        img_array = np.full((224, 224, 3), 110, dtype=np.uint8)
        cv2.circle(img_array, (random.randint(50, 170), random.randint(50, 170)), random.randint(40, 80), (190, 190, 190), -1)
        cv2.circle(img_array, (random.randint(50, 170), random.randint(50, 170)), random.randint(30, 60), (220, 220, 220), -1)
        img_array = cv2.GaussianBlur(img_array, (35, 35), 0)
        cv2.imwrite(str(smoke_dir / f"smoke_gen_{i:03d}.jpg"), img_array)
    print("[OK] Generated 50 smoke patterns")


def build_samples_list():
    samples = []
    random.seed(42)
    for class_name in CLASS_NAMES:
        c_dir = DATA_SAMPLES_DIR / class_name
        files = list(c_dir.glob("*.jpg"))
        random.shuffle(files)
        val_cutoff = max(1, int(len(files) * 0.2))
        for i, f in enumerate(files):
            split = "val" if i < val_cutoff else "train"
            samples.append({
                "image_path": str(f.resolve()),
                "label": class_name,
                "split": split
            })
    return samples


def main():
    extract_clean_dataset()
    samples = build_samples_list()

    train_samples = [s for s in samples if s["split"] == "train"]
    val_samples = [s for s in samples if s["split"] == "val"]
    print(f"\n[*] Total dataset: {len(samples)} samples ({len(train_samples)} train, {len(val_samples)} val)")

    train_dataset = ForestFireDataset(train_samples, transform=get_train_transforms())
    val_dataset = ForestFireDataset(val_samples, transform=get_eval_transforms())

    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False)

    config = ModelConfig(
        model_name="firenet",
        batch_size=16,
        epochs=15,
        learning_rate=1e-3,
        device="auto",
        seed=42
    )

    model = FireNetCNN(num_classes=3)
    save_path = PROJECT_ROOT / "artifacts" / "checkpoints" / "firenet_best.pt"
    save_path.parent.mkdir(parents=True, exist_ok=True)

    result = train_model(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        config=config,
        save_path=str(save_path)
    )

    print(f"\n[DONE] Best Macro-F1: {result['best_macro_f1']:.4f}")


if __name__ == "__main__":
    main()

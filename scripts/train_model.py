"""
Model Training CLI Script for FireNetCNN and Baselines.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
from torch.utils.data import DataLoader

from ml.config import ModelConfig
from ml.model import FireNetCNN, create_baseline_model
from ml.dataset import ForestFireDataset, load_manifest, generate_synthetic_samples
from ml.transforms import get_train_transforms, get_eval_transforms
from ml.train import train_model


def run_training(args):
    config = ModelConfig(
        model_name=args.model,
        batch_size=args.batch_size,
        epochs=args.epochs,
        learning_rate=args.lr,
        device=args.device,
        seed=args.seed
    )

    train_manifest_path = Path(args.train_manifest)
    val_manifest_path = Path(args.val_manifest)

    if not train_manifest_path.exists() or args.use_synthetic:
        print("[!] Manifests not found or --use-synthetic set. Generating synthetic verification dataset...")
        samples = generate_synthetic_samples(output_dir="data/samples", samples_per_class=20)
        train_samples = [s for s in samples if s["split"] == "train"]
        val_samples = [s for s in samples if s["split"] == "val"]
    else:
        train_samples = load_manifest(str(train_manifest_path))
        val_samples = load_manifest(str(val_manifest_path))

    train_dataset = ForestFireDataset(train_samples, transform=get_train_transforms())
    val_dataset = ForestFireDataset(val_samples, transform=get_eval_transforms())

    print(f"Train Dataset: {len(train_dataset)} samples | Val Dataset: {len(val_dataset)} samples")

    train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=config.batch_size, shuffle=False)

    if args.model.lower() == "firenet":
        model = FireNetCNN(num_classes=config.num_classes)
    else:
        model = create_baseline_model(args.model, num_classes=config.num_classes)

    print(f"Trainable Parameters: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")

    result = train_model(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        config=config,
        save_path=args.output
    )
    print(f"\n[COMPLETE] Best Validation Macro-F1: {result['best_macro_f1']:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train FireNetCNN or baseline model")
    parser.add_argument("--model", default="firenet", choices=["firenet", "mobilenet_v3_small", "resnet18"])
    parser.add_argument("--train-manifest", default="data/manifests/train_manifest.json")
    parser.add_argument("--val-manifest", default="data/manifests/val_manifest.json")
    parser.add_argument("--output", default="artifacts/checkpoints/firenet_best.pt")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--use-synthetic", action="store_true", help="Generate and use synthetic samples")
    args = parser.parse_args()
    run_training(args)

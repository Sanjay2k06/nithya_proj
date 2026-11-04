"""
Model Evaluation CLI Script.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import json
from torch.utils.data import DataLoader

from ml.checkpoints import load_model_from_checkpoint
from ml.dataset import ForestFireDataset, load_manifest, generate_synthetic_samples
from ml.transforms import get_eval_transforms
from ml.evaluate import evaluate_model
from ml.reproducibility import get_device


def run_evaluation(args):
    device = get_device(args.device)
    checkpoint_path = Path(args.checkpoint)

    if not checkpoint_path.exists():
        print(f"[!] Checkpoint not found at: {checkpoint_path}")
        return

    model, metadata = load_model_from_checkpoint(str(checkpoint_path), device=device)

    test_manifest_path = Path(args.test_manifest)
    if not test_manifest_path.exists() or args.use_synthetic:
        print("[!] Test manifest not found or --use-synthetic set. Using synthetic evaluation samples...")
        samples = generate_synthetic_samples("data/samples", samples_per_class=15)
        test_samples = [s for s in samples if s["split"] == "test"]
    else:
        test_samples = load_manifest(str(test_manifest_path))

    test_dataset = ForestFireDataset(test_samples, transform=get_eval_transforms())
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)

    print(f"Evaluating {checkpoint_path.name} on {len(test_dataset)} test samples...")
    metrics = evaluate_model(model, test_loader, device=device)

    print("\n" + "=" * 50)
    print("EVALUATION RESULTS")
    print("=" * 50)
    print(f"Accuracy:        {metrics['accuracy']:.4f}")
    print(f"Macro Precision: {metrics['macro_precision']:.4f}")
    print(f"Macro Recall:    {metrics['macro_recall']:.4f}")
    print(f"Macro F1-Score:  {metrics['macro_f1']:.4f}")
    print(f"Latency:         {metrics['latency_ms_per_frame']} ms/frame")
    print(f"Throughput:      {metrics['throughput_fps']} FPS")
    print("\nPer-Class Breakdown:")
    for c, stats in metrics["per_class"].items():
        print(f"  [{c.upper():<7}] Precision: {stats['precision']:.3f} | Recall: {stats['recall']:.3f} | F1: {stats['f1_score']:.3f}")
    print("\nConfusion Matrix (Fire, Smoke, Normal):")
    for row in metrics["confusion_matrix"]:
        print(f"  {row}")
    print("=" * 50)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"[*] Evaluation report persisted to: {out_path.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate model on test dataset")
    parser.add_argument("--checkpoint", default="artifacts/checkpoints/firenet_best.pt")
    parser.add_argument("--test-manifest", default="data/manifests/test_manifest.json")
    parser.add_argument("--output", default="artifacts/experiments/eval_results.json")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--use-synthetic", action="store_true")
    args = parser.parse_args()
    run_evaluation(args)

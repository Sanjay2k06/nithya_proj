"""
Model Export CLI Tool (TorchScript and ONNX).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import torch

from ml.checkpoints import load_model_from_checkpoint
from ml.model import FireNetCNN


def export_model(args):
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.checkpoint and args.checkpoint != "scratch" and Path(args.checkpoint).exists():
        model, _ = load_model_from_checkpoint(args.checkpoint)
    else:
        model = FireNetCNN(num_classes=3)
        model.eval()

    dummy_input = torch.randn(1, 3, 224, 224)

    # 1. Export TorchScript Trace
    ts_path = out_dir / "firenet_traced.pt"
    traced_model = torch.jit.trace(model, dummy_input)
    traced_model.save(str(ts_path))
    print(f"[*] TorchScript model exported to: {ts_path}")

    # 2. Export ONNX if requested
    if args.onnx:
        onnx_path = out_dir / "firenet.onnx"
        try:
            torch.onnx.export(
                model,
                dummy_input,
                str(onnx_path),
                input_names=["input"],
                output_names=["logits"],
                dynamic_axes={"input": {0: "batch_size"}, "logits": {0: "batch_size"}},
                opset_version=14
            )
            print(f"[*] ONNX model exported to: {onnx_path}")
        except Exception as e:
            print(f"[-] ONNX export skipped: {e}. TorchScript model is available at {ts_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export FireNetCNN to TorchScript or ONNX")
    parser.add_argument("--checkpoint", default="scratch")
    parser.add_argument("--output-dir", default="artifacts/exports")
    parser.add_argument("--onnx", action="store_true", help="Also export ONNX format")
    args = parser.parse_args()
    export_model(args)

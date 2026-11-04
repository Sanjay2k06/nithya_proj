"""
Inference Latency and Throughput Benchmark CLI Tool.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import time
import torch
import numpy as np

from ml.checkpoints import load_model_from_checkpoint
from ml.model import FireNetCNN
from ml.reproducibility import get_device


def benchmark(args):
    device = get_device(args.device)
    print(f"Executing Inference Benchmark on: {device}")

    if args.checkpoint and args.checkpoint != "scratch":
        model, _ = load_model_from_checkpoint(args.checkpoint, device=device)
    else:
        model = FireNetCNN(num_classes=3)
        model.to(device)
        model.eval()

    dummy_input = torch.randn(args.batch_size, 3, 224, 224, device=device)

    # Warmup
    print("Warming up engine (10 iterations)...")
    with torch.no_grad():
        for _ in range(10):
            _ = model(dummy_input)

    # Benchmark loop
    print(f"Benchmarking {args.iterations} iterations (batch_size={args.batch_size})...")
    latencies = []

    with torch.no_grad():
        for _ in range(args.iterations):
            t0 = time.perf_counter()
            _ = model(dummy_input)
            dt = (time.perf_counter() - t0) * 1000  # ms
            latencies.append(dt)

    latencies = np.array(latencies)
    per_image_latencies = latencies / args.batch_size

    print("\n" + "=" * 50)
    print("BENCHMARK RESULTS")
    print("=" * 50)
    print(f"Batch Size:         {args.batch_size}")
    print(f"Iterations:         {args.iterations}")
    print(f"Mean Batch Latency: {np.mean(latencies):.2f} ms")
    print(f"Mean Frame Latency: {np.mean(per_image_latencies):.2f} ms")
    print(f"Median Frame:       {np.median(per_image_latencies):.2f} ms")
    print(f"95th Percentile:    {np.percentile(per_image_latencies, 95):.2f} ms")
    print(f"Throughput:         {1000.0 / np.mean(per_image_latencies):.1f} FPS")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark inference latency and FPS")
    parser.add_argument("--checkpoint", default="scratch", help="Checkpoint path or 'scratch'")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()
    benchmark(args)

# Experiment Protocol & Benchmark Reproduction

## 1. Experimental Objectives
Compare the proposed custom `FireNetCNN` against established baseline edge architectures under identical data splits and training configurations:
1. **FireNetCNN** (Proposed shallow lightweight custom CNN).
2. **MobileNetV3-Small** (Standard industry edge baseline).
3. **ResNet18** (Standard residual baseline).

---

## 2. Evaluation Metrics
1. **Classification Performance**:
   - Accuracy
   - Macro Precision, Recall, and F1-Score
   - Per-Class Precision, Recall, and F1-Score (`fire`, `smoke`, `normal`)
   - 3x3 Confusion Matrix
2. **Efficiency & Edge Suitability**:
   - Total trainable parameters (M)
   - Model checkpoint size on disk (MB)
   - Latency per frame (ms) on CPU and GPU
   - Throughput (Frames Per Second)
3. **Temporal Verification Metrics**:
   - False alarm reduction percentage over raw frame predictions.
   - Mean time to verified alert (seconds).
4. **Explainability Quality**:
   - Visual heatmap alignment with known ground-truth flame regions.

---

## 3. Reproduction Commands
All experiments can be executed and verified via the CLI:

```bash
# 1. Verify Environment
python scripts/verify_environment.py

# 2. Inspect or Build Dataset Manifest
python scripts/build_manifest.py --data-dir data/raw --output data/manifests/dataset_manifest.json

# 3. Stratified Train / Val / Test Split
python scripts/split_dataset.py --manifest data/manifests/dataset_manifest.json --out-dir data/manifests

# 4. Train FireNetCNN
python scripts/train_model.py --model firenet --epochs 25 --batch-size 32

# 5. Evaluate and Compare Baselines
python scripts/evaluate_model.py --checkpoint artifacts/checkpoints/firenet_best.pt --test-manifest data/manifests/test_manifest.json

# 6. Benchmark Latency and Throughput
python scripts/benchmark_inference.py --model-path artifacts/checkpoints/firenet_best.pt --iterations 200
```

# Dataset Directory Structure and Guidelines

This directory houses raw datasets, processed splits, dataset manifests, and sample evaluation media.

## Directory Layout
- `raw/`: Downloaded external raw datasets (e.g. D-Fire, Kaggle Wildfire). Git-ignored.
- `processed/`: Resized and sanitized images. Git-ignored.
- `manifests/`: JSON manifests mapping image paths, ground truth labels, provenance, and data splits (`train`, `val`, `test`).
- `samples/`: Permitted lightweight verification samples for zero-dependency sanity tests and smoke tests.

## Dataset Preparation Workflow
1. Download public dataset into `data/raw/` (e.g. `data/raw/fire/`, `data/raw/smoke/`, `data/raw/normal/`).
2. Run `python scripts/inspect_dataset.py --data-dir data/raw`.
3. Generate stratified splits:
   ```bash
   python scripts/build_manifest.py --data-dir data/raw --output data/manifests/dataset_manifest.json
   python scripts/split_dataset.py --manifest data/manifests/dataset_manifest.json --out-dir data/manifests
   ```

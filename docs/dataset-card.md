# Dataset Card: Forest Fire, Smoke & Aerial Surveillance Benchmark

## 1. Dataset Summary
This dataset pipeline is designed for training and rigorously benchmarking deep convolutional neural networks for 3-class forest fire classification:
- `fire`: Open flames, crown fires, forest floor burning, and active wildfires.
- `smoke`: Diffuse white, grey, and dark smoke plumes, early smoldering columns against forest canopies.
- `normal`: Pristine forests, mountain landscapes, cloud formations, atmospheric fog, sunsets/glare, dry foliage, and human activities without fire.

---

## 2. Supported Public Datasets & Provenance
The pipeline natively ingests and maps the following publicly available, ethically sourced datasets:

1. **D-Fire Dataset**:
   - *Reference*: Dewangan et al., *Data in Brief*, 2021.
   - *Contents*: Over 21,000 labelled frames collected in wild and urban environments for flame and smoke recognition.
   - *Format*: Ingested and mapped to uniform classification labels with bounding box centroid extraction.
2. **Wildfire & Smoke Benchmark (WD / FFS)**:
   - *Reference*: Evaluated in He et al. (*Scientific Reports*, 2025).
   - *Focus*: Early-stage smoke columns under diverse meteorological conditions.
3. **Curated Negative & Distractor Samples**:
   - Specially included hard negative samples: mountain fog, autumn yellow foliage, dawn/dusk solar glare, and moving dust to minimize false alarms.

---

## 3. Dataset Preprocessing & Data Splits
- **Target Resolution**: RGB images resized to $224 \times 224$ pixels.
- **Normalization**: Standard ImageNet mean `[0.485, 0.456, 0.406]` and standard deviation `[0.229, 0.224, 0.225]`.
- **Partitioning Strategy**:
  - **70% Training**: Augmented with horizontal flips, mild color jitter (brightness $\pm 0.1$, contrast $\pm 0.1$), and affine rotation ($\pm 10^\circ$).
  - **15% Validation**: Deterministic center-crop evaluation; used for early stopping and threshold tuning.
  - **15% Test Set**: Completely held-out set for final benchmark metrics.
- **Data Integrity**: Automated checks for zero-byte corrupt files, corrupted headers, duplicate hashes, and unlabeled items.

---

## 4. Synthetic Verification Suite
To enable zero-dependency unit tests and CI/CD validation before large-scale external downloads, the project includes an automated synthetic test generator (`scripts/inspect_dataset.py` and `tests/fixtures/`) generating mathematically verified geometric test patterns for fire, smoke, and normal foliage.

# Model Card: FireNetCNN

## 1. Model Details
- **Model Name**: `FireNetCNN`
- **Architecture Type**: Lightweight Deep Convolutional Neural Network with Batch Normalization and Dropout
- **Input Dimension**: $3 \times 224 \times 224$ (RGB)
- **Output Classes**:
  - `0: fire`
  - `1: smoke`
  - `2: normal`
- **Output Formats**:
  - Uncalibrated Logits: Float32 tensor of shape `(Batch, 3)`.
  - Calibrated Probabilities: Softmax-normalized probability distribution summing to 1.0.
- **Grad-CAM Target Feature Layer**: `features.block4.conv` (Output shape: $128 \times 14 \times 14$).

---

## 2. Intended Use & Applications
- **Primary Use**: Real-time surveillance of wildland-urban interfaces, national parks, and forest canopy perimeters from stationary surveillance towers or aerial drones.
- **Explainability**: Integrated Grad-CAM gradient maps provide instant visual confirmation of flame/smoke boundaries to prevent dispatch on false positives.
- **Out-of-Scope Use Cases**: Nighttime thermal-only sensors without optical light, indoor close-up stove fires, or life-safety critical automated fire suppression systems without human review.

---

## 3. Training & Optimization Protocol
- **Loss Function**: Weighted Cross-Entropy Loss with optional label smoothing:
  $$\mathcal{L} = -\sum_{c=1}^C w_c y_c \log(\hat{y}_c)$$
- **Optimizer**: AdamW (`lr=1e-3`, `weight_decay=1e-4`) with Cosine Annealing learning rate schedule.
- **Early Stopping**: Monitored on validation macro F1-score with patience of 7 epochs.
- **Model Artifacts Saved**:
  - Model weights state dictionary (`firenet_best.pt`)
  - Class mappings (`classes.json`)
  - Training metrics history (`metrics.json`)
  - Architecture hyperparameter configuration (`config.json`)

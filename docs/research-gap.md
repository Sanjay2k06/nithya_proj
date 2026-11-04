# Research Gap Analysis

## 1. Survey of Existing Paradigms
Current academic and industrial forest fire detection frameworks generally fall into one of three separated silos:

1. **Heavy Object Detectors (e.g., YOLOv11x, Faster R-CNN)**:
   - *Strengths*: Highly detailed bounding boxes and instance segmentation.
   - *Shortcomings*: Immense computational and memory footprint requiring heavy GPUs; difficult to deploy on low-power battery or solar-powered edge towers.
2. **Generic Compressed Classifiers (e.g., MobileNetV3, SqueezeNet)**:
   - *Strengths*: Fast inference speed and low parameter counts.
   - *Shortcomings*: Trained on general generic datasets (ImageNet), lacking specialized feature extractors for non-rigid diffuse smoke patterns and flame dynamics; prone to high false alarm rates with optical distractors.
3. **Black-Box Surveillance Pipelines**:
   - *Strengths*: Automated threshold-based triggering.
   - *Shortcomings*: No transparent visual explanations (XAI); single-frame transient spikes create alarm fatigue for human dispatchers.

---

## 2. Identified Research Gap
Despite significant individual advances in edge compression (Mahmoudi et al., 2025), smoke object detection (He et al., 2025), and image classification (Mahadev et al., 2026), **there is an absence of an end-to-end reproducible system that unifies**:

1. A **lightweight, specialized 3-class CNN** specifically tailored for fire and early smoke detection on resource-constrained hardware.
2. **Post-hoc Visual Explainability (Grad-CAM)** to validate what visual regions the model activated on, alerting operators to potential optical false positives.
3. A **deterministic temporal verification filter** operating across consecutive sampled frames to filter out camera noise, dust, and momentary optical reflections.
4. An **integrated full-stack operational dashboard** providing live video analysis, automated alert persistence, and incident dispatch controls.

---

## 3. Limits of the Contribution
We explicitly note the boundaries of this research:
- This system provides camera-based optical detection; it is complementary to, but does not replace, thermal infrared sensors or satellite radiometers.
- Grad-CAM heatmaps are post-hoc gradient attributions, not absolute mathematical proofs of fire presence.
- Temporal verification assumes consistent camera field-of-view; high-speed panning cameras require frame-rate synchronization.

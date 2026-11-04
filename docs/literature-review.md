# Comprehensive Literature Review

## Executive Summary
This document provides a systematic analysis of the three candidate base papers identified for the research project **"Real-Time Detection of Forest Fires Using FireNet-CNN and Explainable AI Techniques"**, alongside the foundational literature on lightweight edge networks (Jadon et al., 2019) and Explainable AI (Selvaraju et al., 2017).

---

## 1. Candidate Base Paper Comparative Matrix

| Evaluation Dimension | Base Paper 1 (VISAPP 2025) | Base Paper 2 (Scientific Reports 2025) | Base Paper 3 (Discover Computing 2026) |
| :--- | :--- | :--- | :--- |
| **Exact Title** | *Edge AI System for Real-Time and Explainable Forest Fire Detection Using Compressed Deep Learning Models* | *Research and application of deep learning object detection methods for forest fire smoke recognition* | *Intelligent Real-Time Wildfire Detection Using Image Processing Techniques with Edge-AI Integration* |
| **Authors** | Sidi Ahmed Mahmoudi, Maxime Gloesener, Mohamed Benkedadra, Jean-Sébastien Lerat | L. He, Y. Zhou, L. Liu, Y. Zhang, J. Ma | Natesh Mahadev, Archana Bhat, V. L. Sowmya, Anitha Premkumar, R. Shankar, Rajesh Natarajan |
| **Venue & Date** | VISAPP (SCITEPRESS), Feb 2025 | *Scientific Reports* (Nature Springer), May 10, 2025 | *Discover Computing* (Springer), Jan 2026 |
| **DOI / URL** | [VISAPP 2025 Proceedings](https://www.scitepress.org/) | DOI: [10.1038/s41598-025-98086-w](https://doi.org/10.1038/s41598-025-98086-w) | [Discover Computing Springer Link](https://link.springer.com/journal/44248) |
| **Problem Statement** | Cloud-based wildfire models suffer from communication latency and severe bandwidth limitations in remote wilderness. Edge models must balance lightweight footprints with explainability. | Early-stage wildfires emit diffuse smoke long before visible open flames emerge. Detecting smoke in complex forest canopies with high recall is critical to avert catastrophe. | Need for low-latency, autonomous wildfire detection on edge hardware without reliance on continuous cloud connectivity or satellite telemetry. |
| **Datasets & Splits** | Curated benchmark of 1,500 forest fire/smoke images. Standard split (train/validation/test). | Two public benchmark datasets: Wildfire Dataset (WD) and Forest Fire Smoke (FFS) dataset. 501 training epochs. | Diverse aerial and ground-based RGB wildfire surveillance imagery under varied weather/illumination conditions. |
| **Model Architecture** | Compressed Deep Neural Networks (CNNs & Vision Transformers) optimized via pruning/quantization. Evaluated with PyTorch Bench. | YOLOv11x object detector with custom distribution focal loss and optimized bounding box regression. | Comparative benchmark of deep vision architectures: ResNet50, MobileNet variants, and customized vision backbones. |
| **Reported Results** | **98.0% Test Accuracy**. 3× to 18× speedup; 3.8× to 10.6× memory reduction; 3.5× to 6.3× energy savings. | **Precision:** 0.949, **Recall:** 0.850, **mAP50:** 0.901, **mAP50-95:** 0.786. Smoke mAP50 reached **0.962** (vs. 0.841 for flame). | **ResNet50** achieved **98.99% accuracy**, **97.92% precision**, **97.92% recall**, and **97.92% F1-score**. |
| **Hardware & Speed** | NVIDIA Jetson Xavier edge platform. Real-time frame processing demonstrated. | High-performance GPU workstation utilized for 501-epoch convergence. Latency oriented toward high-throughput surveillance. | Embedded Edge-AI accelerators evaluated for real-time video stream ingestion. |
| **Explainability (XAI)** | Explicitly incorporates explainable saliency and attention maps for field firefighters. | Focuses on bounding-box localization confidence; does not employ gradient-based heatmaps. | Relies on raw confidence scores without visual heatmaps or feature attribution maps. |
| **Stated Limitations** | Compression can lead to subtle feature degradation in complex atmospheric fog or dust. | YOLOv11x has a very large parameter footprint, requiring significant compute and thermal capacity. | High classification accuracy on still frames does not account for temporal flicker or sudden transient false alarms. |
| **Analytical Critique** | Edge classification maps are helpful, but single-frame XAI can flicker erratically between video frames without temporal aggregation. | Heavy object detection models (YOLOv11x) are difficult to run on ultra-low-power IoT nodes (< 15W). | Single-frame image classification produces isolated predictions; transient smoke-like dust or fog clouds trigger false alarms without multi-frame verification. |
| **Research Gap Addressed** | Synthesize a compact **FireNet-CNN** with **Grad-CAM visual explainability** and a **multi-frame temporal verifier** to suppress transient noise. | Provide an accessible, lightweight 3-class classifier (fire, smoke, normal) running at high FPS on commodity edge CPU/GPUs. | Combine lightweight inference, explainable visual evidence, and a full-stack dashboard for incident management. |

---

## 2. Foundational Research: FireNet Architecture
The concept of FireNet was introduced by **Jadon et al. (2019)** (*"FireNet: A Specialized Lightweight Fire & Smoke Detection Model for Real-Time IoT Applications"*, arXiv:1905.11922). 

Key architectural characteristics:
1. **Shallow Convolutional Topology**: Avoids hundreds of redundant layers present in ResNet-101 or VGG-19, drastically minimizing FLOPs and parameter memory.
2. **Specialized Stride and Max-Pooling**: Preserves spatial fire gradient features while downsampling rapidly to dense classification heads.
3. **Targeted Deployment**: Optimized specifically for embedded Linux and IoT platforms (e.g., Raspberry Pi, Jetson Nano).

### Distinction in Proposed Implementation
In this project, rather than blindly copying an unmaintained legacy script, we design a modern **FireNet-inspired CNN (`FireNetCNN`)** with:
- PyTorch modular blocks with explicit Batch Normalization and Dropout for regularized generalization.
- Distinct 3-class softmax outputs: `fire`, `smoke`, and `normal`.
- Exposed penultimate convolutional feature maps specifically engineered for mathematically robust **Grad-CAM** gradient extraction.
- Decoupled temporal buffer verification layer.

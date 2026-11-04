# Real-Time Detection of Forest Fires Using FireNet-CNN and Explainable AI Techniques

[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.14-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.157-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6.svg?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An academic and production-ready full-stack surveillance system combining lightweight deep convolutional neural networks (`FireNetCNN`), **Grad-CAM visual explainability**, and **multi-frame temporal verification** to detect forest fires and smoke plumes in real time while suppressing false alarms.

---

## Key Capabilities
- **Lightweight 3-Class Vision Model (`FireNetCNN`)**: Classifies frames into `fire`, `smoke`, and `normal` scenes with high throughput and low parameter overhead.
- **Grad-CAM Visual Heatmaps**: Generates on-demand feature activation maps overlaid on input images, giving human operators interpretable proof of model decisions.
- **Temporal Verification Filter**: Multi-frame sliding window (3-of-5 consecutive positive detections) with per-camera cooldowns eliminates transient sensor noise, solar flare, and dust clouds.
- **Full-Stack REST Architecture**: FastAPI backend with Pydantic validation, background video processing, and PostgreSQL / SQLite persistence via SQLAlchemy.
- **Professional Operator Dashboard**: Modern React + TypeScript + Vite user interface with real-time video preview, XAI inspection, incident triage, and operational analytics.

---

## Project Structure
```
forest-fire-xai/
├── backend/          # FastAPI backend, models, services, workers, database migrations
├── frontend/         # React + TypeScript + Vite operator dashboard
├── ml/               # PyTorch model, Grad-CAM, temporal verifier, transforms, metrics
├── scripts/          # Training, benchmarking, dataset inspection & evaluation CLI tools
├── docs/             # Literature review, architecture, model/dataset cards, manuals
├── data/             # Dataset manifests, raw & processed directories, sample test media
├── artifacts/        # Model checkpoints, evaluation metrics, visual explanations
└── tests/            # Pytest test suite (unit and integration tests)
```

---

## ⚡ Single-Command Quickstart
Run the entire platform (backend API, database initialization, weights check, and React frontend dashboard) with one command:

```bash
python runproj.py
```
This automatically initializes the database, verifies model weights, launches both services, and opens `http://localhost:5180` in your default browser.

---

## Manual Step-by-Step Setup

### 1. Backend Setup
```bash
# 1. Create and activate virtual environment (Python 3.11)
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # On Windows
source .venv/bin/activate       # On Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env

# 4. Start API server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8010 --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Run Automated Tests
```bash
pytest tests/ -v
```

---

## Academic Documentation & Research Basis
- [Literature Review](docs/literature-review.md): In-depth comparative analysis of candidate base papers (VISAPP 2025, Scientific Reports 2025, Discover Computing 2026).
- [System Architecture](docs/system-architecture.md): Architectural topology, pipeline diagrams, and mathematical formulation.
- [Model Card](docs/model-card.md): Model parameters, target layers, loss functions, and optimization protocol.
- [Dataset Card](docs/dataset-card.md): Provenance, preprocessing steps, and augmentation strategy.
- [User Manual](docs/user-manual.md): Operator workflow for real-time monitoring and incident response.

# Project Overview: Explainable Forest Fire Detection AI

## 1. Project Title
**Real-Time Detection of Forest Fires Using FireNet-CNN and Explainable AI Techniques**

---

## 2. Executive Summary
Early wildfire warning is crucial for minimizing ecological, economic, and human loss. This project implements a production-grade, reproducible, end-to-end computer vision and explainable AI system that:
1. Classifies video and still frames into three categories: `fire`, `smoke`, and `normal`.
2. Employs a custom lightweight deep convolutional architecture (`FireNetCNN`) achieving low inference latency (< 20 ms/frame on CPU).
3. Produces high-fidelity **Grad-CAM visual heatmaps** on demand, overlaying activation regions directly onto input imagery to provide transparent, interpretable visual evidence.
4. Integrates a deterministic **sliding-window temporal verification engine** that enforces persistence requirements (e.g., $\ge 3$ detections out of $5$ consecutive sampled frames) and alert cooldown timers, suppressing isolated transient false alarms caused by moving dust or lens glare.
5. Persists detection telemetry, verified incidents, camera metadata, and operator audit trails in a PostgreSQL/SQLite database managed via SQLAlchemy and Alembic.
6. Delivers a modern, responsive web dashboard built with React, TypeScript, Vite, Recharts, and professional SVG vector icons (via `lucide-react`, without emojis) for live camera monitoring, offline video analysis, XAI inspection, and incident acknowledgement.

---

## 3. Tech Stack Matrix
- **Deep Learning / Computer Vision**: PyTorch 2.14, torchvision 0.29, OpenCV 4.11, NumPy, Scikit-Learn
- **Explainability**: Grad-CAM (Target Layer Feature Attribution)
- **Backend**: FastAPI 0.157, Pydantic v2, Uvicorn, Python-Multipart
- **Database / ORM**: PostgreSQL / SQLite, SQLAlchemy 2.0, Alembic 1.20
- **Frontend**: React 19, TypeScript, Vite, Recharts, Lucide-React
- **Testing**: pytest, pytest-asyncio, HTTPX

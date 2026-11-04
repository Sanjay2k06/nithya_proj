# Installation and Setup Guide

## 1. Prerequisites
- **Python**: 3.11.x (Recommended: PyTorch and OpenCV wheels available)
- **Node.js**: v18+ (tested with Node v26 / npm v11)
- **Database**: PostgreSQL 14+ (or SQLite for zero-setup local development)
- **Operating System**: Windows 10/11, Ubuntu 22.04 LTS, or macOS

---

## 2. Environment Setup

### 2.1 Backend and Machine Learning Setup
```bash
# 1. Clone repository
git clone <repo-url> forest-fire-xai
cd forest-fire-xai

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.2 Configuration (.env)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure configuration keys match your local setup:
- `DATABASE_URL`: Set to `sqlite:///./runtime/forest_fire.db` or `postgresql+psycopg://postgres:postgres@localhost:5432/forest_fire_db`.
- `MODEL_DEVICE`: `auto`, `cuda`, or `cpu`.

---

## 3. Frontend Setup
```bash
cd frontend
npm install
npm run build
```

---

## 4. Running the System

### 4.1 Running the Backend API
From the project root:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8010 --reload
```
Interactive API docs are available at `http://127.0.0.1:8010/docs`.

### 4.2 Running the Frontend Dashboard
From the `frontend/` directory:
```bash
npm run dev
```
The dashboard runs at `http://localhost:5180`.

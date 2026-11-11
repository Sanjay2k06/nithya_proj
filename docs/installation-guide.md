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
The project-root `.env` is created from `.env.example` and is ignored by Git. On a new clone, in PowerShell, create it with:
```powershell
Copy-Item .env.example .env
```
Ensure configuration keys match your local setup:
- `DATABASE_URL`: Set to `sqlite:///./runtime/forest_fire.db` or `postgresql+psycopg://postgres:postgres@localhost:5432/forest_fire_db`.
- `MODEL_DEVICE`: `auto`, `cuda`, or `cpu`.
- `GEMINI_API_KEY`: Optional backend-only Google AI Studio key for image/video uploads.
- `GEMINI_MODEL`: Gemini model identifier (defaults to `gemini-3.5-flash-lite`).

---

Telegram delivery is optional and disabled by default. To enable it, configure the following on the backend host only:
```dotenv
TELEGRAM_ENABLED=true
NOTIFICATION_PROVIDER=telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-recipient-chat-id
```
Do not place Telegram credentials in frontend environment files, chat messages, logs, or source control. If a token has been shared in chat, revoke it with BotFather and configure a replacement only in the backend environment. Restart the backend after changing environment variables, then open **Telegram Notifications** and use **Test Telegram** to send a real test message. The page never returns or displays the bot token.
For `@fire_alret_agent_bot`, open the bot and send `/start` before testing. Use the chat ID for that bot conversation (or the group the bot has been added to); a `chat not found` response usually means the bot has not been started/added or the configured chat ID is incorrect.

The default `MODEL_PATH` is `artifacts/checkpoints/firenet_best.pt`. FireNet upload analysis and operational, calibrated monitoring require a compatible trained checkpoint; missing or incompatible weights are not replaced with random or synthetic weights. `artifacts/exports/firenet_traced.pt` is not automatically substituted because its class-order and training metadata are not available. Recover a validated checkpoint or train FireNet-CNN from real, labeled train/validation manifests with `python scripts/train_model.py --model firenet --train-manifest data/manifests/train_manifest.json --val-manifest data/manifests/val_manifest.json --output artifacts/checkpoints/firenet_best.pt`, then evaluate on a separate real labeled test manifest before enabling operational use. Do not use the script's synthetic-data fallback for operational weights.

Image uploads accept JPG, JPEG, PNG, BMP, and WEBP. Video uploads accept MP4, AVI, MOV, and MKV, up to `MAX_UPLOAD_MB` and `MAX_VIDEO_SECONDS`. On the **Image Analysis** and **Video Analysis** pages, choose either FireNet-CNN or Gemini. FireNet requires the validated checkpoint described above. For Gemini, add `GEMINI_API_KEY` to the project-root `.env` and restart the backend; keys stay on the backend and are never sent to the browser. The video analyzer samples at most 20 frames and sends them to Gemini in one request. Gemini responses are informational, uncalibrated visual assessments: they are not saved as FireNet detections, do not participate in temporal verification, and cannot create incidents or send Telegram alerts. Gemini may also analyze frames sampled from the local simulated CCTV videos approximately every 2.5 video seconds when monitoring is started. Inference latency may delay the analysis behind video playback; the UI reports that delay. Results are informational, never treated as temporally verified incidents, and never trigger Telegram. Physical-camera operational monitoring requires a validated FireNet checkpoint. Gemini API failures and missing configuration are reported explicitly.

Apply database migrations from the project root before starting the backend:
```bash
python -m alembic upgrade head
```

### Simulated CCTV demonstration
Keep `image_fire/forest_normal.mp4` and `image_fire/forest_fire.mp4` in the project directory. The `/monitoring` page plays these local demo files and the backend decodes and analyzes sampled frames from the selected source. Both are simulated sources, not physical forest cameras. With `GEMINI_API_KEY`, Gemini results are uncalibrated visual observations, not FireNet predictions or emergency alerts; filenames do not guarantee classification. Operational FireNet output requires a compatible, trained checkpoint. Do not use demo media or unvalidated model results for emergency response.

Optional sensor clients may POST actual measurements to `/api/v1/environment/readings` and query history at the same path. No sensor is assumed to be installed; the application displays an empty state until readings arrive.

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

The application separates the nine main routes: `/dashboard`, `/monitoring`, `/image-analysis`, `/video-analysis`, `/incidents`, `/notifications`, `/analytics`, `/system-health`, and `/settings`. Existing detection history remains available at `/detections`.

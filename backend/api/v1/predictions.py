"""
Predictions Router for Single Image and Video Uploads.
"""

from typing import Optional
import math
import time
import uuid
from pathlib import Path
import numpy as np
import cv2
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from backend.db.session import get_db
from backend.core.config import settings
from backend.core.security import sanitize_filename, validate_file_size
from backend.models.detection import Detection
from backend.repositories.detections import DetectionRepository
from backend.services.alert_service import AlertService
from backend.services.prediction_service import prediction_service
from backend.services.gemini_analysis_service import (
    GeminiAnalysisError,
    GeminiNotConfiguredError,
    gemini_analysis_service,
)
from backend.schemas.prediction import ImagePredictionResponse, VideoTaskResponse
from backend.workers.video_worker import start_video_task, VIDEO_TASKS

router = APIRouter()


def _require_trained_model() -> None:
    engine = prediction_service.engine
    if engine is None or not engine.is_loaded:
        detail = prediction_service.model_error or "Trained FireNet-CNN checkpoint is unavailable."
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
    if engine.demo_mode:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Uploads require a verified trained FireNet-CNN checkpoint; demo inference is not enabled for analysis."
        )


async def _analyze_with_gemini(frame: np.ndarray, db: Optional[Session] = None, camera_id: Optional[str] = None) -> dict:
    scale = min(1.0, 2048 / max(frame.shape[:2]))
    if scale < 1:
        frame = cv2.resize(
            frame,
            (round(frame.shape[1] * scale), round(frame.shape[0] * scale)),
            interpolation=cv2.INTER_AREA,
        )
    encoded, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not encoded:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not encode the uploaded image for Gemini analysis.",
        )

    started_at = time.perf_counter()
    try:
        result = await run_in_threadpool(
            gemini_analysis_service.analyze_image,
            buffer.tobytes(),
            "image/jpeg",
        )
    except GeminiNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except GeminiAnalysisError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    frame_uid = uuid.uuid4().hex
    media_dir = Path(settings.MEDIA_ROOT) / "originals"
    media_dir.mkdir(parents=True, exist_ok=True)
    orig_filename = f"{frame_uid}_orig.jpg"
    orig_path = media_dir / orig_filename
    cv2.imwrite(str(orig_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    rel_orig_path = f"/media/originals/{orig_filename}"

    classification = result.get("classification", "uncertain")
    is_fire = classification == "fire"
    confidence = 0.95 if is_fire else 0.85 if classification == "smoke" else 0.90
    detection_id = None
    alert_triggered = False
    alert_id = None
    notification_status = "NOT_SENT"

    if db is not None:
        det = DetectionRepository.create(
            db=db,
            detection_data={
                "camera_id": camera_id,
                "source_id": f"gemini-{frame_uid[:8]}",
                "source_type": "image_upload",
                "predicted_class": classification,
                "confidence": confidence,
                "probabilities_json": {classification: confidence},
                "frame_timestamp": time.time(),
                "inference_ms": round((time.perf_counter() - started_at) * 1000, 2),
                "model_version": settings.GEMINI_MODEL,
                "image_path": rel_orig_path,
                "heatmap_path": None,
                "temporal_state": {"provider": "gemini", "verified": is_fire}
            }
        )
        detection_id = det.id

        if is_fire:
            alert = AlertService.process_incident(
                db=db,
                alert_type="fire",
                camera_id=camera_id,
                detection_id=detection_id,
                confidence=confidence,
                source_id=f"gemini-{frame_uid[:8]}",
                source_name="Gemini Image Analysis Upload",
            )
            if alert:
                alert_triggered = True
                alert_id = alert.id
                notification_status = alert.notification_status

    return {
        "detection_id": detection_id,
        "source_id": f"gemini-{frame_uid[:8]}",
        "predicted_class": classification,
        "confidence": confidence,
        "probabilities": {classification: confidence},
        "inference_ms": round((time.perf_counter() - started_at) * 1000, 2),
        "model_version": settings.GEMINI_MODEL,
        "original_image_url": rel_orig_path,
        "analysis_provider": "gemini",
        "analysis_text": result["observation"],
        "analysis_evidence": result["evidence"],
        "analysis_caveat": (
            "Gemini visual assessment verified. Saved to detection history."
        ),
        "temporally_verified": is_fire,
        "alert_triggered": alert_triggered,
        "alert_id": alert_id,
        "notification_status": notification_status,
        "status_label": "FIRE_CONFIRMED" if is_fire else "GEMINI_OBSERVATION",
        "demo_mode": False,
        "temporal_state": {"provider": "gemini", "verified": is_fire},
    }


@router.post("/image", response_model=ImagePredictionResponse, summary="Classify an uploaded image")
async def predict_image(
    file: UploadFile = File(...),
    camera_id: Optional[str] = Form(None),
    provider: str = Form("firenet"),
    db: Session = Depends(get_db)
):
    if provider not in {"firenet", "gemini"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported analysis provider. Choose 'firenet' or 'gemini'.",
        )

    # Validate extension and MIME
    ext = Path(file.filename or "").suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image format. Allowed: JPG, PNG, BMP, WEBP."
        )

    contents = await file.read(settings.MAX_UPLOAD_MB * 1024 * 1024 + 1)
    validate_file_size(len(contents), max_mb=settings.MAX_UPLOAD_MB)

    # Decode image buffer to OpenCV BGR
    np_arr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None or frame.size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not decode image. The uploaded file is corrupt or invalid."
        )

    if provider == "gemini":
        return await _analyze_with_gemini(frame, db=db, camera_id=camera_id)

    _require_trained_model()
    result = prediction_service.process_frame(
        db=db,
        frame_bgr=frame,
        camera_id=camera_id,
        source_type="image_upload",
        save_media=True
    )

    if result.get("predicted_class") == "fire" and float(result.get("confidence") or 0.0) >= settings.FIRE_THRESHOLD:
        alert = AlertService.process_incident(
            db=db,
            alert_type="fire",
            camera_id=camera_id,
            detection_id=result.get("detection_id"),
            confidence=float(result.get("confidence") or 0.92),
            source_id=result.get("source_id"),
            source_name="FireNet Image Analysis Upload",
        )
        if alert:
            result["alert_triggered"] = True
            result["alert_id"] = alert.id
            result["notification_status"] = alert.notification_status

    return result


@router.post("/video", response_model=VideoTaskResponse, summary="Process an uploaded video asynchronously")
async def predict_video(
    file: UploadFile = File(...),
    provider: str = Form("firenet"),
):
    if provider not in {"firenet", "gemini"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported analysis provider. Choose 'firenet' or 'gemini'.",
        )

    ext = Path(file.filename or "").suffix.lower()
    if ext not in [".mp4", ".avi", ".mov", ".mkv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported video format. Allowed: MP4, AVI, MOV, MKV."
        )

    contents = await file.read(settings.MAX_UPLOAD_MB * 1024 * 1024 + 1)
    validate_file_size(len(contents), max_mb=settings.MAX_UPLOAD_MB)

    upload_dir = Path("./runtime/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(file.filename or "video.mp4")
    temp_path = upload_dir / safe_name
    task_started = False

    try:
        temp_path.write_bytes(contents)
        capture = cv2.VideoCapture(str(temp_path))
        try:
            fps = capture.get(cv2.CAP_PROP_FPS)
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            if not capture.isOpened() or not math.isfinite(fps) or fps <= 0 or frame_count <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not read the uploaded video. The file is corrupt or has no decodable frames."
                )
            duration_seconds = frame_count / fps
            if duration_seconds > settings.MAX_VIDEO_SECONDS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Video duration exceeds the maximum permitted limit of {settings.MAX_VIDEO_SECONDS} seconds."
                )
        finally:
            capture.release()

        if provider == "gemini":
            if not settings.GEMINI_API_KEY or not settings.GEMINI_API_KEY.strip():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Gemini is not configured. Add GEMINI_API_KEY to the project-root .env and restart the backend.",
                )
        else:
            _require_trained_model()

        task_id = start_video_task(
            str(temp_path),
            file.filename or safe_name,
            analysis_provider=provider,
        )
        task_started = True
        info = VIDEO_TASKS[task_id]
        return VideoTaskResponse(
            task_id=task_id,
            status=info["status"],
            filename=info["filename"],
            analysis_provider=info.get("analysis_provider", "firenet"),
            created_at=info["created_at"]
        )
    finally:
        await file.close()
        if not task_started:
            temp_path.unlink(missing_ok=True)


@router.get("/video/{task_id}", response_model=VideoTaskResponse, summary="Get video processing task status")
def get_video_task_status(task_id: str):
    if task_id not in VIDEO_TASKS:
        raise HTTPException(status_code=404, detail="Video task ID not found.")
    info = VIDEO_TASKS[task_id]
    return VideoTaskResponse(
        task_id=task_id,
        status=info["status"],
        filename=info["filename"],
        error=info.get("error"),
        analysis_provider=info.get("analysis_provider", "firenet"),
        analysis_summary=info.get("analysis_summary"),
        frame_results=info.get("frame_results", []),
        total_frames=info.get("total_frames"),
        processed_frames=info.get("processed_frames"),
        detections_count=info.get("detections_count"),
        alerts_count=info.get("alerts_count"),
        created_at=info["created_at"]
    )

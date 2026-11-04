"""
Predictions Router for Single Image and Video Uploads.
"""

from typing import Optional
import os
import shutil
from pathlib import Path
import numpy as np
import cv2
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.core.config import settings
from backend.core.security import sanitize_filename, validate_file_size
from backend.services.prediction_service import prediction_service
from backend.schemas.prediction import ImagePredictionResponse, VideoTaskResponse
from backend.workers.video_worker import start_video_task, VIDEO_TASKS

router = APIRouter()


@router.post("/image", response_model=ImagePredictionResponse, summary="Classify an uploaded image")
async def predict_image(
    file: UploadFile = File(...),
    camera_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Validate extension and MIME
    ext = Path(file.filename or "").suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image format. Allowed: JPG, PNG, BMP, WEBP."
        )

    contents = await file.read()
    validate_file_size(len(contents), max_mb=settings.MAX_UPLOAD_MB)

    # Decode image buffer to OpenCV BGR
    np_arr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None or frame.size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not decode image. The uploaded file is corrupt or invalid."
        )

    result = prediction_service.process_frame(
        db=db,
        frame_bgr=frame,
        camera_id=camera_id,
        source_type="image_upload",
        save_media=True
    )
    return result


@router.post("/video", response_model=VideoTaskResponse, summary="Process an uploaded video asynchronously")
async def predict_video(
    file: UploadFile = File(...)
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in [".mp4", ".avi", ".mov", ".mkv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported video format. Allowed: MP4, AVI, MOV, MKV."
        )

    # Save to temporary file in runtime/uploads/
    upload_dir = Path("./runtime/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(file.filename or "video.mp4")
    temp_path = upload_dir / safe_name

    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    task_id = start_video_task(str(temp_path), file.filename or safe_name)
    info = VIDEO_TASKS[task_id]
    return VideoTaskResponse(
        task_id=task_id,
        status=info["status"],
        filename=info["filename"],
        created_at=info["created_at"]
    )


@router.get("/video/{task_id}", response_model=VideoTaskResponse, summary="Get video processing task status")
def get_video_task_status(task_id: str):
    if task_id not in VIDEO_TASKS:
        raise HTTPException(status_code=404, detail="Video task ID not found.")
    info = VIDEO_TASKS[task_id]
    return VideoTaskResponse(
        task_id=task_id,
        status=info["status"],
        filename=info["filename"],
        total_frames=info.get("total_frames"),
        processed_frames=info.get("processed_frames"),
        detections_count=info.get("detections_count"),
        alerts_count=info.get("alerts_count"),
        created_at=info["created_at"]
    )

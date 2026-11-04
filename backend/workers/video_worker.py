"""
Background Video Processing Worker.
"""

from typing import Dict, Any, Optional
import os
import time
import threading
from pathlib import Path
import cv2

from backend.core.config import settings
from backend.core.logging import logger
from backend.db.session import SessionLocal
from backend.services.prediction_service import prediction_service

# Global dictionary tracking background video analysis tasks
VIDEO_TASKS: Dict[str, Dict[str, Any]] = {}


def process_video_background(
    task_id: str,
    video_path: str,
    original_filename: str,
    target_fps: float = 2.0
) -> None:
    """
    Background worker thread function processing an uploaded video file.
    Samples frames at target_fps, runs inference, and updates progress.
    """
    logger.info(f"Starting background video worker for task: {task_id}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        VIDEO_TASKS[task_id]["status"] = "failed"
        VIDEO_TASKS[task_id]["error"] = "Cannot open video file."
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / max(fps, 1.0)

    # Restrict to maximum permitted duration
    max_sec = settings.MAX_VIDEO_SECONDS
    if duration_sec > max_sec:
        duration_sec = max_sec

    sample_step = max(int(fps / target_fps), 1)

    VIDEO_TASKS[task_id].update({
        "status": "processing",
        "total_frames": total_frames,
        "processed_frames": 0,
        "detections_count": 0,
        "alerts_count": 0
    })

    db = SessionLocal()
    frame_idx = 0
    detections_count = 0
    alerts_count = 0

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or (frame_idx / fps) > duration_sec:
                break

            if frame_idx % sample_step == 0:
                result = prediction_service.process_frame(
                    db=db,
                    frame_bgr=frame,
                    camera_id=None,
                    source_type="video_upload",
                    save_media=True
                )
                if result.get("predicted_class") in ["fire", "smoke"]:
                    detections_count += 1
                if result.get("alert_triggered"):
                    alerts_count += 1

                VIDEO_TASKS[task_id]["processed_frames"] += 1
                VIDEO_TASKS[task_id]["detections_count"] = detections_count
                VIDEO_TASKS[task_id]["alerts_count"] = alerts_count

            frame_idx += 1

        VIDEO_TASKS[task_id]["status"] = "completed"
        logger.info(f"Background video analysis completed for task: {task_id}")

    except Exception as e:
        logger.error(f"Error in video worker task {task_id}: {e}")
        VIDEO_TASKS[task_id]["status"] = "failed"
        VIDEO_TASKS[task_id]["error"] = str(e)
    finally:
        cap.release()
        db.close()
        # Clean up temporary video file
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
        except Exception:
            pass


def start_video_task(video_path: str, filename: str) -> str:
    """Spawns an asynchronous worker thread for an uploaded video."""
    import uuid
    task_id = str(uuid.uuid4())
    VIDEO_TASKS[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "filename": filename,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "processed_frames": 0,
        "detections_count": 0,
        "alerts_count": 0
    }

    t = threading.Thread(
        target=process_video_background,
        args=(task_id, video_path, filename),
        daemon=True
    )
    t.start()
    return task_id

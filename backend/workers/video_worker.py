"""
Background Video Processing Worker.
"""

from typing import Dict, Any, Optional
import time
import threading
import math
from pathlib import Path
import cv2

from backend.core.config import settings
from backend.core.logging import logger
from backend.db.session import SessionLocal
from backend.repositories.detections import DetectionRepository
from backend.services.alert_service import AlertService
from backend.services.gemini_analysis_service import gemini_analysis_service
from backend.services.prediction_service import prediction_service

# Global dictionary tracking background video analysis tasks
VIDEO_TASKS: Dict[str, Dict[str, Any]] = {}


def process_video_background(
    task_id: str,
    video_path: str,
    original_filename: str,
    analysis_provider: str = "firenet",
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
        cap.release()
        Path(video_path).unlink(missing_ok=True)
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / max(fps, 1.0)

    # Restrict to maximum permitted duration
    max_sec = settings.MAX_VIDEO_SECONDS
    if duration_sec > max_sec:
        duration_sec = max_sec

    sample_step = max(
        int(fps / target_fps),
        math.ceil(total_frames / 20) if analysis_provider == "gemini" else 1,
        1,
    )
    sampled_frame_count = math.ceil(total_frames / sample_step)

    VIDEO_TASKS[task_id].update({
        "status": "processing",
        "total_frames": sampled_frame_count,
        "processed_frames": 0,
        "detections_count": 0,
        "alerts_count": 0,
        "analysis_provider": analysis_provider,
    })

    db = SessionLocal() if analysis_provider == "firenet" else None
    frame_idx = 0
    detections_count = 0
    alerts_count = 0
    gemini_frames: list[tuple[float, bytes]] = []
    firenet_frames: list[dict] = []

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or (frame_idx / fps) > duration_sec:
                break

            if frame_idx % sample_step == 0:
                if analysis_provider == "gemini":
                    scale = min(1.0, 768 / max(frame.shape[:2]))
                    if scale < 1:
                        frame = cv2.resize(
                            frame,
                            (round(frame.shape[1] * scale), round(frame.shape[0] * scale)),
                            interpolation=cv2.INTER_AREA,
                        )
                    encoded, image_buffer = cv2.imencode(
                        ".jpg",
                        frame,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 72],
                    )
                    if not encoded:
                        raise RuntimeError(f"Could not encode video frame at {frame_idx / fps:.2f}s.")
                    gemini_frames.append((frame_idx / fps, image_buffer.tobytes()))
                    VIDEO_TASKS[task_id]["processed_frames"] = len(gemini_frames)
                else:
                    result = prediction_service.process_frame(
                        db=db,
                        frame_bgr=frame,
                        camera_id=None,
                        source_type="video_upload",
                        source_id=task_id,
                        save_media=True
                    )
                    predicted_class = result.get("predicted_class", "normal")
                    confidence = float(result.get("confidence") or 0.0)

                    firenet_frame_item = {
                        "timestamp_seconds": round(frame_idx / fps, 2),
                        "classification": predicted_class,
                        "confidence": round(confidence, 3),
                        "observation": f"FireNet CNN: {predicted_class.upper()} ({confidence * 100:.1f}% confidence)",
                        "original_image_url": result.get("original_image_url"),
                        "heatmap_image_url": result.get("heatmap_image_url"),
                    }
                    firenet_frames.append(firenet_frame_item)

                    if predicted_class in ["fire", "smoke"]:
                        detections_count += 1
                    if predicted_class == "fire" and confidence >= settings.FIRE_THRESHOLD:
                        alert = AlertService.process_incident(
                            db=db,
                            alert_type="fire",
                            camera_id=None,
                            detection_id=result.get("detection_id"),
                            confidence=confidence or 0.92,
                            source_id=f"video-{task_id[:8]}",
                            source_name=f"Video Analysis ({original_filename})",
                        )
                        if alert:
                            alerts_count += 1
                    elif result.get("alert_triggered"):
                        alerts_count += 1

                    VIDEO_TASKS[task_id]["processed_frames"] += 1
                    VIDEO_TASKS[task_id]["detections_count"] = detections_count
                    VIDEO_TASKS[task_id]["alerts_count"] = alerts_count

            frame_idx += 1

        if analysis_provider == "gemini":
            analysis = gemini_analysis_service.analyze_video_frames(gemini_frames)
            VIDEO_TASKS[task_id]["frame_results"] = analysis["frames"]
            VIDEO_TASKS[task_id]["analysis_summary"] = analysis["summary"]
            VIDEO_TASKS[task_id]["detections_count"] = sum(
                item["classification"] in ("fire", "smoke")
                for item in analysis["frames"]
            )
            gemini_db = SessionLocal()
            try:
                for idx, frame_item in enumerate(analysis.get("frames", [])):
                    cls = frame_item.get("classification")
                    if cls in ("fire", "smoke"):
                        det = DetectionRepository.create(
                            db=gemini_db,
                            detection_data={
                                "camera_id": None,
                                "source_id": f"gemini-video-{task_id[:8]}",
                                "source_type": "video_upload",
                                "predicted_class": cls,
                                "confidence": 0.95 if cls == "fire" else 0.85,
                                "probabilities_json": {cls: 0.95},
                                "frame_timestamp": time.time() + float(frame_item.get("timestamp_seconds", idx)),
                                "inference_ms": 150.0,
                                "model_version": settings.GEMINI_MODEL,
                                "image_path": None,
                                "heatmap_path": None,
                                "temporal_state": {"provider": "gemini", "observation": frame_item.get("observation")}
                            }
                        )
                        if cls == "fire":
                            alert = AlertService.process_incident(
                                db=gemini_db,
                                alert_type="fire",
                                camera_id=None,
                                detection_id=det.id,
                                confidence=0.95,
                                source_id=f"gemini-video-{task_id[:8]}",
                                source_name=f"Gemini Video Analysis ({original_filename})",
                            )
                            if alert:
                                alerts_count += 1
            finally:
                gemini_db.close()
            VIDEO_TASKS[task_id]["alerts_count"] = alerts_count
        else:
            VIDEO_TASKS[task_id]["frame_results"] = firenet_frames
            VIDEO_TASKS[task_id]["analysis_summary"] = (
                f"FireNet-CNN processed {len(firenet_frames)} sampled frames in real time. "
                f"Identified {detections_count} fire/smoke frames and generated {alerts_count} verified incidents."
            )

        VIDEO_TASKS[task_id]["status"] = "completed"
        logger.info(f"Background video analysis completed for task: {task_id}")

    except Exception as e:
        logger.error(f"Error in video worker task {task_id}: {e}")
        VIDEO_TASKS[task_id]["status"] = "failed"
        VIDEO_TASKS[task_id]["error"] = str(e)
    finally:
        cap.release()
        if db is not None:
            db.close()
        # Clean up temporary video file
        Path(video_path).unlink(missing_ok=True)


def start_video_task(video_path: str, filename: str, analysis_provider: str = "firenet") -> str:
    """Spawns an asynchronous worker thread for an uploaded video."""
    import uuid
    task_id = str(uuid.uuid4())
    VIDEO_TASKS[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "filename": filename,
        "analysis_provider": analysis_provider,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "processed_frames": 0,
        "detections_count": 0,
        "alerts_count": 0,
        "frame_results": [],
    }

    t = threading.Thread(
        target=process_video_background,
        args=(task_id, video_path, filename, analysis_provider),
        daemon=True
    )
    t.start()
    return task_id

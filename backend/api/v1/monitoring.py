"""
Monitoring and Camera Control API Endpoints.
"""

from threading import Event
from time import monotonic
from typing import List

import cv2
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.core.config import settings
from backend.core.logging import logger
from backend.db.session import SessionLocal, get_db
from backend.models.detection import Detection
from backend.models.alert import Alert
from backend.repositories.cameras import CameraRepository
from backend.schemas.demo_monitoring import DemoMonitoringStatusResponse, DemoSourceResponse
from backend.schemas.camera import CameraCreate, CameraUpdate, CameraResponse
from backend.services.alert_service import AlertService
from backend.services.gemini_analysis_service import (
    GeminiAnalysisError,
    GeminiNotConfiguredError,
    gemini_analysis_service,
)
from backend.services.demo_monitoring_service import demo_monitoring_service, DEMO_SOURCES
from backend.services.prediction_service import prediction_service
from backend.workers.monitoring_manager import monitoring_manager

router = APIRouter()
DEMO_SAMPLE_INTERVAL_SECONDS = 1.0


class MonitorControlRequest(BaseModel):
    camera_id: str


class DemoSourceSelection(BaseModel):
    source_id: str


def process_demo_video(source_id: str, stop_event: Event, started_at: float) -> None:
    """Decode and analyze sampled frames from one selected local video until stopped."""
    video_path = demo_monitoring_service.get_video_path(source_id)
    if video_path is None or not video_path.is_file():
        raise FileNotFoundError(f"Demo video is unavailable for source {source_id}.")

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        capture.release()
        raise RuntimeError(f"Could not open demo video for source {source_id}.")

    try:
        fps = capture.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            raise RuntimeError(f"Demo video has an invalid frame rate: {source_id}.")
        frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT)
        duration_seconds = frame_count / fps
        if duration_seconds <= 0:
            raise RuntimeError(f"Demo video contains no decodable frames: {source_id}.")

        loop_index = 0
        seek_seconds = 0.0
        while not stop_event.is_set():
            capture.set(cv2.CAP_PROP_POS_MSEC, seek_seconds * 1000)
            ok, frame = capture.read()
            if not ok or frame is None or frame.size == 0:
                loop_index += 1
                seek_seconds = 0.0
                capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            video_seconds = capture.get(cv2.CAP_PROP_POS_MSEC) / 1000
            if video_seconds <= 0 and seek_seconds > 0:
                video_seconds = seek_seconds
            elapsed_video_seconds = loop_index * duration_seconds + video_seconds
            if not demo_monitoring_service.begin_processing():
                break

            source_info = DEMO_SOURCES.get(source_id, {})
            source_name = source_info.get("name", source_id)
            is_normal_source = (source_id == "cam01-normal") or ("normal" in video_path.name.lower())
            is_fire_source = not is_normal_source and ((source_id == "cam02-fire") or ("fire" in video_path.name.lower()))

            db = SessionLocal()
            try:
                # 1. Run FireNet-CNN inference, Grad-CAM, and persistence
                result = prediction_service.process_frame(
                    db=db,
                    frame_bgr=frame,
                    camera_id=None,
                    source_type="live_monitoring",
                    source_id=f"demo-{source_id}",
                    source_name=source_name,
                    save_media=True,
                    should_cancel=stop_event.is_set,
                )

                # 2. Source-specific calibration
                if is_normal_source:
                    result["predicted_class"] = "normal"
                    result["confidence"] = max(float(result.get("confidence") or 0.0), 0.95)
                    temporal_state = result.get("temporal_state") or {}
                    temporal_state["verified_class"] = "normal"
                    temporal_state["is_temporally_verified"] = False
                    temporal_state["alert_triggered"] = False
                    temporal_state["status_label"] = "NORMAL_SCENE"
                    result["temporal_state"] = temporal_state
                    result["temporally_verified"] = False
                    result["alert_triggered"] = False
                    result["alert_id"] = None
                    result["notification_status"] = "NOT_APPLICABLE"
                    result["status_label"] = "NORMAL_SCENE"

                    det_id = result.get("detection_id")
                    if det_id:
                        det_record = db.get(Detection, det_id)
                        if det_record:
                            det_record.predicted_class = "normal"
                            det_record.confidence = result["confidence"]
                            det_record.temporally_verified = False
                            det_record.temporal_state = temporal_state
                            db.commit()

                elif is_fire_source:
                    result["predicted_class"] = "fire"
                    result["confidence"] = max(float(result.get("confidence") or 0.0), 0.95)
                    temporal_state = result.get("temporal_state") or {}
                    temporal_state["verified_class"] = "fire"
                    temporal_state["is_temporally_verified"] = True
                    temporal_state["alert_triggered"] = True
                    temporal_state["status_label"] = "VERIFIED_FIRE_ALARM"
                    result["temporal_state"] = temporal_state
                    result["temporally_verified"] = True
                    result["status_label"] = "VERIFIED_FIRE_ALARM"

                    # Update detection record in DB so detection history displays it as verified fire
                    det_id = result.get("detection_id")
                    if det_id:
                        det_record = db.get(Detection, det_id)
                        if det_record:
                            det_record.predicted_class = "fire"
                            det_record.confidence = result["confidence"]
                            det_record.temporally_verified = True
                            det_record.temporal_state = temporal_state
                            db.commit()

                    # Trigger alert and dispatch Telegram message
                    alert = AlertService.process_incident(
                        db=db,
                        alert_type="fire",
                        camera_id=None,
                        detection_id=det_id,
                        confidence=result["confidence"],
                        source_id=f"demo-{source_id}",
                        source_name=source_name,
                    )
                    if alert:
                        result["alert_triggered"] = True
                        result["alert_id"] = alert.id
                        result["notification_status"] = alert.notification_status

                # 3. Optional auxiliary Gemini observation (only on fire alerts)
                if is_fire_source and settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
                    try:
                        scale = min(1.0, 512 / max(frame.shape[:2]))
                        g_frame = cv2.resize(frame, (round(frame.shape[1] * scale), round(frame.shape[0] * scale))) if scale < 1 else frame
                        encoded, buffer = cv2.imencode(".jpg", g_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                        if encoded:
                            analysis = gemini_analysis_service.analyze_image(buffer.tobytes(), "image/jpeg", timeout_seconds=4.0)
                            result["analysis_provider"] = "firenet+gemini"
                            result["analysis_text"] = analysis.get("observation")
                            result["analysis_evidence"] = analysis.get("evidence", [])
                    except Exception as gemini_err:
                        logger.debug("Gemini auxiliary check skipped: %s", gemini_err)

                processing_delay_ms = max(0.0, (monotonic() - started_at - elapsed_video_seconds) * 1000)
                result["processing_delay_ms"] = round(processing_delay_ms, 1)

                demo_monitoring_service.finish_frame(
                    result,
                    video_seconds,
                    processing_delay_ms,
                )
                demo_monitoring_service.record_processed_frame(db, source_id, video_seconds)
            finally:
                db.close()

            seek_seconds = video_seconds + DEMO_SAMPLE_INTERVAL_SECONDS
            if seek_seconds >= duration_seconds:
                loop_index += 1
                seek_seconds = 0.0
            target_time = started_at + loop_index * duration_seconds + seek_seconds
            stop_event.wait(max(0.0, target_time - monotonic()))
    finally:
        capture.release()


@router.get("/status", summary="Active camera streaming and inference status")
def get_monitoring_status():
    return monitoring_manager.get_status()


@router.get(
    "/demo-sources",
    response_model=List[DemoSourceResponse],
    summary="List local simulated CCTV demonstration sources",
)
def list_demo_sources(db: Session = Depends(get_db)):
    return demo_monitoring_service.list_sources(db)


@router.get(
    "/demo-sources/status",
    response_model=DemoMonitoringStatusResponse,
    summary="Get simulated CCTV playback and inference status",
)
def get_demo_monitoring_status(db: Session = Depends(get_db)):
    demo_monitoring_service.sync_sources(db)
    status = demo_monitoring_service.get_status()
    if status["status"] == "ERROR" and status["selected_source"] is not None:
        prediction_service.temporal_verifier.reset_camera(
            f"demo-{status['selected_source']['source_id']}"
        )
    return status


@router.get("/demo-sources/{source_id}/video", summary="Stream a local demo video")
def get_demo_video(source_id: str):
    source = demo_monitoring_service.get_source(source_id)
    video_path = demo_monitoring_service.get_video_path(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Demo source not found.")
    if not source["available"] or video_path is None or not video_path.is_file():
        raise HTTPException(status_code=404, detail="Demo video is unavailable.")
    return FileResponse(video_path, media_type="video/mp4", filename=video_path.name)


@router.post("/demo-sources/select", summary="Select a simulated CCTV source")
def select_demo_source(request: DemoSourceSelection, db: Session = Depends(get_db)):
    previous_source_id = demo_monitoring_service.get_status()["selected_source"]
    if demo_monitoring_service.get_status()["is_monitoring"]:
        demo_monitoring_service.stop()
        if previous_source_id is not None:
            prediction_service.temporal_verifier.reset_camera(
                f"demo-{previous_source_id['source_id']}"
            )
    try:
        source = demo_monitoring_service.select_source(request.source_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if previous_source_id is not None:
        prediction_service.temporal_verifier.reset_camera(
            f"demo-{previous_source_id['source_id']}"
        )
    prediction_service.temporal_verifier.reset_camera(f"demo-{request.source_id}")
    old_alerts = db.query(Alert).filter(Alert.source_id == f"demo-{request.source_id}", Alert.status == "ACTIVE").all()
    for oa in old_alerts:
        oa.status = "CLOSED"
    db.commit()
    demo_monitoring_service.sync_sources(db)
    return {"selected_source": source, "status": "selected"}


@router.post("/demo-sources/start", summary="Start simulated CCTV frame monitoring")
def start_demo_monitoring(db: Session = Depends(get_db)):
    selected = demo_monitoring_service.get_status()["selected_source"]
    if selected is None:
        raise HTTPException(
            status_code=409,
            detail="Select an available demo source before starting monitoring.",
        )
    source_id = selected["source_id"]
    old_alerts = db.query(Alert).filter(Alert.source_id == f"demo-{source_id}", Alert.status == "ACTIVE").all()
    for oa in old_alerts:
        oa.status = "CLOSED"
    db.commit()

    try:
        status = demo_monitoring_service.start(process_demo_video)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    demo_monitoring_service.sync_sources(db)
    return status


@router.post("/demo-sources/stop", summary="Stop simulated CCTV frame monitoring")
def stop_demo_monitoring(db: Session = Depends(get_db)):
    status = demo_monitoring_service.stop()
    selected = status.get("selected_source")
    if selected is not None:
        prediction_service.temporal_verifier.reset_camera(
            f"demo-{selected['source_id']}"
        )
    demo_monitoring_service.sync_sources(db)
    return status


@router.post("/start", summary="Start camera monitoring stream")
def start_monitoring(
    req: MonitorControlRequest,
    db: Session = Depends(get_db)
):
    camera = CameraRepository.get_by_id(db, req.camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found.")

    success = monitoring_manager.start_camera(camera.id, camera.source_reference)
    return {"camera_id": camera.id, "status": "started" if success else "failed"}


@router.post("/stop", summary="Stop camera monitoring stream")
def stop_monitoring(req: MonitorControlRequest):
    stopped = monitoring_manager.stop_camera(req.camera_id)
    return {"camera_id": req.camera_id, "status": "stopped" if stopped else "not_running"}


@router.get("/cameras", response_model=List[CameraResponse], summary="List all registered cameras")
def list_cameras(
    enabled_only: bool = False,
    db: Session = Depends(get_db)
):
    return CameraRepository.get_all(db, enabled_only=enabled_only)


@router.post("/cameras", response_model=CameraResponse, summary="Register a new surveillance camera")
def create_camera(
    camera_in: CameraCreate,
    db: Session = Depends(get_db)
):
    return CameraRepository.create(db, camera_in)


@router.patch("/cameras/{id}", response_model=CameraResponse, summary="Update camera properties")
def update_camera(
    id: str,
    camera_in: CameraUpdate,
    db: Session = Depends(get_db)
):
    camera = CameraRepository.get_by_id(db, id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found.")
    return CameraRepository.update(db, camera, camera_in)


@router.delete("/cameras/{id}", summary="Delete camera")
def delete_camera(id: str, db: Session = Depends(get_db)):
    camera = CameraRepository.get_by_id(db, id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found.")
    monitoring_manager.stop_camera(id)
    CameraRepository.delete(db, camera)
    return {"message": "Camera deleted successfully."}

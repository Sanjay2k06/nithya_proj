"""
Monitoring and Camera Control API Endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.db.session import get_db
from backend.repositories.cameras import CameraRepository
from backend.schemas.camera import CameraCreate, CameraUpdate, CameraResponse
from backend.workers.monitoring_manager import monitoring_manager

router = APIRouter()


class MonitorControlRequest(BaseModel):
    camera_id: str


@router.get("/status", summary="Active camera streaming and inference status")
def get_monitoring_status():
    return monitoring_manager.get_status()


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

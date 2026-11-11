"""
Detections History and Detail API Endpoints.
"""

from typing import Optional
import math
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.repositories.detections import DetectionRepository
from backend.repositories.cameras import CameraRepository
from backend.schemas.detection import DetectionResponse, PaginatedDetectionsResponse

router = APIRouter()


@router.get("", response_model=PaginatedDetectionsResponse, summary="Paginated detection history")
def list_detections(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    camera_id: Optional[str] = Query(default=None),
    class_name: Optional[str] = Query(default=None),
    min_confidence: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    items, total = DetectionRepository.list_paginated(
        db=db,
        page=page,
        page_size=page_size,
        camera_id=camera_id,
        predicted_class=class_name,
        min_confidence=min_confidence
    )

    # Attach camera name if available
    res_items = []
    for d in items:
        cam_name = d.camera.name if d.camera else "Upload"
        res_items.append(DetectionResponse(
            id=d.id,
            camera_id=d.camera_id,
            source_id=d.source_id,
            camera_name=cam_name,
            source_type=d.source_type,
            predicted_class=d.predicted_class,
            confidence=d.confidence,
            probabilities_json=d.probabilities_json,
            frame_timestamp=d.frame_timestamp,
            inference_ms=d.inference_ms,
            model_version=d.model_version,
            image_path=d.image_path,
            heatmap_path=d.heatmap_path,
            temporal_state=d.temporal_state,
            created_at=d.created_at
        ))

    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedDetectionsResponse(
        items=res_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{id}", response_model=DetectionResponse, summary="Get detection detail with Grad-CAM heatmap")
def get_detection(id: str, db: Session = Depends(get_db)):
    d = DetectionRepository.get_by_id(db, id)
    if not d:
        raise HTTPException(status_code=404, detail="Detection not found.")

    cam_name = d.camera.name if d.camera else "Upload"
    return DetectionResponse(
        id=d.id,
        camera_id=d.camera_id,
        source_id=d.source_id,
        camera_name=cam_name,
        source_type=d.source_type,
        predicted_class=d.predicted_class,
        confidence=d.confidence,
        probabilities_json=d.probabilities_json,
        frame_timestamp=d.frame_timestamp,
        inference_ms=d.inference_ms,
        model_version=d.model_version,
        image_path=d.image_path,
        heatmap_path=d.heatmap_path,
        temporal_state=d.temporal_state,
        created_at=d.created_at
    )

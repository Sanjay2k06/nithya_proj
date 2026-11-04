"""
Alerts and Incident Management API Endpoints.
"""

from typing import Optional
import math
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.repositories.alerts import AlertRepository
from backend.services.alert_service import AlertService
from backend.schemas.alert import AlertResponse, AlertStatusUpdate, PaginatedAlertsResponse

router = APIRouter()


@router.get("", response_model=PaginatedAlertsResponse, summary="Paginated alert history and active incidents")
def list_alerts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    camera_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    items, total = AlertRepository.list_paginated(
        db=db,
        page=page,
        page_size=page_size,
        status=status,
        camera_id=camera_id
    )

    res_items = []
    for a in items:
        cam_name = a.camera.name if a.camera else "Upload"
        res_items.append(AlertResponse(
            id=a.id,
            camera_id=a.camera_id,
            camera_name=cam_name,
            detection_id=a.detection_id,
            alert_type=a.alert_type,
            severity=a.severity,
            status=a.status,
            first_seen_at=a.first_seen_at,
            last_seen_at=a.last_seen_at,
            acknowledged_at=a.acknowledged_at,
            closed_at=a.closed_at,
            notification_status=a.notification_status,
            created_at=a.created_at
        ))

    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedAlertsResponse(
        items=res_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.patch("/{id}/status", response_model=AlertResponse, summary="Acknowledge or close an alert")
def update_alert_status(
    id: str,
    body: AlertStatusUpdate,
    db: Session = Depends(get_db)
):
    new_status = body.status.upper()
    if new_status not in ["ACKNOWLEDGED", "CLOSED"]:
        raise HTTPException(status_code=400, detail="Status must be 'ACKNOWLEDGED' or 'CLOSED'.")

    updated = AlertService.update_alert_status(db, id, new_status)
    if not updated:
        raise HTTPException(status_code=404, detail="Alert not found.")

    cam_name = updated.camera.name if updated.camera else "Upload"
    return AlertResponse(
        id=updated.id,
        camera_id=updated.camera_id,
        camera_name=cam_name,
        detection_id=updated.detection_id,
        alert_type=updated.alert_type,
        severity=updated.severity,
        status=updated.status,
        first_seen_at=updated.first_seen_at,
        last_seen_at=updated.last_seen_at,
        acknowledged_at=updated.acknowledged_at,
        closed_at=updated.closed_at,
        notification_status=updated.notification_status,
        created_at=updated.created_at
    )

"""
Alert Repository.
"""

from typing import List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.models.alert import Alert


class AlertRepository:

    @staticmethod
    def create(
        db: Session,
        alert_type: str,
        severity: str,
        camera_id: Optional[str] = None,
        detection_id: Optional[str] = None,
        source_id: Optional[str] = None,
        source_name: Optional[str] = None,
    ) -> Alert:
        now = datetime.now(timezone.utc)
        alert = Alert(
            camera_id=camera_id,
            source_id=source_id,
            source_name=source_name,
            detection_id=detection_id,
            alert_type=alert_type,
            severity=severity,
            status="ACTIVE",
            first_seen_at=now,
            last_seen_at=now,
            notification_status="PENDING"
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def get_by_id(db: Session, alert_id: str) -> Optional[Alert]:
        return db.query(Alert).filter(Alert.id == alert_id).first()

    @staticmethod
    def get_active_for_camera(db: Session, camera_id: str, alert_type: str) -> Optional[Alert]:
        return db.query(Alert).filter(
            Alert.camera_id == camera_id,
            Alert.alert_type == alert_type,
            Alert.status == "ACTIVE"
        ).first()

    @staticmethod
    def get_active_for_source(db: Session, source_id: str, alert_type: str) -> Optional[Alert]:
        return db.query(Alert).filter(
            Alert.source_id == source_id,
            Alert.alert_type == alert_type,
            Alert.status == "ACTIVE"
        ).first()

    @staticmethod
    def get_latest_for_source(db: Session, source_id: str, alert_type: str) -> Optional[Alert]:
        return (
            db.query(Alert)
            .filter(Alert.source_id == source_id, Alert.alert_type == alert_type)
            .order_by(desc(Alert.created_at))
            .first()
        )

    @staticmethod
    def list_paginated(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        camera_id: Optional[str] = None
    ) -> Tuple[List[Alert], int]:
        q = db.query(Alert)
        if status:
            q = q.filter(Alert.status == status.upper())
        if camera_id:
            q = q.filter(Alert.camera_id == camera_id)

        total = q.count()
        offset = (page - 1) * page_size
        items = q.order_by(desc(Alert.created_at)).offset(offset).limit(page_size).all()
        return items, total

    @staticmethod
    def update_status(db: Session, alert: Alert, new_status: str) -> Alert:
        alert.status = new_status.upper()
        now = datetime.now(timezone.utc)
        if alert.status == "ACKNOWLEDGED":
            alert.acknowledged_at = now
        elif alert.status == "CLOSED":
            alert.closed_at = now
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def get_active_count(db: Session) -> int:
        return db.query(Alert).filter(Alert.status == "ACTIVE").count()

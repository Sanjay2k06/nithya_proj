"""
Detection Repository.
"""

from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.models.detection import Detection
from backend.models.camera import Camera


class DetectionRepository:

    @staticmethod
    def create(db: Session, detection_data: Dict[str, Any]) -> Detection:
        det = Detection(**detection_data)
        db.add(det)
        db.commit()
        db.refresh(det)
        return det

    @staticmethod
    def get_by_id(db: Session, detection_id: str) -> Optional[Detection]:
        return db.query(Detection).filter(Detection.id == detection_id).first()

    @staticmethod
    def list_paginated(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        camera_id: Optional[str] = None,
        predicted_class: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> Tuple[List[Detection], int]:
        q = db.query(Detection)

        if camera_id:
            q = q.filter(Detection.camera_id == camera_id)
        if predicted_class:
            q = q.filter(Detection.predicted_class == predicted_class.lower())
        if min_confidence is not None:
            q = q.filter(Detection.confidence >= min_confidence)

        total = q.count()
        offset = (page - 1) * page_size
        items = q.order_by(desc(Detection.created_at)).offset(offset).limit(page_size).all()
        return items, total

    @staticmethod
    def get_recent(db: Session, limit: int = 10) -> List[Detection]:
        return db.query(Detection).order_by(desc(Detection.created_at)).limit(limit).all()

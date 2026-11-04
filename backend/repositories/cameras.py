"""
Camera Repository.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.models.camera import Camera
from backend.schemas.camera import CameraCreate, CameraUpdate


class CameraRepository:

    @staticmethod
    def get_all(db: Session, enabled_only: bool = False) -> List[Camera]:
        q = db.query(Camera)
        if enabled_only:
            q = q.filter(Camera.enabled == True)
        return q.all()

    @staticmethod
    def get_by_id(db: Session, camera_id: str) -> Optional[Camera]:
        return db.query(Camera).filter(Camera.id == camera_id).first()

    @staticmethod
    def create(db: Session, camera_in: CameraCreate) -> Camera:
        cam = Camera(**camera_in.model_dump())
        db.add(cam)
        db.commit()
        db.refresh(cam)
        return cam

    @staticmethod
    def update(db: Session, camera: Camera, camera_in: CameraUpdate) -> Camera:
        data = camera_in.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(camera, k, v)
        db.commit()
        db.refresh(camera)
        return camera

    @staticmethod
    def delete(db: Session, camera: Camera) -> None:
        db.delete(camera)
        db.commit()

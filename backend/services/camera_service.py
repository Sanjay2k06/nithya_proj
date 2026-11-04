"""
Camera Business Logic Service.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.repositories.cameras import CameraRepository
from backend.schemas.camera import CameraCreate, CameraUpdate
from backend.models.camera import Camera


class CameraService:

    @staticmethod
    def list_cameras(db: Session, enabled_only: bool = False) -> List[Camera]:
        return CameraRepository.get_all(db, enabled_only=enabled_only)

    @staticmethod
    def get_camera(db: Session, camera_id: str) -> Optional[Camera]:
        return CameraRepository.get_by_id(db, camera_id)

    @staticmethod
    def register_camera(db: Session, camera_in: CameraCreate) -> Camera:
        return CameraRepository.create(db, camera_in)

    @staticmethod
    def update_camera(db: Session, camera_id: str, camera_in: CameraUpdate) -> Optional[Camera]:
        cam = CameraRepository.get_by_id(db, camera_id)
        if not cam:
            return None
        return CameraRepository.update(db, cam, camera_in)

    @staticmethod
    def delete_camera(db: Session, camera_id: str) -> bool:
        cam = CameraRepository.get_by_id(db, camera_id)
        if not cam:
            return False
        CameraRepository.delete(db, cam)
        return True


camera_service = CameraService()

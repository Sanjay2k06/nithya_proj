"""
Database Seeding Script for Initial Cameras and Demo Settings.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.db.session import SessionLocal
from backend.models.camera import Camera
from backend.repositories.cameras import CameraRepository
from backend.schemas.camera import CameraCreate


def seed():
    db = SessionLocal()
    existing = CameraRepository.get_all(db)
    if not existing:
        print("Seeding initial surveillance cameras...")
        cameras = [
            CameraCreate(
                name="Watchtower 01 - North Ridge",
                source_type="webcam",
                source_reference="0",
                location_label="North Ridge Sector 4",
                latitude=37.8651,
                longitude=-119.5383,
                enabled=True
            ),
            CameraCreate(
                name="Station 02 - Pine Valley Perimeter",
                source_type="ip_camera",
                source_reference="rtsp://192.168.1.120:554/live",
                location_label="Pine Valley Observation Post",
                latitude=37.8722,
                longitude=-119.5510,
                enabled=True
            ),
            CameraCreate(
                name="Aerial Drone Alpha - West Canopy",
                source_type="ip_camera",
                source_reference="rtsp://192.168.1.125:554/drone",
                location_label="West Canopy Drone Corridor",
                latitude=37.8590,
                longitude=-119.5705,
                enabled=True
            )
        ]
        for c in cameras:
            cam = CameraRepository.create(db, c)
            print(f"[*] Created camera: {cam.name} ({cam.id})")
    else:
        print(f"Database already contains {len(existing)} cameras. Skipping seed.")
    db.close()


if __name__ == "__main__":
    seed()

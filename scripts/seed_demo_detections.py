"""
Seed demo detections, Grad-CAM heatmaps, and alerts for project presentation and screenshots.
"""

import sys
import glob
from pathlib import Path
import cv2
from datetime import datetime, timezone, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.db.session import SessionLocal
from backend.repositories.cameras import CameraRepository
from backend.repositories.alerts import AlertRepository
from backend.models.alert import Alert
from backend.models.setting import SettingModel
from backend.services.prediction_service import PredictionService


def seed_demo_data():
    db = SessionLocal()
    pred_service = PredictionService()

    cameras = CameraRepository.get_all(db)
    if not cameras:
        print("[!] No cameras found. Run seed_database.py first.")
        db.close()
        return

    cam1 = cameras[0]  # Watchtower 01 - North Ridge
    cam2 = cameras[1] if len(cameras) > 1 else cam1  # Station 02
    cam3 = cameras[2] if len(cameras) > 2 else cam1  # Aerial Drone Alpha

    # Find sample images
    fire_samples = sorted(glob.glob(str(PROJECT_ROOT / "data" / "samples" / "fire" / "*.jpg")))
    smoke_samples = sorted(glob.glob(str(PROJECT_ROOT / "data" / "samples" / "smoke" / "*.jpg")))
    normal_samples = sorted(glob.glob(str(PROJECT_ROOT / "data" / "samples" / "normal" / "*.jpg")))

    print(f"[*] Found {len(fire_samples)} fire, {len(smoke_samples)} smoke, {len(normal_samples)} normal samples.")

    # 1. Process 5 fire frames for cam1 to satisfy 3-of-5 temporal window and trigger verified incident
    print("[*] Processing fire sequence for Watchtower 01...")
    for i in range(min(5, len(fire_samples))):
        img_bgr = cv2.imread(fire_samples[i])
        if img_bgr is not None:
            pred_service.process_frame(
                db=db,
                frame_bgr=img_bgr,
                camera_id=cam1.id,
                source_type="camera_stream",
                save_media=True
            )

    # 2. Process 4 smoke frames for cam2 to trigger smoke alert
    print("[*] Processing smoke sequence for Station 02...")
    for i in range(min(4, len(smoke_samples))):
        img_bgr = cv2.imread(smoke_samples[i])
        if img_bgr is not None:
            pred_service.process_frame(
                db=db,
                frame_bgr=img_bgr,
                camera_id=cam2.id,
                source_type="camera_stream",
                save_media=True
            )

    # 3. Process normal frames for cam3 (all clear)
    print("[*] Processing normal canopy frames for Aerial Drone Alpha...")
    for i in range(min(4, len(normal_samples))):
        img_bgr = cv2.imread(normal_samples[i])
        if img_bgr is not None:
            pred_service.process_frame(
                db=db,
                frame_bgr=img_bgr,
                camera_id=cam3.id,
                source_type="camera_stream",
                save_media=True
            )

    # 4. Process a few more fire and smoke frames for rich history
    for i in range(5, min(8, len(fire_samples))):
        img_bgr = cv2.imread(fire_samples[i])
        if img_bgr is not None:
            pred_service.process_frame(
                db=db,
                frame_bgr=img_bgr,
                camera_id=cam1.id,
                source_type="image_upload",
                save_media=True
            )

    # 5. Review alerts and adjust statuses for rich triage display
    alerts = db.query(Alert).all()
    print(f"[*] Generated {len(alerts)} alerts.")
    if len(alerts) >= 2:
        # Acknowledge second alert
        alerts[1].status = "ACKNOWLEDGED"
        alerts[1].acknowledged_at = datetime.now(timezone.utc) - timedelta(minutes=15)
        alerts[1].notes = "Ground Ranger Unit Alpha dispatched to sector for visual confirmation."
        db.commit()

    if len(alerts) >= 3:
        # Close third alert
        alerts[2].status = "CLOSED"
        alerts[2].acknowledged_at = datetime.now(timezone.utc) - timedelta(hours=2)
        alerts[2].closed_at = datetime.now(timezone.utc) - timedelta(minutes=45)
        alerts[2].notes = "Controlled agricultural burn safely concluded. Area monitored and clear."
        db.commit()
    elif len(alerts) == 1:
        # Create an acknowledged alert so both ACTIVE and ACKNOWLEDGED show
        new_ack = AlertRepository.create(
            db=db,
            alert_type="smoke",
            severity="WARNING",
            camera_id=cam2.id,
            detection_id=alerts[0].detection_id
        )
        new_ack.status = "ACKNOWLEDGED"
        new_ack.acknowledged_at = datetime.now(timezone.utc) - timedelta(minutes=22)
        new_ack.notes = "Ranger station notified. Aerial drone deployed for perimeter tracking."
        db.commit()

    # 6. Seed initial operational settings
    settings_data = {
        "fire_threshold": 0.75,
        "smoke_threshold": 0.70,
        "temporal_window": 5,
        "temporal_required_positives": 3,
        "alert_cooldown_seconds": 60
    }
    for k, v in settings_data.items():
        existing_setting = db.query(SettingModel).filter(SettingModel.key == k).first()
        if not existing_setting:
            s = SettingModel(key=k, value_json=v)
            db.add(s)
    db.commit()

    print("[OK] Demo detections, heatmaps, alerts, and settings seeded successfully!")
    db.close()


if __name__ == "__main__":
    seed_demo_data()

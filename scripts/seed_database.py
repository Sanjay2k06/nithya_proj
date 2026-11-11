"""
Database Seeding Script for Initial Cameras, Mock Historical Detections, and Surveillance Alerts.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uuid
from datetime import datetime, timezone, timedelta
from backend.db.session import SessionLocal
from backend.models.camera import Camera
from backend.models.detection import Detection
from backend.models.alert import Alert
from backend.models.notification_log import NotificationLog
from backend.repositories.cameras import CameraRepository
from backend.schemas.camera import CameraCreate


def seed():
    db = SessionLocal()
    existing_cameras = CameraRepository.get_all(db)

    # 1. Seed Cameras if empty
    if not existing_cameras:
        print("Seeding initial surveillance cameras...")
        camera_payloads = [
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
        existing_cameras = [CameraRepository.create(db, c) for c in camera_payloads]
        print(f"[OK] Seeded {len(existing_cameras)} surveillance cameras.")

    # Find available media images for realistic preview links
    media_dir = Path("runtime/media/originals")
    heatmap_dir = Path("runtime/media/heatmaps")
    orig_files = [f"/media/originals/{f.name}" for f in media_dir.glob("*.jpg")] if media_dir.exists() else []
    heat_files = [f"/media/heatmaps/{f.name}" for f in heatmap_dir.glob("*.jpg")] if heatmap_dir.exists() else []

    sample_orig = orig_files[0] if orig_files else None
    sample_heat = heat_files[0] if heat_files else None

    # 2. Seed Mock Detections if total detections < 15
    detection_count = db.query(Detection).count()
    if detection_count < 15:
        print(f"Current detections: {detection_count}. Seeding realistic historical surveillance telemetry...")
        now = datetime.now(timezone.utc)

        mock_scenarios = [
            # Day 0 (today)
            {"mins_ago": 6, "class": "fire", "conf": 0.965, "cam_idx": 0, "verified": True},
            {"mins_ago": 18, "class": "fire", "conf": 0.942, "cam_idx": 0, "verified": True},
            {"mins_ago": 35, "class": "smoke", "conf": 0.884, "cam_idx": 1, "verified": False},
            {"mins_ago": 52, "class": "normal", "conf": 0.971, "cam_idx": 2, "verified": False},
            {"mins_ago": 90, "class": "normal", "conf": 0.964, "cam_idx": 1, "verified": False},
            {"mins_ago": 140, "class": "normal", "conf": 0.952, "cam_idx": 0, "verified": False},
            # Day 1
            {"mins_ago": 1440 + 45, "class": "fire", "conf": 0.938, "cam_idx": 1, "verified": True},
            {"mins_ago": 1440 + 80, "class": "smoke", "conf": 0.875, "cam_idx": 1, "verified": True},
            {"mins_ago": 1440 + 160, "class": "normal", "conf": 0.980, "cam_idx": 2, "verified": False},
            {"mins_ago": 1440 + 300, "class": "normal", "conf": 0.962, "cam_idx": 0, "verified": False},
            # Day 2
            {"mins_ago": 2880 + 20, "class": "smoke", "conf": 0.892, "cam_idx": 0, "verified": True},
            {"mins_ago": 2880 + 110, "class": "normal", "conf": 0.974, "cam_idx": 1, "verified": False},
            {"mins_ago": 2880 + 240, "class": "normal", "conf": 0.968, "cam_idx": 2, "verified": False},
            # Day 3
            {"mins_ago": 4320 + 30, "class": "fire", "conf": 0.955, "cam_idx": 2, "verified": True},
            {"mins_ago": 4320 + 95, "class": "normal", "conf": 0.959, "cam_idx": 0, "verified": False},
            {"mins_ago": 4320 + 180, "class": "normal", "conf": 0.972, "cam_idx": 1, "verified": False},
            # Day 4
            {"mins_ago": 5760 + 60, "class": "smoke", "conf": 0.864, "cam_idx": 1, "verified": False},
            {"mins_ago": 5760 + 150, "class": "normal", "conf": 0.983, "cam_idx": 0, "verified": False},
            # Day 5
            {"mins_ago": 7200 + 40, "class": "normal", "conf": 0.966, "cam_idx": 2, "verified": False},
            {"mins_ago": 7200 + 120, "class": "normal", "conf": 0.975, "cam_idx": 1, "verified": False},
            # Day 6
            {"mins_ago": 8640 + 30, "class": "fire", "conf": 0.924, "cam_idx": 0, "verified": True},
            {"mins_ago": 8640 + 90, "class": "normal", "conf": 0.988, "cam_idx": 1, "verified": False},
        ]

        created_detections = []
        for item in mock_scenarios:
            t = now - timedelta(minutes=item["mins_ago"])
            cam = existing_cameras[item["cam_idx"] % len(existing_cameras)]
            cls = item["class"]
            conf = item["conf"]
            rem = (1.0 - conf) / 2
            probs = {
                "fire": conf if cls == "fire" else rem,
                "smoke": conf if cls == "smoke" else rem,
                "normal": conf if cls == "normal" else rem
            }

            det = Detection(
                id=str(uuid.uuid4()),
                camera_id=cam.id,
                source_id=cam.id,
                source_type="stream",
                predicted_class=cls,
                confidence=conf,
                probabilities_json=probs,
                frame_timestamp=t.timestamp(),
                inference_ms=18.5 + (item["mins_ago"] % 7),
                model_version="v1.0.0-firenet",
                image_path=sample_orig,
                heatmap_path=sample_heat if cls in ("fire", "smoke") else None,
                temporal_state={
                    "is_temporally_verified": item["verified"],
                    "alert_triggered": item["verified"] and cls == "fire",
                    "status_label": "VERIFIED_FIRE_ALARM" if (item["verified"] and cls == "fire") else ("SMOKE_WARNING" if cls == "smoke" else "NORMAL_SCENE"),
                    "positive_fire_count": 4 if cls == "fire" else 0,
                    "positive_smoke_count": 3 if cls == "smoke" else 0,
                    "window_size": 5,
                    "required_positives": 3,
                    "in_cooldown": False,
                    "cooldown_remaining_seconds": 0
                },
                created_at=t
            )
            db.add(det)
            created_detections.append(det)

        db.commit()
        print(f"[OK] Seeded {len(created_detections)} historical detection records.")

        # 3. Seed Realistic Active & Historical Alerts
        fire_dets = [d for d in created_detections if d.predicted_class == "fire"]
        smoke_dets = [d for d in created_detections if d.predicted_class == "smoke"]

        if fire_dets:
            # Active Fire Alert
            active_fire = Alert(
                id=str(uuid.uuid4()),
                camera_id=fire_dets[0].camera_id,
                source_id=fire_dets[0].source_id,
                source_name="Watchtower 01 - North Ridge",
                detection_id=fire_dets[0].id,
                alert_type="fire",
                severity="CRITICAL",
                status="ACTIVE",
                first_seen_at=fire_dets[0].created_at,
                last_seen_at=fire_dets[0].created_at,
                notification_status="DELIVERED",
                created_at=fire_dets[0].created_at
            )
            db.add(active_fire)

            # Notification Log for Active Fire Alert
            notif_log = NotificationLog(
                alert_id=active_fire.id,
                channel="telegram",
                status="DELIVERED",
                recipient="6270155918",
                message="FOREST FIRE EMERGENCY ALERT\n\nStatus: VERIFIED FIRE DETECTED\nSource: Watchtower 01 - North Ridge",
                evidence_path=sample_heat,
                attempted_at=fire_dets[0].created_at,
                delivered_at=fire_dets[0].created_at,
                retry_count=0
            )
            db.add(notif_log)

        if smoke_dets:
            # Active Smoke Warning
            active_smoke = Alert(
                id=str(uuid.uuid4()),
                camera_id=smoke_dets[0].camera_id,
                source_id=smoke_dets[0].source_id,
                source_name="Station 02 - Pine Valley Perimeter",
                detection_id=smoke_dets[0].id,
                alert_type="smoke",
                severity="WARNING",
                status="ACTIVE",
                first_seen_at=smoke_dets[0].created_at,
                last_seen_at=smoke_dets[0].created_at,
                notification_status="NOT_APPLICABLE",
                created_at=smoke_dets[0].created_at
            )
            db.add(active_smoke)

        if len(fire_dets) > 1:
            # Acknowledged Historical Alert
            hist_alert = Alert(
                id=str(uuid.uuid4()),
                camera_id=fire_dets[1].camera_id,
                source_id=fire_dets[1].source_id,
                source_name="Watchtower 01 - North Ridge",
                detection_id=fire_dets[1].id,
                alert_type="fire",
                severity="CRITICAL",
                status="ACKNOWLEDGED",
                first_seen_at=fire_dets[1].created_at,
                last_seen_at=fire_dets[1].created_at,
                acknowledged_at=fire_dets[1].created_at + timedelta(minutes=5),
                notification_status="DELIVERED",
                created_at=fire_dets[1].created_at
            )
            db.add(hist_alert)

        db.commit()
        print("[OK] Seeded realistic active and acknowledged alerts with Telegram delivery tracking.")

    db.close()


if __name__ == "__main__":
    seed()

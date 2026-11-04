"""
Analytics and Operational Summary Service.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta

from backend.models.detection import Detection
from backend.models.alert import Alert
from backend.models.camera import Camera


class AnalyticsService:

    @staticmethod
    def get_summary(db: Session) -> Dict[str, Any]:
        total_detections = db.query(Detection).count()
        fire_count = db.query(Detection).filter(Detection.predicted_class == "fire").count()
        smoke_count = db.query(Detection).filter(Detection.predicted_class == "smoke").count()
        normal_count = db.query(Detection).filter(Detection.predicted_class == "normal").count()

        active_alerts = db.query(Alert).filter(Alert.status == "ACTIVE").count()
        total_alerts = db.query(Alert).count()

        total_cameras = db.query(Camera).count()
        active_cameras = db.query(Camera).filter(Camera.status == "STREAMING").count()

        avg_latency = db.query(func.avg(Detection.inference_ms)).scalar() or 0.0

        # Calculate temporal suppression efficiency
        raw_positives = fire_count + smoke_count
        suppressed_transients = max(raw_positives - total_alerts, 0)
        suppression_rate = (suppressed_transients / max(raw_positives, 1)) * 100.0

        # Recent 7-day trend
        today = datetime.now(timezone.utc).date()
        daily_trend: List[Dict[str, Any]] = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_start = datetime(day.year, day.month, day.day, 0, 0, 0, tzinfo=timezone.utc)
            day_end = day_start + timedelta(days=1)

            d_count = db.query(Detection).filter(
                Detection.created_at >= day_start,
                Detection.created_at < day_end
            ).count()
            a_count = db.query(Alert).filter(
                Alert.created_at >= day_start,
                Alert.created_at < day_end
            ).count()

            daily_trend.append({
                "date": day.strftime("%b %d"),
                "detections": d_count,
                "alerts": a_count
            })

        return {
            "total_detections": total_detections,
            "classes": {
                "fire": fire_count,
                "smoke": smoke_count,
                "normal": normal_count
            },
            "active_alerts": active_alerts,
            "total_alerts": total_alerts,
            "total_cameras": total_cameras,
            "active_cameras": active_cameras,
            "avg_inference_ms": round(float(avg_latency), 2),
            "suppression_efficiency": {
                "raw_positives": raw_positives,
                "verified_alerts": total_alerts,
                "suppressed_transients": suppressed_transients,
                "suppression_percentage": round(suppression_rate, 1)
            },
            "daily_trend": daily_trend
        }

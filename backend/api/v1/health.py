"""
Application and Database Health Endpoint.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.db.session import get_db
from backend.services.prediction_service import prediction_service

router = APIRouter()


@router.get("/health", summary="Check backend and database health")
def get_health(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)[:50]}"

    model_loaded = (
        prediction_service.engine is not None and
        prediction_service.engine.is_loaded
    )

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "model_loaded": model_loaded,
        "demo_mode": prediction_service.engine.demo_mode if prediction_service.engine else False,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

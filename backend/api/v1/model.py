"""
Model Information and Status Endpoint.
"""

from fastapi import APIRouter
from backend.core.config import settings
from backend.services.prediction_service import prediction_service
from ml.config import CLASS_NAMES

router = APIRouter()


@router.get("/status", summary="Model status, version, and classes")
def get_model_status():
    eng = prediction_service.engine
    is_loaded = eng is not None and eng.is_loaded

    return {
        "loaded": is_loaded,
        "model_name": "FireNetCNN",
        "version": eng.checkpoint_metadata.get("config", {}).get("version", "v1.0.0") if eng else "unknown",
        "classes": CLASS_NAMES,
        "device": str(eng.device) if eng else "unknown",
        "demo_mode": eng.demo_mode if eng else False,
        "checkpoint_path": settings.MODEL_PATH,
        "fire_threshold": settings.FIRE_THRESHOLD,
        "smoke_threshold": settings.SMOKE_THRESHOLD
    }

"""
Main API Router aggregating all v1 sub-routers.
"""

from fastapi import APIRouter

from backend.api.v1.health import router as health_router
from backend.api.v1.model import router as model_router
from backend.api.v1.predictions import router as predictions_router
from backend.api.v1.monitoring import router as monitoring_router
from backend.api.v1.detections import router as detections_router
from backend.api.v1.alerts import router as alerts_router
from backend.api.v1.analytics import router as analytics_router
from backend.api.v1.settings import router as settings_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(model_router, prefix="/model", tags=["Model"])
api_router.include_router(predictions_router, prefix="/predictions", tags=["Predictions"])
api_router.include_router(monitoring_router, prefix="/monitoring", tags=["Monitoring & Cameras"])
api_router.include_router(detections_router, prefix="/detections", tags=["Detections"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["Alerts & Incidents"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(settings_router, prefix="/settings", tags=["Operational Settings"])

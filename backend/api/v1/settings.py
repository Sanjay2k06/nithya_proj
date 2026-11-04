"""
Operational Settings API Router.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.core.config import settings
from backend.repositories.settings import SettingsRepository
from backend.schemas.settings import OperationalSettingsSchema, OperationalSettingsUpdate
from backend.services.prediction_service import prediction_service

router = APIRouter()


@router.get("", response_model=OperationalSettingsSchema, summary="Read operational thresholds and parameters")
def get_operational_settings(db: Session = Depends(get_db)):
    persisted = SettingsRepository.get(db, "operational_settings")
    if persisted:
        return OperationalSettingsSchema(**persisted)

    # Return default configuration values
    return OperationalSettingsSchema(
        fire_threshold=settings.FIRE_THRESHOLD,
        smoke_threshold=settings.SMOKE_THRESHOLD,
        temporal_window=settings.TEMPORAL_WINDOW,
        temporal_required_positives=settings.TEMPORAL_REQUIRED_POSITIVES,
        alert_cooldown_seconds=settings.ALERT_COOLDOWN_SECONDS,
        max_upload_mb=settings.MAX_UPLOAD_MB,
        max_video_seconds=settings.MAX_VIDEO_SECONDS,
        model_demo_mode=settings.MODEL_DEMO_MODE
    )


@router.patch("", response_model=OperationalSettingsSchema, summary="Update permitted operational thresholds")
def update_operational_settings(
    update_in: OperationalSettingsUpdate,
    db: Session = Depends(get_db)
):
    current = get_operational_settings(db)
    updated_dict = current.model_dump()

    data = update_in.model_dump(exclude_unset=True)
    for k, v in data.items():
        if v is not None:
            updated_dict[k] = v

    SettingsRepository.set(db, "operational_settings", updated_dict)

    # Apply live to temporal verifier
    prediction_service.temporal_verifier.default_fire_threshold = updated_dict["fire_threshold"]
    prediction_service.temporal_verifier.default_smoke_threshold = updated_dict["smoke_threshold"]
    prediction_service.temporal_verifier.default_window_size = updated_dict["temporal_window"]
    prediction_service.temporal_verifier.default_required_positives = updated_dict["temporal_required_positives"]
    prediction_service.temporal_verifier.default_cooldown_seconds = updated_dict["alert_cooldown_seconds"]

    return OperationalSettingsSchema(**updated_dict)

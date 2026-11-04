"""
FastAPI Route Dependencies.
"""

from typing import Generator
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.services.prediction_service import prediction_service, PredictionService


def get_prediction_engine() -> PredictionService:
    """Dependency injection for prediction engine service."""
    return prediction_service

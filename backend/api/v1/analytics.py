"""
Analytics and Operational Summary API Endpoint.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/summary", summary="Aggregated monitoring statistics and class breakdown")
def get_analytics_summary(db: Session = Depends(get_db)):
    return AnalyticsService.get_summary(db)

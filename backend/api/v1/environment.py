"""Optional environmental sensor ingestion and history."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.models.environmental_reading import EnvironmentalReading
from backend.schemas.environmental_reading import (
    EnvironmentalReadingCreate,
    EnvironmentalReadingResponse,
)

router = APIRouter()


@router.post(
    "/readings",
    response_model=EnvironmentalReadingResponse,
    status_code=201,
    summary="Ingest an actual environmental sensor reading",
)
def create_environmental_reading(
    reading: EnvironmentalReadingCreate,
    db: Session = Depends(get_db),
):
    record = EnvironmentalReading(**reading.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get(
    "/readings",
    response_model=List[EnvironmentalReadingResponse],
    summary="List actual environmental sensor readings",
)
def list_environmental_readings(
    source_id: Optional[str] = Query(default=None, max_length=128),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(EnvironmentalReading)
    if source_id:
        query = query.filter(EnvironmentalReading.source_id == source_id)
    return query.order_by(desc(EnvironmentalReading.recorded_at)).limit(limit).all()

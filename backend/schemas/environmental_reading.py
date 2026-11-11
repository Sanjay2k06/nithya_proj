"""Validated API contracts for environmental readings."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EnvironmentalReadingCreate(BaseModel):
    source_id: str = Field(..., min_length=1, max_length=128)
    temperature_c: Optional[float] = Field(default=None, ge=-80, le=80, allow_inf_nan=False)
    humidity_percent: Optional[float] = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    wind_speed_mps: Optional[float] = Field(default=None, ge=0, le=200, allow_inf_nan=False)
    wind_direction_degrees: Optional[float] = Field(default=None, ge=0, le=360, allow_inf_nan=False)
    smoke_sensor_value: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("recorded_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value

    @model_validator(mode="after")
    def require_a_measurement(self):
        readings = (
            self.temperature_c,
            self.humidity_percent,
            self.wind_speed_mps,
            self.wind_direction_degrees,
            self.smoke_sensor_value,
        )
        if all(value is None for value in readings):
            raise ValueError("At least one sensor measurement must be supplied.")
        return self


class EnvironmentalReadingResponse(EnvironmentalReadingCreate):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

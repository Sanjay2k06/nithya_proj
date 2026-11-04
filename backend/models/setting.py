"""
Setting SQLAlchemy Model.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON

from backend.db.base import Base


class SettingModel(Base):
    __tablename__ = "settings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(100), unique=True, nullable=False, index=True)
    value_json = Column(JSON, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

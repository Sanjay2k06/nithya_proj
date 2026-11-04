"""
Settings Repository.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models.setting import SettingModel


class SettingsRepository:

    @staticmethod
    def get(db: Session, key: str) -> Optional[Any]:
        rec = db.query(SettingModel).filter(SettingModel.key == key).first()
        return rec.value_json if rec else None

    @staticmethod
    def set(db: Session, key: str, value: Any) -> SettingModel:
        rec = db.query(SettingModel).filter(SettingModel.key == key).first()
        if rec:
            rec.value_json = value
        else:
            rec = SettingModel(key=key, value_json=value)
            db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec

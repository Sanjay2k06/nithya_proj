"""
SQLAlchemy Database Models Package.
"""

from backend.models.camera import Camera
from backend.models.detection import Detection
from backend.models.alert import Alert
from backend.models.setting import SettingModel
from backend.models.notification_log import NotificationLog
from backend.models.environmental_reading import EnvironmentalReading
from backend.models.monitoring_source import MonitoringSource

__all__ = [
    "Camera",
    "Detection",
    "Alert",
    "SettingModel",
    "NotificationLog",
    "EnvironmentalReading",
    "MonitoringSource",
]

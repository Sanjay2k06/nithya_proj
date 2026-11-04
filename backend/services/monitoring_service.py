"""
Monitoring Service managing active streams and status.
"""

from typing import Dict, Any
from backend.workers.monitoring_manager import monitoring_manager


class MonitoringService:

    @staticmethod
    def start_camera(camera_id: str, source_reference: str) -> bool:
        return monitoring_manager.start_camera(camera_id, source_reference)

    @staticmethod
    def stop_camera(camera_id: str) -> bool:
        return monitoring_manager.stop_camera(camera_id)

    @staticmethod
    def get_status() -> Dict[str, Any]:
        return monitoring_manager.get_status()


monitoring_service = MonitoringService()

"""
Video Processing Service.
"""

from typing import Dict, Any, Optional
from backend.workers.video_worker import start_video_task, VIDEO_TASKS


class VideoService:

    @staticmethod
    def start_task(video_path: str, filename: str) -> str:
        return start_video_task(video_path, filename)

    @staticmethod
    def get_task(task_id: str) -> Optional[Dict[str, Any]]:
        return VIDEO_TASKS.get(task_id)


video_service = VideoService()

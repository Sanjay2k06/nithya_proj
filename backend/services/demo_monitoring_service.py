"""Backend-owned video processing state for the local simulated CCTV sources."""

from datetime import datetime, timezone
from pathlib import Path
from threading import Event, Lock, Thread
from time import monotonic
from typing import Any, Callable, Dict, Optional

import cv2
import numpy as np
from sqlalchemy.orm import Session

from backend.core.logging import logger
from backend.models.monitoring_source import MonitoringSource
from ml.experimental.progression import measure_optical_flow


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_SOURCES = {
    "cam01-normal": {
        "source_id": "cam01-normal",
        "name": "CAM 01 - NORMAL FOREST",
        "description": "Simulated forest footage without an assumed detection result.",
        "file_name": "forest_normal.mp4",
    },
    "cam02-fire": {
        "source_id": "cam02-fire",
        "name": "CAM 02 - FOREST FIRE",
        "description": "Simulated forest footage containing a fire scene.",
        "file_name": "forest_fire.mp4",
    },
}

VideoProcessor = Callable[[str, Event, float], None]


class DemoMonitoringService:
    """Owns the selected source, processing thread, and latest backend result."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._selected_source_id: Optional[str] = None
        self._state = "IDLE"
        self._is_processing = False
        self._latest_result: Optional[Dict[str, Any]] = None
        self._last_processed_video_seconds: Optional[float] = None
        self._processing_delay_ms: Optional[float] = None
        self._processed_frames = 0
        self._last_error: Optional[str] = None
        self._worker: Optional[Thread] = None
        self._stop_event: Optional[Event] = None
        self._previous_gray_by_source: Dict[str, np.ndarray] = {}
        self._previous_video_time_by_source: Dict[str, float] = {}

    @staticmethod
    def get_source(source_id: str) -> Optional[Dict[str, Any]]:
        source = DEMO_SOURCES.get(source_id)
        if source is None:
            return None
        source_path = PROJECT_ROOT / "image_fire" / source["file_name"]
        return {
            **source,
            "available": source_path.is_file(),
            "video_url": f"/api/v1/monitoring/demo-sources/{source_id}/video",
            "source_type": "simulated_cctv",
            "source_status": "AVAILABLE" if source_path.is_file() else "UNAVAILABLE",
            "playback_status": "STOPPED",
            "processing_status": "STOPPED",
            "last_processed_at": None,
            "last_processed_video_seconds": None,
        }

    @staticmethod
    def get_video_path(source_id: str) -> Optional[Path]:
        source = DEMO_SOURCES.get(source_id)
        if source is None:
            return None
        return PROJECT_ROOT / "image_fire" / source["file_name"]

    def list_sources(self, db: Session) -> list[Dict[str, Any]]:
        return self.sync_sources(db)

    def sync_sources(self, db: Session) -> list[Dict[str, Any]]:
        status = self.get_status()
        selected_source_id = (
            status["selected_source"]["source_id"] if status["selected_source"] else None
        )
        source_responses = []
        for source_id, source_data in DEMO_SOURCES.items():
            source = self.get_source(source_id)
            if source is None:
                continue
            record = db.get(MonitoringSource, source_id)
            if record is None:
                record = MonitoringSource(
                    id=source_id,
                    name=source_data["name"],
                    source_type="simulated_cctv",
                    video_filename=source_data["file_name"],
                    source_status=source["source_status"],
                    playback_status="STOPPED",
                    processing_status="STOPPED",
                )
                db.add(record)
            record.name = source_data["name"]
            record.source_type = "simulated_cctv"
            record.video_filename = source_data["file_name"]
            record.source_status = source["source_status"]
            record.playback_status = (
                "PLAYING" if source_id == selected_source_id and status["is_monitoring"] else "STOPPED"
            )
            record.processing_status = (
                "PROCESSING"
                if source_id == selected_source_id and status["is_processing"]
                else status["status"]
                if source_id == selected_source_id and status["is_monitoring"]
                else "STOPPED"
            )
            source_responses.append((source, record))
        db.commit()
        return [
            {
                **source,
                "source_status": record.source_status,
                "playback_status": record.playback_status,
                "processing_status": record.processing_status,
                "last_processed_at": record.last_processed_at,
                "last_processed_video_seconds": record.last_processed_video_seconds,
            }
            for source, record in source_responses
        ]

    def record_processed_frame(
        self,
        db: Session,
        source_id: str,
        video_timestamp_seconds: float,
    ) -> None:
        record = db.get(MonitoringSource, source_id)
        if record is None:
            source_data = DEMO_SOURCES[source_id]
            record = MonitoringSource(
                id=source_id,
                name=source_data["name"],
                source_type="simulated_cctv",
                video_filename=source_data["file_name"],
                source_status="AVAILABLE",
                playback_status="PLAYING",
                processing_status="IN_PROGRESS",
            )
            db.add(record)
        record.last_processed_at = datetime.now(timezone.utc)
        record.last_processed_video_seconds = video_timestamp_seconds
        db.commit()

    def select_source(self, source_id: str) -> Dict[str, Any]:
        if source_id not in DEMO_SOURCES:
            raise ValueError(f"Unknown demo source: {source_id}")
        source = self.get_source(source_id)
        if source is None or not source["available"]:
            raise FileNotFoundError(f"Demo video is unavailable for source {source_id}.")
        with self._lock:
            if self._worker is not None and self._worker.is_alive():
                raise RuntimeError("Stop the current monitoring task before switching sources.")
            self._selected_source_id = source_id
            self._state = "IDLE"
            self._is_processing = False
            self._latest_result = None
            self._last_processed_video_seconds = None
            self._processing_delay_ms = None
            self._processed_frames = 0
            self._last_error = None
            self._previous_gray_by_source.pop(source_id, None)
            self._previous_video_time_by_source.pop(source_id, None)
        return source

    def measure_motion(
        self,
        source_id: str,
        frame_bgr: np.ndarray,
        video_timestamp_seconds: float,
    ) -> Optional[Dict[str, float]]:
        current_gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        with self._lock:
            previous_gray = self._previous_gray_by_source.get(source_id)
            previous_video_time = self._previous_video_time_by_source.get(source_id)
            self._previous_gray_by_source[source_id] = current_gray
            self._previous_video_time_by_source[source_id] = video_timestamp_seconds
        if previous_gray is None or (
            previous_video_time is not None and video_timestamp_seconds < previous_video_time
        ):
            return None
        return measure_optical_flow(previous_gray, current_gray)

    def start(self, processor: VideoProcessor) -> Dict[str, Any]:
        with self._lock:
            if self._selected_source_id is None:
                raise ValueError("Select an available demo source before starting monitoring.")
            if self._worker is not None and self._worker.is_alive():
                raise RuntimeError("A simulated CCTV processing task is already running.")
            source_id = self._selected_source_id
            stop_event = Event()
            started_at = monotonic()
            self._stop_event = stop_event
            self._state = "IN_PROGRESS"
            self._is_processing = False
            self._latest_result = None
            self._last_processed_video_seconds = None
            self._processing_delay_ms = None
            self._processed_frames = 0
            self._last_error = None
            worker = Thread(
                target=self._run_worker,
                args=(processor, source_id, stop_event, started_at),
                name=f"demo-monitor-{source_id}",
                daemon=True,
            )
            self._worker = worker
            worker.start()
        return self.get_status()

    def _run_worker(
        self,
        processor: VideoProcessor,
        source_id: str,
        stop_event: Event,
        started_at: float,
    ) -> None:
        try:
            processor(source_id, stop_event, started_at)
        except Exception as exc:
            logger.exception("Simulated CCTV processing failed for source %s.", source_id)
            with self._lock:
                self._state = "ERROR"
                self._last_error = str(exc)
                self._latest_result = None
                self._last_processed_video_seconds = None
                self._processing_delay_ms = None
        finally:
            with self._lock:
                if stop_event.is_set() and self._state != "ERROR":
                    self._state = "STOPPED"
                elif self._state not in {"ERROR", "STOPPED"}:
                    self._state = "STOPPED"
                self._is_processing = False
                self._worker = None

    def stop(self, timeout_seconds: float = 65.0) -> Dict[str, Any]:
        with self._lock:
            worker = self._worker
            stop_event = self._stop_event
            if stop_event is not None:
                stop_event.set()
            self._is_processing = False
        if worker is not None and worker.is_alive():
            worker.join(timeout=timeout_seconds)
        with self._lock:
            self._latest_result = None
            self._last_processed_video_seconds = None
            self._processing_delay_ms = None
            self._previous_gray_by_source.clear()
            self._previous_video_time_by_source.clear()
            if worker is not None and worker.is_alive():
                self._state = "ERROR"
                self._last_error = "The processing task did not stop within the timeout."
            elif self._state != "ERROR":
                self._state = "STOPPED"
                self._last_error = None
        return self.get_status()

    def begin_processing(self) -> bool:
        with self._lock:
            if self._stop_event is None or self._stop_event.is_set():
                return False
            self._is_processing = True
            return True

    def finish_frame(
        self,
        result: Dict[str, Any],
        video_timestamp_seconds: float,
        processing_delay_ms: float,
    ) -> None:
        temporal = result.get("temporal_state") or {}
        if result.get("analysis_provider") == "gemini":
            state = "IN_PROGRESS"
        elif temporal.get("is_temporally_verified"):
            state = "VERIFIED"
        elif result.get("predicted_class") in {"fire", "smoke"}:
            state = "VERIFYING"
        else:
            state = "IN_PROGRESS"
        with self._lock:
            if self._stop_event is not None and self._stop_event.is_set():
                self._is_processing = False
                return
            self._latest_result = result
            self._last_processed_video_seconds = video_timestamp_seconds
            self._processing_delay_ms = round(max(0.0, processing_delay_ms), 1)
            self._processed_frames += 1
            self._is_processing = False
            self._state = state

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            source = (
                self.get_source(self._selected_source_id)
                if self._selected_source_id is not None
                else None
            )
            is_monitoring = self._state in {"IN_PROGRESS", "VERIFYING", "VERIFIED"}
            if source is not None:
                source["playback_status"] = "PLAYING" if is_monitoring else "STOPPED"
                source["processing_status"] = (
                    "PROCESSING" if self._is_processing else self._state
                )
                source["last_processed_video_seconds"] = self._last_processed_video_seconds
            return {
                "selected_source": source,
                "is_monitoring": is_monitoring,
                "is_processing": self._is_processing,
                "latest_detection": self._latest_result,
                "last_processed_video_seconds": self._last_processed_video_seconds,
                "processing_delay_ms": self._processing_delay_ms,
                "processed_frames": self._processed_frames,
                "status": self._state,
                "error": self._last_error,
            }


demo_monitoring_service = DemoMonitoringService()

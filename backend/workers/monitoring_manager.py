"""
Monitoring Manager and Camera Ingestion Thread Lifecycle.
"""

from typing import Dict, Any, Optional
import time
import threading
import cv2

from backend.core.logging import logger
from backend.db.session import SessionLocal
from backend.repositories.cameras import CameraRepository
from backend.services.prediction_service import prediction_service


class CameraWorker(threading.Thread):
    """Background worker thread processing live frames from a specific camera."""

    def __init__(self, camera_id: str, source_ref: str, sample_interval: float = 0.5):
        super().__init__(daemon=True)
        self.camera_id = camera_id
        self.source_ref = source_ref
        self.sample_interval = sample_interval
        self.stop_event = threading.Event()
        self.latest_result: Dict[str, Any] = {}
        self.is_connected = False
        self.fps: float = 0.0

    def run(self):
        logger.info(f"Starting camera worker thread for: {self.camera_id} (source: {self.source_ref})")

        # Parse source reference (integer for webcam index or string for RTSP/file)
        try:
            source = int(self.source_ref)
        except ValueError:
            source = self.source_ref

        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            logger.warning(f"Failed to open video source: {self.source_ref}")
            self._update_camera_status("ERROR")
            return

        self.is_connected = True
        self._update_camera_status("STREAMING")

        last_sample_time = 0.0
        frame_counter = 0
        t_start = time.time()

        db = SessionLocal()
        try:
            while not self.stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue

                now = time.time()
                frame_counter += 1
                if now - t_start >= 1.0:
                    self.fps = frame_counter / (now - t_start)
                    frame_counter = 0
                    t_start = now

                if now - last_sample_time >= self.sample_interval:
                    last_sample_time = now
                    try:
                        res = prediction_service.process_frame(
                            db=db,
                            frame_bgr=frame,
                            camera_id=self.camera_id,
                            source_type="stream",
                            save_media=True
                        )
                        self.latest_result = res
                    except Exception as e:
                        logger.error(f"Error evaluating camera frame: {e}")

                time.sleep(0.01)

        finally:
            cap.release()
            db.close()
            self.is_connected = False
            self._update_camera_status("IDLE")
            logger.info(f"Camera worker stopped for: {self.camera_id}")

    def stop(self):
        self.stop_event.set()

    def _update_camera_status(self, status: str):
        try:
            db = SessionLocal()
            cam = CameraRepository.get_by_id(db, self.camera_id)
            if cam:
                cam.status = status
                db.commit()
            db.close()
        except Exception:
            pass


class MonitoringManager:
    """Singleton managing active camera threads and system-wide monitoring lifecycle."""

    def __init__(self):
        self.workers: Dict[str, CameraWorker] = {}
        self.lock = threading.Lock()

    def start_camera(self, camera_id: str, source_ref: str) -> bool:
        with self.lock:
            if camera_id in self.workers and self.workers[camera_id].is_alive():
                logger.info(f"Camera {camera_id} is already actively being monitored.")
                return True

            worker = CameraWorker(camera_id=camera_id, source_ref=source_ref)
            self.workers[camera_id] = worker
            worker.start()
            return True

    def stop_camera(self, camera_id: str) -> bool:
        with self.lock:
            worker = self.workers.get(camera_id)
            if worker:
                worker.stop()
                worker.join(timeout=2.0)
                del self.workers[camera_id]
                return True
            return False

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            active_list = []
            for cid, w in self.workers.items():
                active_list.append({
                    "camera_id": cid,
                    "is_alive": w.is_alive(),
                    "fps": round(w.fps, 1),
                    "latest_prediction": w.latest_result.get("predicted_class", "none"),
                    "confidence": w.latest_result.get("confidence", 0.0),
                    "temporally_verified": w.latest_result.get("temporally_verified", False)
                })
            return {
                "active_workers_count": len(self.workers),
                "workers": active_list
            }

    def shutdown_all(self):
        logger.info("Shutting down all active monitoring workers...")
        with self.lock:
            for worker in self.workers.values():
                worker.stop()
            for worker in self.workers.values():
                worker.join(timeout=1.0)
            self.workers.clear()


monitoring_manager = MonitoringManager()

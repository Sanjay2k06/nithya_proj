"""
Prediction Service orchestrating ML Inference, Grad-CAM, Media Storage, and Persistence.
"""

from typing import Dict, Any, Optional, Tuple
import os
import time
import uuid
from pathlib import Path
import numpy as np
import cv2
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.logging import logger
from backend.repositories.detections import DetectionRepository
from backend.services.alert_service import AlertService
from ml.inference import InferenceEngine
from ml.temporal_verifier import TemporalVerifier, TemporalState


class PredictionService:

    def __init__(self):
        self.media_root = Path(settings.MEDIA_ROOT)
        self.originals_dir = self.media_root / "originals"
        self.heatmaps_dir = self.media_root / "heatmaps"
        self.originals_dir.mkdir(parents=True, exist_ok=True)
        self.heatmaps_dir.mkdir(parents=True, exist_ok=True)

        self.engine: Optional[InferenceEngine] = None
        self.temporal_verifier = TemporalVerifier(
            default_window_size=settings.TEMPORAL_WINDOW,
            default_required_positives=settings.TEMPORAL_REQUIRED_POSITIVES,
            default_fire_threshold=settings.FIRE_THRESHOLD,
            default_smoke_threshold=settings.SMOKE_THRESHOLD,
            default_cooldown_seconds=settings.ALERT_COOLDOWN_SECONDS
        )

        self._initialize_engine()

    def _initialize_engine(self) -> None:
        checkpoint_path = settings.MODEL_PATH
        demo_mode = settings.MODEL_DEMO_MODE

        logger.info(f"Initializing InferenceEngine (checkpoint: {checkpoint_path}, demo_mode: {demo_mode})...")
        try:
            self.engine = InferenceEngine(
                checkpoint_path=checkpoint_path,
                device_str=settings.MODEL_DEVICE,
                demo_mode=demo_mode
            )
            logger.info("InferenceEngine initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not load checkpoint ({e}). Initializing fallback demo engine.")
            self.engine = InferenceEngine(demo_mode=True)

    def process_frame(
        self,
        db: Optional[Session],
        frame_bgr: np.ndarray,
        camera_id: Optional[str] = None,
        source_type: str = "stream",
        save_media: bool = True
    ) -> Dict[str, Any]:
        """
        Executes end-to-end frame analysis: ML prediction, Grad-CAM explanation,
        temporal filtering, database persistence, and alert triggering.
        """
        if self.engine is None:
            raise RuntimeError("Inference engine is not initialized.")

        t_now = time.time()
        # 1. Run model inference and Grad-CAM
        infer_result = self.engine.predict(frame_bgr, generate_explanation=True)

        predicted_class = infer_result["predicted_class"]
        confidence = infer_result["confidence"]
        probabilities = infer_result["probabilities"]
        inference_ms = infer_result["inference_ms"]

        # 2. Run temporal verification
        stream_id = camera_id if camera_id else "ephemeral_stream"
        temporal_state: TemporalState = self.temporal_verifier.verify_frame(
            camera_id=stream_id,
            predicted_class=predicted_class,
            confidence=confidence,
            probabilities=probabilities,
            timestamp=t_now
        )

        # 3. Save media files if requested
        rel_orig_path: Optional[str] = None
        rel_heatmap_path: Optional[str] = None

        if save_media:
            frame_uid = uuid.uuid4().hex
            orig_filename = f"{frame_uid}_orig.jpg"
            orig_full = self.originals_dir / orig_filename
            cv2.imwrite(str(orig_full), frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            rel_orig_path = f"/media/originals/{orig_filename}"

            if "blended_bgr" in infer_result:
                heat_filename = f"{frame_uid}_gradcam.jpg"
                heat_full = self.heatmaps_dir / heat_filename
                cv2.imwrite(str(heat_full), infer_result["blended_bgr"], [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                rel_heatmap_path = f"/media/heatmaps/{heat_filename}"

        # 4. Persist detection record if database session is provided
        detection_id: Optional[str] = None
        alert_id: Optional[str] = None

        if db is not None:
            detection_record = DetectionRepository.create(
                db=db,
                detection_data={
                    "camera_id": camera_id,
                    "source_type": source_type,
                    "predicted_class": predicted_class,
                    "confidence": confidence,
                    "probabilities_json": probabilities,
                    "frame_timestamp": t_now,
                    "inference_ms": inference_ms,
                    "model_version": infer_result.get("model_version", "1.0.0"),
                    "image_path": rel_orig_path,
                    "heatmap_path": rel_heatmap_path,
                    "temporal_state": temporal_state.model_dump()
                }
            )
            detection_id = detection_record.id

            # 5. Trigger alert if temporal verifier declared alert condition
            if temporal_state.alert_triggered and temporal_state.verified_class:
                alert = AlertService.process_incident(
                    db=db,
                    alert_type=temporal_state.verified_class,
                    camera_id=camera_id,
                    detection_id=detection_id,
                    confidence=confidence
                )
                alert_id = alert.id

        return {
            "detection_id": detection_id,
            "predicted_class": predicted_class,
            "confidence": confidence,
            "probabilities": probabilities,
            "inference_ms": inference_ms,
            "model_version": infer_result.get("model_version", "1.0.0"),
            "original_image_url": rel_orig_path,
            "heatmap_image_url": rel_heatmap_path,
            "temporally_verified": temporal_state.is_temporally_verified,
            "alert_triggered": temporal_state.alert_triggered,
            "alert_id": alert_id,
            "status_label": temporal_state.status_label,
            "demo_mode": infer_result.get("demo_mode", False),
            "temporal_state": temporal_state.model_dump()
        }


prediction_service = PredictionService()

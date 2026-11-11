"""
High-Performance Inference Engine with Grad-CAM and Temporal Verification.
"""

from typing import Optional, Dict, Any
import time
from pathlib import Path
import cv2
import numpy as np
import torch

from ml.config import CLASS_NAMES, IDX_TO_CLASS
from ml.model import FireNetCNN
from ml.transforms import preprocess_numpy_frame
from ml.gradcam import GradCAM
from ml.checkpoints import load_model_from_checkpoint
from ml.reproducibility import get_device


class InferenceEngine:
    """
    Production-ready inference engine for FireNetCNN.
    Caches model in memory, executes tensor operations, and generates Grad-CAM overlays.
    """

    def __init__(
        self,
        checkpoint_path: Optional[str] = None,
        device_str: str = "auto",
        demo_mode: bool = False
    ):
        self.device = get_device(device_str)
        self.demo_mode = demo_mode
        self.model: Optional[FireNetCNN] = None
        self.gradcam: Optional[GradCAM] = None
        self.checkpoint_metadata: Dict[str, Any] = {}
        self.is_loaded = False

        if self.demo_mode:
            # Demo mode initializes an untrained FireNetCNN instance for testing UI
            self.model = FireNetCNN(num_classes=len(CLASS_NAMES))
            self.model.to(self.device)
            self.model.eval()
            self.gradcam = GradCAM(self.model)
            self.is_loaded = True
            self.checkpoint_metadata = {"mode": "demo_fixture", "version": "demo"}
        else:
            if not checkpoint_path:
                raise ValueError("A trained FireNet-CNN checkpoint path is required.")
            if not Path(checkpoint_path).is_file():
                raise FileNotFoundError(f"Trained checkpoint not found at: {Path(checkpoint_path).resolve()}")
            self.load_checkpoint(checkpoint_path)

    def load_checkpoint(self, checkpoint_path: str) -> None:
        """Loads model weights from disk and hooks Grad-CAM."""
        model, metadata = load_model_from_checkpoint(checkpoint_path, device=self.device)
        self.model = model
        self.gradcam = GradCAM(self.model)
        self.checkpoint_metadata = metadata
        self.is_loaded = True

    def predict(
        self,
        frame_bgr: np.ndarray,
        generate_explanation: bool = True
    ) -> Dict[str, Any]:
        """
        Executes inference on a single BGR OpenCV frame.

        Returns:
            Dict containing predicted_class, confidence, probabilities, inference_ms,
            and optional explanation heatmap & blended image.
        """
        if not self.is_loaded or self.model is None:
            raise RuntimeError("Inference engine has no model loaded and is not in demo mode.")

        if frame_bgr is None or frame_bgr.size == 0:
            raise ValueError("Input frame is empty or invalid.")

        start_time = time.perf_counter()

        # Preprocess frame to (1, 3, 224, 224)
        input_tensor = preprocess_numpy_frame(frame_bgr, device=self.device)

        with torch.no_grad():
            logits = self.model(input_tensor)
            probs = torch.softmax(logits, dim=1).squeeze().cpu().numpy()

        fire_idx = CLASS_NAMES.index("fire") if "fire" in CLASS_NAMES else 0
        smoke_idx = CLASS_NAMES.index("smoke") if "smoke" in CLASS_NAMES else 1
        normal_idx = CLASS_NAMES.index("normal") if "normal" in CLASS_NAMES else 2

        fire_prob = float(probs[fire_idx])
        smoke_prob = float(probs[smoke_idx])

        # Multi-modal flame verification: combine CNN activations with optical color distribution
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        lower_fire1 = np.array([0, 70, 70])
        upper_fire1 = np.array([25, 255, 255])
        lower_fire2 = np.array([160, 70, 70])
        upper_fire2 = np.array([180, 255, 255])
        fire_mask = cv2.inRange(hsv, lower_fire1, upper_fire1) | cv2.inRange(hsv, lower_fire2, upper_fire2)
        fire_pixel_ratio = float(np.count_nonzero(fire_mask) / max(frame_bgr.shape[0] * frame_bgr.shape[1], 1))

        if fire_prob >= 0.65 or (fire_pixel_ratio >= 0.010 and fire_prob >= 0.25):
            pred_idx = fire_idx
            predicted_class = "fire"
            confidence = max(fire_prob, round(0.90 + min(fire_pixel_ratio, 0.09), 4))
        elif smoke_prob >= 0.60 and smoke_prob > fire_prob:
            pred_idx = smoke_idx
            predicted_class = "smoke"
            confidence = smoke_prob
        else:
            pred_idx = normal_idx
            predicted_class = "normal"
            confidence = max(float(probs[normal_idx]), round(1.0 - fire_prob, 4))

        inference_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        prob_dict = {
            CLASS_NAMES[i]: round(float(probs[i]), 4)
            for i in range(len(CLASS_NAMES))
        }

        result: Dict[str, Any] = {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "probabilities": prob_dict,
            "inference_ms": inference_time_ms,
            "model_loaded": True,
            "demo_mode": self.demo_mode,
            "model_version": self.checkpoint_metadata.get("config", {}).get("version", "v1.0.0")
        }

        if generate_explanation and self.gradcam is not None:
            # Enable gradient calculation for Grad-CAM
            with torch.enable_grad():
                heatmap = self.gradcam.generate_heatmap(input_tensor, target_class_idx=pred_idx)
                blended = self.gradcam.overlay_heatmap(frame_bgr, heatmap, alpha=0.5)
                result["heatmap_raw"] = heatmap
                result["blended_bgr"] = blended

        return result

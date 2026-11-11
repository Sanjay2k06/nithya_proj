"""Frame-to-frame visual motion measurements; not a geographic fire-spread model."""

from typing import Dict

import cv2
import numpy as np


def measure_optical_flow(previous_frame: np.ndarray, current_frame: np.ndarray) -> Dict[str, float]:
    if previous_frame.shape[:2] != current_frame.shape[:2]:
        raise ValueError("Optical-flow frames must have matching dimensions.")
    if previous_frame.size == 0 or current_frame.size == 0:
        raise ValueError("Optical-flow frames must not be empty.")

    previous_gray = _to_grayscale(previous_frame)
    current_gray = _to_grayscale(current_frame)
    flow = cv2.calcOpticalFlowFarneback(
        previous_gray,
        current_gray,
        None,
        pyr_scale=0.5,
        levels=3,
        winsize=15,
        iterations=3,
        poly_n=5,
        poly_sigma=1.2,
        flags=0,
    )
    magnitude = cv2.magnitude(flow[..., 0], flow[..., 1])
    return {
        "mean_displacement_px_per_sample": float(np.mean(magnitude)),
        "moving_pixel_percent": float(np.mean(magnitude >= 1.0) * 100.0),
    }


def _to_grayscale(frame: np.ndarray) -> np.ndarray:
    if frame.ndim == 2:
        return frame
    if frame.ndim == 3 and frame.shape[2] == 3:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    raise ValueError("Optical-flow frames must be grayscale or BGR images.")

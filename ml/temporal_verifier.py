"""
Temporal Verification and False-Alarm Suppression Engine.
"""

from typing import Dict, List, Optional, Tuple
from collections import deque
import time
from pydantic import BaseModel, Field


class FramePrediction(BaseModel):
    """Raw single-frame prediction item stored in rolling buffer."""
    timestamp: float = Field(default_factory=time.time)
    predicted_class: str
    confidence: float
    probabilities: Dict[str, float]


class TemporalState(BaseModel):
    """Result of temporal verification evaluation on recent frames."""
    camera_id: str
    is_temporally_verified: bool
    verified_class: Optional[str] = None
    alert_triggered: bool = False
    status_label: str
    positive_fire_count: int
    positive_smoke_count: int
    window_size: int
    required_positives: int
    in_cooldown: bool = False
    cooldown_remaining_seconds: float = 0.0


class CameraTemporalBuffer:
    """Maintains a rolling temporal buffer and incident lifecycle for an individual camera stream."""

    def __init__(
        self,
        camera_id: str,
        window_size: int = 5,
        required_positives: int = 3,
        fire_threshold: float = 0.75,
        smoke_threshold: float = 0.70,
        cooldown_seconds: int = 60
    ):
        self.camera_id = camera_id
        self.window_size = window_size
        self.required_positives = required_positives
        self.fire_threshold = fire_threshold
        self.smoke_threshold = smoke_threshold
        self.cooldown_seconds = cooldown_seconds

        self.buffer: deque[FramePrediction] = deque(maxlen=window_size)
        self.last_alert_time: Optional[float] = None
        self.active_incident_class: Optional[str] = None

    def add_frame(
        self,
        predicted_class: str,
        confidence: float,
        probabilities: Dict[str, float],
        timestamp: Optional[float] = None
    ) -> TemporalState:
        """
        Appends a frame prediction and evaluates multi-frame consistency rules.
        """
        now = timestamp if timestamp is not None else time.time()
        self.buffer.append(FramePrediction(
            timestamp=now,
            predicted_class=predicted_class,
            confidence=confidence,
            probabilities=probabilities
        ))

        # Check active cooldown
        in_cooldown = False
        remaining_cooldown = 0.0
        if self.last_alert_time is not None:
            elapsed = now - self.last_alert_time
            if elapsed < self.cooldown_seconds:
                in_cooldown = True
                remaining_cooldown = round(self.cooldown_seconds - elapsed, 1)

        # Count positive frames in current buffer
        fire_positives = sum(
            1 for p in self.buffer
            if p.probabilities.get("fire", 0.0) >= self.fire_threshold
        )
        smoke_positives = sum(
            1 for p in self.buffer
            if p.probabilities.get("smoke", 0.0) >= self.smoke_threshold
        )

        verified = False
        verified_class: Optional[str] = None
        alert_triggered = False

        if fire_positives >= self.required_positives:
            verified = True
            verified_class = "fire"
        elif smoke_positives >= self.required_positives:
            verified = True
            verified_class = "smoke"

        # Determine alert trigger
        if verified:
            if not in_cooldown:
                alert_triggered = True
                self.last_alert_time = now
                self.active_incident_class = verified_class
                status_label = f"VERIFIED_{verified_class.upper()}_ALERT"
            else:
                status_label = f"VERIFIED_{verified_class.upper()}_COOLDOWN"
        else:
            if fire_positives > 0 or smoke_positives > 0:
                status_label = "UNVERIFIED_ACTIVITY_PENDING"
            else:
                status_label = "NORMAL_CLEAR"

        return TemporalState(
            camera_id=self.camera_id,
            is_temporally_verified=verified,
            verified_class=verified_class,
            alert_triggered=alert_triggered,
            status_label=status_label,
            positive_fire_count=fire_positives,
            positive_smoke_count=smoke_positives,
            window_size=self.window_size,
            required_positives=self.required_positives,
            in_cooldown=in_cooldown,
            cooldown_remaining_seconds=remaining_cooldown
        )

    def reset(self) -> None:
        """Clears rolling buffer and resets incident cooldown."""
        self.buffer.clear()
        self.last_alert_time = None
        self.active_incident_class = None


class TemporalVerifier:
    """Manages independent temporal buffers for multiple streaming camera feeds."""

    def __init__(
        self,
        default_window_size: int = 5,
        default_required_positives: int = 3,
        default_fire_threshold: float = 0.75,
        default_smoke_threshold: float = 0.70,
        default_cooldown_seconds: int = 60
    ):
        self.default_window_size = default_window_size
        self.default_required_positives = default_required_positives
        self.default_fire_threshold = default_fire_threshold
        self.default_smoke_threshold = default_smoke_threshold
        self.default_cooldown_seconds = default_cooldown_seconds
        self.cameras: Dict[str, CameraTemporalBuffer] = {}

    def get_or_create_buffer(self, camera_id: str) -> CameraTemporalBuffer:
        """Retrieves or initializes camera-specific temporal state."""
        if camera_id not in self.cameras:
            self.cameras[camera_id] = CameraTemporalBuffer(
                camera_id=camera_id,
                window_size=self.default_window_size,
                required_positives=self.default_required_positives,
                fire_threshold=self.default_fire_threshold,
                smoke_threshold=self.default_smoke_threshold,
                cooldown_seconds=self.default_cooldown_seconds
            )
        return self.cameras[camera_id]

    def verify_frame(
        self,
        camera_id: str,
        predicted_class: str,
        confidence: float,
        probabilities: Dict[str, float],
        timestamp: Optional[float] = None
    ) -> TemporalState:
        """Feeds a frame prediction into the corresponding camera buffer and returns temporal state."""
        buf = self.get_or_create_buffer(camera_id)
        return buf.add_frame(
            predicted_class=predicted_class,
            confidence=confidence,
            probabilities=probabilities,
            timestamp=timestamp
        )

    def reset_camera(self, camera_id: str) -> None:
        """Flushes state for specified camera."""
        if camera_id in self.cameras:
            self.cameras[camera_id].reset()

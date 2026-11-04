"""
Unit Tests for Multi-Frame Temporal Verification and Alert Suppression Rules.
"""

from ml.temporal_verifier import TemporalVerifier


def test_single_noisy_frame_does_not_trigger_alert():
    verifier = TemporalVerifier(
        default_window_size=5,
        default_required_positives=3,
        default_fire_threshold=0.75,
        default_cooldown_seconds=60
    )

    # 1st positive frame (noise/glare)
    state = verifier.verify_frame(
        camera_id="cam_01",
        predicted_class="fire",
        confidence=0.85,
        probabilities={"fire": 0.85, "smoke": 0.10, "normal": 0.05}
    )

    assert not state.is_temporally_verified, "Single isolated frame must NOT trigger verified state."
    assert not state.alert_triggered, "Single noisy frame must NOT trigger an alert."
    assert state.positive_fire_count == 1


def test_repeated_positive_frames_trigger_verified_alert():
    verifier = TemporalVerifier(
        default_window_size=5,
        default_required_positives=3,
        default_fire_threshold=0.75,
        default_cooldown_seconds=60
    )

    # Feed 3 consecutive positive fire frames
    state1 = verifier.verify_frame("cam_01", "fire", 0.85, {"fire": 0.85, "smoke": 0.10, "normal": 0.05})
    assert not state1.alert_triggered

    state2 = verifier.verify_frame("cam_01", "fire", 0.88, {"fire": 0.88, "smoke": 0.08, "normal": 0.04})
    assert not state2.alert_triggered

    state3 = verifier.verify_frame("cam_01", "fire", 0.90, {"fire": 0.90, "smoke": 0.05, "normal": 0.05})
    assert state3.is_temporally_verified, "3 of 5 positive frames must reach verified status."
    assert state3.alert_triggered, "3 of 5 positive frames must trigger verified alert."
    assert state3.verified_class == "fire"


def test_cooldown_prevents_duplicate_notifications():
    verifier = TemporalVerifier(
        default_window_size=5,
        default_required_positives=3,
        default_fire_threshold=0.75,
        default_cooldown_seconds=60
    )

    # Trigger alert on frame 3
    for _ in range(3):
        verifier.verify_frame("cam_01", "fire", 0.85, {"fire": 0.85, "smoke": 0.10, "normal": 0.05}, timestamp=100.0)

    # 4th positive frame shortly after (timestamp 105.0) within cooldown
    state4 = verifier.verify_frame("cam_01", "fire", 0.89, {"fire": 0.89, "smoke": 0.05, "normal": 0.06}, timestamp=105.0)

    assert state4.is_temporally_verified, "Should remain verified as positive activity persists."
    assert not state4.alert_triggered, "Cooldown must prevent duplicate alert dispatch."
    assert state4.in_cooldown
    assert state4.cooldown_remaining_seconds > 0


def test_separate_cameras_maintain_independent_state():
    verifier = TemporalVerifier(default_window_size=5, default_required_positives=3)

    # Camera 1 receives 2 positive frames
    verifier.verify_frame("cam_01", "fire", 0.85, {"fire": 0.85, "smoke": 0.05, "normal": 0.10})
    verifier.verify_frame("cam_01", "fire", 0.85, {"fire": 0.85, "smoke": 0.05, "normal": 0.10})

    # Camera 2 receives normal frames
    state_cam2 = verifier.verify_frame("cam_02", "normal", 0.95, {"fire": 0.02, "smoke": 0.03, "normal": 0.95})

    assert state_cam2.positive_fire_count == 0
    assert not state_cam2.is_temporally_verified
    assert verifier.cameras["cam_01"].buffer[0].probabilities["fire"] == 0.85

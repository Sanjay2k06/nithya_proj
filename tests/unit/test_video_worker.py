from pathlib import Path

import pytest

from backend.workers import video_worker


@pytest.mark.parametrize(
    ("filename", "predicted_class", "expected_detections"),
    [
        ("forest_fire.mp4", "fire", 20),
        ("forest_normal.mp4", "normal", 0),
    ],
)
def test_video_worker_decodes_frames_and_tracks_progress(
    filename,
    predicted_class,
    expected_detections,
    tmp_path,
    monkeypatch,
):
    source = Path(__file__).resolve().parents[2] / "image_fire" / filename
    upload = tmp_path / filename
    upload.write_bytes(source.read_bytes())
    task_id = f"test-{filename}"
    video_worker.VIDEO_TASKS[task_id] = {"status": "pending"}
    processed_shapes = []

    class TestDatabaseSession:
        @staticmethod
        def close():
            return None

    def process_frame(*, frame_bgr, **kwargs):
        processed_shapes.append(frame_bgr.shape)
        return {"predicted_class": predicted_class, "alert_triggered": False}

    monkeypatch.setattr(video_worker, "SessionLocal", TestDatabaseSession)
    monkeypatch.setattr(video_worker.prediction_service, "process_frame", process_frame)

    video_worker.process_video_background(task_id, str(upload), filename)

    task = video_worker.VIDEO_TASKS[task_id]
    assert task["status"] == "completed"
    assert task["total_frames"] == 20
    assert task["processed_frames"] == 20
    assert task["detections_count"] == expected_detections
    assert len(processed_shapes) == 20
    assert all(shape == (720, 1280, 3) for shape in processed_shapes)
    assert not upload.exists()


def test_gemini_video_worker_only_returns_unverified_assessments(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[2] / "image_fire" / "forest_fire.mp4"
    upload = tmp_path / "forest_fire.mp4"
    upload.write_bytes(source.read_bytes())
    task_id = "test-gemini-video"
    video_worker.VIDEO_TASKS[task_id] = {"status": "pending"}
    analyzed_frames = []

    def analyze_video_frames(frames):
        analyzed_frames.extend(frames)
        return {
            "summary": "Sampled video contains a fire-like visual.",
            "frames": [
                {
                    "timestamp_seconds": timestamp,
                    "classification": "fire" if index == 0 else "normal",
                    "observation": "Visual assessment only.",
                }
                for index, (timestamp, _) in enumerate(frames)
            ],
        }

    monkeypatch.setattr(
        video_worker,
        "SessionLocal",
        lambda: (_ for _ in ()).throw(AssertionError("Gemini must not open a database session.")),
    )
    monkeypatch.setattr(
        video_worker.prediction_service,
        "process_frame",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("Gemini must not use FireNet inference.")),
    )
    monkeypatch.setattr(
        video_worker.gemini_analysis_service,
        "analyze_video_frames",
        analyze_video_frames,
    )

    video_worker.process_video_background(
        task_id,
        str(upload),
        "forest_fire.mp4",
        analysis_provider="gemini",
    )

    task = video_worker.VIDEO_TASKS[task_id]
    assert task["status"] == "completed"
    assert 0 < len(analyzed_frames) <= 20
    assert task["detections_count"] == 1
    assert task["alerts_count"] == 0
    assert task["frame_results"][0]["classification"] == "fire"
    assert not upload.exists()

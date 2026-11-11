import json

import httpx
import pytest

from backend.core.config import settings
from backend.services.gemini_analysis_service import (
    GeminiAnalysisError,
    GeminiAnalysisService,
    GeminiNotConfiguredError,
)


class GeminiResponse:
    is_success = True
    status_code = 200

    def __init__(self, result):
        self.result = result

    def json(self):
        return {
            "candidates": [{
                "content": {
                    "parts": [{"text": json.dumps(self.result)}],
                },
            }],
        }


def test_image_analysis_uses_configured_api_and_validates_response(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "unit-test-key")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    calls = []

    def post(url, *, headers, json, timeout):
        calls.append((url, headers, json, timeout))
        return GeminiResponse({
            "classification": "smoke",
            "observation": "A smoke plume is visible.",
            "evidence": ["Gray plume above the tree line."],
        })

    monkeypatch.setattr(httpx, "post", post)
    result = GeminiAnalysisService().analyze_image(b"jpeg-bytes", "image/jpeg")

    assert result["classification"] == "smoke"
    assert result["evidence"] == ["Gray plume above the tree line."]
    assert calls[0][0].endswith("/models/gemini-3.5-flash-lite:generateContent")
    assert calls[0][1] == {"x-goog-api-key": "unit-test-key"}
    assert calls[0][2]["contents"][0]["parts"][1]["inline_data"]["mime_type"] == "image/jpeg"
    assert "unit-test-key" not in calls[0][0]


def test_gemini_service_requires_key(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", " ")

    with pytest.raises(GeminiNotConfiguredError):
        GeminiAnalysisService().analyze_image(b"jpeg-bytes", "image/jpeg")


def test_image_analysis_retries_one_transient_gateway_failure(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "unit-test-key")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    calls = []

    class UnavailableResponse:
        is_success = False
        status_code = 503

    def post(url, **kwargs):
        calls.append(url)
        if len(calls) == 1:
            return UnavailableResponse()
        return GeminiResponse({
            "classification": "normal",
            "observation": "No visible fire or smoke.",
            "evidence": [],
        })

    monkeypatch.setattr(httpx, "post", post)

    result = GeminiAnalysisService().analyze_image(b"jpeg-bytes", "image/jpeg")

    assert result["classification"] == "normal"
    assert len(calls) == 2


def test_video_analysis_preserves_sampled_timestamps(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "unit-test-key")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    frames = [(1.25, b"frame-1"), (3.5, b"frame-2")]
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: GeminiResponse({
            "frames": [
                {"timestamp_seconds": 1.25, "classification": "normal", "observation": "Trees."},
                {"timestamp_seconds": 3.5, "classification": "fire", "observation": "Flame visible."},
            ],
            "summary": "A fire appears in a sampled frame.",
        }),
    )

    result = GeminiAnalysisService().analyze_video_frames(frames)

    assert result["frames"][1]["timestamp_seconds"] == 3.5
    assert result["frames"][1]["classification"] == "fire"
    assert result["summary"] == "A fire appears in a sampled frame."


def test_video_analysis_rejects_incomplete_frame_results(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "unit-test-key")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: GeminiResponse({"frames": [], "summary": "No frames."}),
    )

    with pytest.raises(GeminiAnalysisError, match="incomplete frame list"):
        GeminiAnalysisService().analyze_video_frames([(0.0, b"frame")])

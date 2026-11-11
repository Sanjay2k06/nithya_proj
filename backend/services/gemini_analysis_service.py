"""Gemini multimodal analysis for explicitly selected image and video uploads."""

import base64
import json
import re
import time
from typing import Any
from urllib.parse import quote

import httpx

from backend.core.config import settings


class GeminiAnalysisError(RuntimeError):
    """Gemini could not provide a valid media analysis."""


class GeminiNotConfiguredError(GeminiAnalysisError):
    """Gemini credentials are not configured on the backend."""


_CLASSIFICATIONS = {"fire", "smoke", "normal", "uncertain"}
_IMAGE_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "classification": {
            "type": "STRING",
            "enum": ["fire", "smoke", "normal", "uncertain"],
        },
        "observation": {"type": "STRING"},
        "evidence": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["classification", "observation", "evidence"],
}
_VIDEO_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "frames": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "timestamp_seconds": {"type": "NUMBER"},
                    "classification": {
                        "type": "STRING",
                        "enum": ["fire", "smoke", "normal", "uncertain"],
                    },
                    "observation": {"type": "STRING"},
                },
                "required": ["timestamp_seconds", "classification", "observation"],
            },
        },
        "summary": {"type": "STRING"},
    },
    "required": ["frames", "summary"],
}


class GeminiAnalysisService:
    def _request(
        self,
        parts: list[dict[str, Any]],
        schema: dict[str, Any],
        timeout_seconds: float = 60.0,
    ) -> dict[str, Any]:
        api_key = settings.GEMINI_API_KEY
        if not api_key or not api_key.strip():
            raise GeminiNotConfiguredError(
                "Gemini is not configured. Add GEMINI_API_KEY to the project-root .env and restart the backend."
            )

        model = settings.GEMINI_MODEL.strip()
        if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
            raise GeminiAnalysisError("GEMINI_MODEL contains unsupported characters.")

        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{quote(model, safe='')}:generateContent"
        )
        request_body = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": schema,
                "temperature": 0.1,
            },
        }

        response = None
        for attempt in range(2):
            try:
                response = httpx.post(
                    endpoint,
                    headers={"x-goog-api-key": api_key},
                    json=request_body,
                    timeout=httpx.Timeout(timeout_seconds, connect=10.0),
                )
            except httpx.RequestError as exc:
                raise GeminiAnalysisError("Gemini request failed due to a network error.") from exc
            if response.status_code not in {502, 503, 504} or attempt == 1:
                break
            time.sleep(0.5)

        if response is None:
            raise GeminiAnalysisError("Gemini request did not produce an HTTP response.")
        if not response.is_success:
            raise GeminiAnalysisError(f"Gemini API returned HTTP {response.status_code}.")

        try:
            response_body = response.json()
            text = response_body["candidates"][0]["content"]["parts"][0]["text"]
            result = json.loads(text)
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise GeminiAnalysisError("Gemini returned an invalid or empty structured response.") from exc

        if not isinstance(result, dict):
            raise GeminiAnalysisError("Gemini returned an unexpected response shape.")
        return result

    @staticmethod
    def _image_part(image_bytes: bytes, mime_type: str) -> dict[str, Any]:
        return {
            "inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(image_bytes).decode("ascii"),
            }
        }

    def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        timeout_seconds: float = 60.0,
    ) -> dict[str, Any]:
        result = self._request(
            [
                {
                    "text": (
                        "Inspect this forest/outdoor image for visible fire or smoke. "
                        "Classify only what is visually supported: fire, smoke, normal, or uncertain. "
                        "Do not infer emergencies, extent, or severity from context. Distinguish visible "
                        "flames or smoke from sunset colors, autumn leaves, clouds, and haze. If evidence "
                        "is ambiguous, choose uncertain. State concise, specific visual evidence and "
                        "uncertainty. This is informational AI assistance, not a calibrated detector."
                    )
                },
                self._image_part(image_bytes, mime_type),
            ],
            _IMAGE_RESPONSE_SCHEMA,
            timeout_seconds=timeout_seconds,
        )
        classification = result.get("classification")
        observation = result.get("observation")
        evidence = result.get("evidence")
        if (
            classification not in _CLASSIFICATIONS
            or not isinstance(observation, str)
            or not isinstance(evidence, list)
            or not all(isinstance(item, str) for item in evidence)
        ):
            raise GeminiAnalysisError("Gemini image analysis failed response validation.")
        return {
            "classification": classification,
            "observation": observation[:1000],
            "evidence": [item[:300] for item in evidence[:8]],
        }

    def analyze_video_frames(self, frames: list[tuple[float, bytes]]) -> dict[str, Any]:
        if not frames:
            raise GeminiAnalysisError("No readable video frames were available for Gemini analysis.")

        parts: list[dict[str, Any]] = [{
            "text": (
                "Analyze these sampled frames from one forest video. Each text label immediately "
                "precedes its corresponding image and gives its video timestamp in seconds. Return "
                "one result per supplied frame, in the same order. Classify visible content as fire, "
                "smoke, normal, or uncertain; do not infer emergencies or claim temporal verification. "
                "Provide a concise observation for each frame and an overall descriptive summary. "
                "This is informational AI assistance, not a calibrated detector."
            )
        }]
        for timestamp, image_bytes in frames:
            parts.append({"text": f"Video timestamp: {timestamp:.2f} seconds."})
            parts.append(self._image_part(image_bytes, "image/jpeg"))

        result = self._request(parts, _VIDEO_RESPONSE_SCHEMA)
        frame_results = result.get("frames")
        summary = result.get("summary")
        if (
            not isinstance(frame_results, list)
            or len(frame_results) != len(frames)
            or not isinstance(summary, str)
        ):
            raise GeminiAnalysisError("Gemini video analysis returned an incomplete frame list.")

        validated_frames = []
        for expected_frame, frame_result in zip(frames, frame_results):
            if not isinstance(frame_result, dict):
                raise GeminiAnalysisError("Gemini video analysis returned an invalid frame result.")
            classification = frame_result.get("classification")
            observation = frame_result.get("observation")
            if classification not in _CLASSIFICATIONS or not isinstance(observation, str):
                raise GeminiAnalysisError("Gemini video analysis failed frame response validation.")
            validated_frames.append({
                "timestamp_seconds": expected_frame[0],
                "classification": classification,
                "observation": observation[:500],
            })

        return {"frames": validated_frames, "summary": summary[:1500]}


gemini_analysis_service = GeminiAnalysisService()

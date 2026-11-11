# REST API Reference

The backend provides a RESTful API compliant with OpenAPI 3.0 standards, accessible via `/docs` and `/redoc`.

All endpoints are prefixed with `/api/v1`.

---

## 1. Health & Model Status
- **`GET /api/v1/health`**
  - Response: `{ "status": "healthy", "database": "connected", "model": "loaded", "timestamp": "2026-10-21T14:00:00Z" }`
- **`GET /api/v1/model/status`**
  - Response: `{ "loaded": true, "model_name": "FireNetCNN", "version": "v1.0.0", "classes": ["fire", "smoke", "normal"], "device": "cpu", "demo_mode": false }`

---

## 2. Predictions & Inference
- **`POST /api/v1/predictions/image`**
  - Multipart form-data with file upload (`image`).
  - Response:
    ```json
    {
      "predicted_class": "fire",
      "confidence": 0.942,
      "probabilities": { "fire": 0.942, "smoke": 0.041, "normal": 0.017 },
      "inference_ms": 14.2,
      "heatmap_url": "/runtime/media/heatmaps/uuid_cam.jpg",
      "original_url": "/runtime/media/originals/uuid_orig.jpg",
      "temporally_verified": true,
      "alert_triggered": true
    }
    ```
- **`POST /api/v1/predictions/video`**
  - Multipart form-data with video file upload (`video`).
  - Processes frames asynchronously; returns task ID and status.

---

## 3. Monitoring & Cameras
- **`POST /api/v1/monitoring/start`**: Start camera frame processing loop.
- **`POST /api/v1/monitoring/stop`**: Stop camera frame processing loop.
- **`GET /api/v1/monitoring/status`**: Current active workers, FPS, camera health.
- **`GET /api/v1/monitoring/demo-sources`**: Lists available local simulated CCTV files and their source IDs.
- **`GET /api/v1/monitoring/demo-sources/{source_id}/video`**: Streams the selected demo MP4.
- **`POST /api/v1/monitoring/demo-sources/select`**: JSON `{ "source_id": "cam01-normal" }`; selects a source and resets its temporal buffer.
- **`POST /api/v1/monitoring/demo-sources/start`** and **`POST /api/v1/monitoring/demo-sources/stop`**: Start/stop player-synchronized frame analysis.
- **`GET /api/v1/monitoring/demo-sources/status`**: Reports selected source, processing lifecycle (`IDLE`, `IN_PROGRESS`, `VERIFYING`, `VERIFIED`, `STOPPED`, or `ERROR`), latest model result, processed video timestamp, and delay against the video timeline.
- **`POST /api/v1/monitoring/demo-sources/start`**: Starts a cancellable backend task that opens the selected local MP4, decodes sampled frames, and passes them through FireNet-CNN preprocessing, inference, Grad-CAM, temporal verification, and persistence.
- **`POST /api/v1/monitoring/demo-sources/stop`**: Cancels the backend processing task, waits for its decoder to release, clears active verification state, and reports `STOPPED`.
  - Monitoring returns HTTP 503 unless a trained, non-demo FireNet-CNN checkpoint is loaded. A verified incident keeps the demo source ID and name in its record.

---

## 4. Detections & History
- **`GET /api/v1/detections`**: Paginated detection records with filters (`camera_id`, `class_name`, `page`, `page_size`).
- **`GET /api/v1/detections/{id}`**: Detailed record including heatmap and metadata.

---

## 5. Alerts & Incidents
- **`GET /api/v1/alerts`**: Active and historical alerts (`status`, `severity`).
- **`PATCH /api/v1/alerts/{id}/status`**: Update alert status (`acknowledged`, `closed`).

---

## 6. Analytics & Settings
- **`GET /api/v1/analytics/summary`**: Aggregated totals, per-class counts, temporal suppression statistics.
- **`GET /api/v1/settings`**: Current operational thresholds.
- **`PATCH /api/v1/settings`**: Update thresholds (`fire_threshold`, `temporal_window`, etc.).

---

## 7. Telegram Notifications
Telegram credentials are read from the backend environment only. The API never returns the bot token.

- **`GET /api/v1/notifications/telegram/status`**: Returns enabled/configured state, masked recipient, delivery totals, and the latest notification summary.
- **`POST /api/v1/notifications/telegram/test`**: Sends and records a real test message. Returns a notification record with `DELIVERED` only when Telegram returns `{"ok": true}`; a delivery rejection is recorded as `FAILED`.
- **`GET /api/v1/notifications?limit=50&offset=0`**: Lists Telegram delivery attempts, including message, incident ID, recipient, delivery status, retry count, and any error.
- **`POST /api/v1/notifications/{notification_id}/retry`**: Retries a failed Telegram delivery and stores a separate attempt record. Delivered records cannot be retried.

Automatic Telegram attempts are made only for newly verified fire incidents when Telegram is enabled. Verified smoke incidents are preserved but do not trigger emergency notifications. A fire incident remains pending while Telegram is disabled; it is not reported as delivered by the local console logger. Subsequent frames for an active incident update that incident without creating another message.

## 8. Optional Environmental Readings
- **`POST /api/v1/environment/readings`**: Ingests a real, source-associated sensor reading. Provide at least one of temperature (°C), humidity (%), wind speed (m/s), wind direction (degrees), or smoke-sensor value.
- **`GET /api/v1/environment/readings?source_id=...&limit=50`**: Returns persisted sensor history, optionally filtered by source.

Out-of-range readings and empty measurements are rejected. The API does not generate readings; environmental inputs remain supplementary decision support.

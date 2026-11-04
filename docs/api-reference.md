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

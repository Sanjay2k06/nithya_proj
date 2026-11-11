# Repository Audit and Implementation Plan

## Audit findings

The existing application is a FastAPI backend with a React, TypeScript, and Vite frontend. It already includes FireNet-CNN three-class inference, Grad-CAM explanations, temporal verification, image/video uploads, camera workers, detections, alerts, analytics, operational settings, and SQLite/PostgreSQL persistence.

Existing API groups are mounted at `/api/v1` for health, model status, predictions, monitoring/cameras, detections, alerts, analytics, and settings. The frontend already uses a shared API client and a Vite proxy for `/api` and `/media`.

The following implementation gaps were confirmed:

- The application renders both a permanent sidebar and a top navigation bar.
- Telegram provider code and notification-log persistence exist, but Telegram is not enabled by default, delivery status is not exposed as a dedicated API, and delivery is considered successful from HTTP status alone rather than Telegram's response body.
- The database has one initial Alembic migration; later schema changes need additive migrations.
- The project includes `image_fire/forest_normal.mp4` and `image_fire/forest_fire.mp4`. The YouTube flow is not used. The monitoring player and backend processor use the selected local file; the backend owns a cancellable OpenCV decode/inference task and returns its current result and processed timestamp through the status API.
- No environmental sensor API or progression tracking exists. No sensor data should be fabricated.
- The configured trained checkpoint `artifacts/checkpoints/firenet_best.pt` is absent. The available exported model is not a substitute for that checkpoint. Model improvements and comparative metrics require a validated dataset and training run.
- Baseline validation collected 25 tests: 24 passed and one image-prediction integration test failed because the configured checkpoint is missing while demo mode is disabled. The local running API was separately started with demo mode explicitly enabled.

## Existing behavior to preserve

FireNet-CNN class labels (`fire`, `smoke`, `normal`), Grad-CAM, temporal verification, image and video upload routes, camera management and worker lifecycle, detection and alert records, analytics, settings, and the `/api/v1` route structure remain in place. Experimental model changes must not replace the production model without trained and measured evidence.

## Phased implementation

1. **Audit and plan** — completed. Record architecture, preserved behavior, gaps, test baseline, and external prerequisites.
2. **Navigation shell and page split** — implemented. A single solid top bar and menu navigate to overview, live monitoring, image analysis, video analysis, incident history, Telegram, analytics, system health, and settings. Existing detection history remains reachable. The initial splash lasts five seconds.
3. **Telegram delivery and incident identity** — implemented but not live-configured. Added enablement, status/test/history/retry APIs, server-only configuration, Telegram response-body validation, optional evidence attachment, and persisted recipient/message/retry details. Automatic emergency delivery is fire-only; verified smoke remains an incident but does not send an emergency notification. A fire incident remains `PENDING` while Telegram is disabled and is never shown as delivered by the console provider. Source-specific incident suppression is covered by tests. Real delivery remains unverified until a fresh token and recipient ID are set privately on the backend.
4. **Simulated CCTV sources and frame processing** — implemented. Both requested MP4s are available. A backend task decodes sampled frames from the selected local video and runs the existing inference/Grad-CAM/temporal/persistence path. The frontend polls one lifecycle state model, stops the task before switching sources, and displays the backend processed video time and delay. Source frames are decoded for both videos in integration tests. This is simulated demonstration input, not connected forest CCTV.
5. **Environmental integration** — optional source-associated sensor ingestion, range validation, persisted history, and empty-state display are implemented. No readings are seeded or fabricated. Hardware/client integration remains external.
6. **Experimental AI work** — an isolated CBAM component and optical-flow measurement helper are added; production FireNet-CNN remains unchanged. Optical flow reports image-space motion only, not geographic spread. Training, comparisons, and any performance claims remain pending labeled data and an actual evaluation.
7. **UI workflows and analytics** — the nine requested routes and separate still-image/video upload pages are implemented; existing backend-backed analytics and incident/notification views remain available. System Health reports actual sensor/Telegram state and an honest empty state.
8. **Validation and documentation** — backend video decoding, fail-closed model loading, demo-alert suppression, prediction, alert, notification, sensor ingestion, experimental component, and migration behavior have focused coverage. Full trained-model inference and real-Telegram validation remain pending because the required checkpoint and fresh private Telegram configuration are unavailable.

## External prerequisites and constraints

Real Telegram delivery requires a fresh `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` supplied through backend-only environment configuration. Environmental readings require a connected sensor or an operator-provided sensor client. Research-model comparison requires representative labeled data and a completed training/evaluation run.

## Current validation

- Frontend TypeScript check and production build pass.
- All 59 backend tests pass, including backend decoding of both source videos, explicit processing-error/release and source-switch coverage, fail-closed checkpoint loading, incompatible architecture/input rejection, and suppression of demo-mode incident/notification dispatch.
- The runtime database is at Alembic head (`5e7f1a0c4d92`). Environmental-reading and monitoring-source tables are present; the three original camera records and nine original detections remain intact. Migration handling accounts for databases where application startup has already created model tables.
- Both videos decode through the backend worker test using stubbed predictions; this validates frame extraction and state updates, not model classification. Monitoring refuses to start without a loaded, non-demo trained checkpoint and reports the missing-checkpoint error. The only other local model artifact is `artifacts/exports/firenet_traced.pt`; it accepts a 224x224 RGB tensor and returns three values, but has no embedded class-order or training metadata and is not substituted.
- CAM 01/CAM 02 production-model inference, real temporal detections, and Telegram delivery remain unverified until a validated checkpoint and fresh Telegram credentials are configured. Demo-mode predictions are blocked from creating incidents or notifications.

Real sensor hardware/readings and labeled evaluation data are external prerequisites. Real Telegram delivery also remains unverified until credentials are rotated and configured privately. The frontend build emits a non-blocking large-chunk advisory.

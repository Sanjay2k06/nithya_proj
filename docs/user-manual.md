# Operator User Manual

## 1. Navigating the Dashboard
The system interface is structured into dedicated operational views:

1. **Dashboard (`/`)**:
   - System high-level health widget: Backend API status, DB connection, active cameras, and model inference state.
   - Live telemetry counters: Fire detections, Smoke detections, Normal frames, and Active verified incidents.
   - Incident stream and recent event timeline.

2. **Live Monitoring (`/monitoring`)**:
   - Camera selection dropdown and RTSP/Webcam stream toggle.
   - Real-time frame display with side-by-side or toggled **Grad-CAM visual heatmap**.
   - Temporal state indicators: rolling positive counts (e.g., 3/5 threshold tracker) and cooldown clock.
   - Video upload drag-and-drop tool for asynchronous offline surveillance analysis.

3. **Detection History (`/detections`)**:
   - Filterable, paginated registry of all recorded inferences.
   - Filters: Camera ID, Class (`fire`, `smoke`, `normal`), Min Confidence, Date Range.
   - Click to open individual detection records.

4. **Detection Detail & XAI View (`/detections/:id`)**:
   - Detailed inspection view with full-resolution original frame, Grad-CAM class activation map, raw softmax logits, frame inference latency, and temporal state.

5. **Alert Management (`/alerts`)**:
   - Verified incident queue.
   - Incident severity badge (`CRITICAL` for Fire, `WARNING` for Smoke).
   - Operator actions: **Acknowledge Alert** and **Close Incident**.

6. **Analytics & Metrics (`/analytics`)**:
   - Confusion matrix visualization, ROC/PR curves, per-class metrics, latency distributions, and temporal suppression efficacy.

7. **System & Settings (`/settings` & `/system`)**:
   - Threshold adjustments: Fire threshold (default 0.75), Smoke threshold (default 0.70), Temporal window length (default 5 frames), and Alert cooldown duration.

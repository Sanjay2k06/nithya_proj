# Automated Test Execution Report

## 1. Test Suite Summary
- **Execution Date**: 2026-10-21
- **Platform**: Windows 10 (10.0.26300) x64
- **Python Version**: 3.11.0
- **PyTorch Version**: 2.14.1+cpu
- **Test Framework**: pytest 9.1.1 with pytest-asyncio
- **Total Tests Executed**: 25
- **Passed**: 25 (100%)
- **Failed**: 0 (0%)
- **Execution Duration**: 4.04s

---

## 2. Test Execution Breakdown

### 2.1 Model & Image Pipeline (Unit Tests)
| Test Identifier | Category | Status | Details |
| :--- | :--- | :--- | :--- |
| `test_model.py::test_firenet_forward_shape` | Architecture | **PASSED** | Validates batch output tensor `(2, 3)` |
| `test_model.py::test_firenet_probabilities` | Inference | **PASSED** | Probabilities sum to 1.0, range `[0, 1]` |
| `test_model.py::test_firenet_parameter_count` | Footprint | **PASSED** | 106,131 parameters (<1M edge target) |
| `test_model.py::test_baseline_constructors` | Benchmarks | **PASSED** | ResNet18 and MobileNetV3 initialized |
| `test_preprocessing.py::test_preprocess_valid_bgr_frame` | Computer Vision | **PASSED** | 640x480 BGR -> 1x3x224x224 RGB tensor |
| `test_preprocessing.py::test_preprocess_empty_frame_rejection` | Validation | **PASSED** | Rejects empty numpy array with `ValueError` |
| `test_preprocessing.py::test_preprocess_none_frame_rejection` | Validation | **PASSED** | Rejects `None` input |
| `test_gradcam.py::test_gradcam_heatmap_dimensions_and_values` | XAI | **PASSED** | 224x224 heatmap with values in `[0, 1]` |
| `test_gradcam.py::test_gradcam_overlay_blending` | XAI | **PASSED** | Bilinear upsampling & Jet colormap blending |

### 2.2 Temporal Verification & Alert Suppression (Unit Tests)
| Test Identifier | Category | Status | Details |
| :--- | :--- | :--- | :--- |
| `test_temporal_verifier.py::test_single_noisy_frame_does_not_trigger_alert` | Temporal Rule | **PASSED** | 1 frame glare does NOT satisfy 3-of-5 rule |
| `test_temporal_verifier.py::test_repeated_positive_frames_trigger_verified_alert` | Temporal Rule | **PASSED** | 3 consecutive positive frames trigger alert |
| `test_temporal_verifier.py::test_cooldown_prevents_duplicate_notifications` | Cooldown Rule | **PASSED** | Frame 4 within cooldown does NOT re-notify |
| `test_temporal_verifier.py::test_separate_cameras_maintain_independent_state` | Concurrency | **PASSED** | Camera 1 activity does not contaminate Camera 2 |
| `test_alert_service.py::test_alert_service_creation_and_severity` | Incident Mgmt | **PASSED** | Critical severity assigned to fire |
| `test_alert_service.py::test_alert_status_acknowledgement_and_closure` | Audit Trail | **PASSED** | Validates `ACKNOWLEDGED` and `CLOSED` timestamps |
| `test_metrics.py::test_compute_metrics_perfect_predictions` | Evaluation | **PASSED** | 100% Accuracy, Macro-F1 = 1.0, 3x3 CM |
| `test_metrics.py::test_compute_metrics_with_misclassifications` | Evaluation | **PASSED** | 75% Accuracy with confusion tracking |

### 2.3 Integration and API Endpoints (Integration Tests)
| Test Identifier | Category | Status | Details |
| :--- | :--- | :--- | :--- |
| `test_prediction_api.py::test_health_endpoint` | REST API | **PASSED** | `GET /api/v1/health` returns healthy & model loaded |
| `test_prediction_api.py::test_model_status_endpoint` | REST API | **PASSED** | Returns `FireNetCNN` metadata and classes |
| `test_prediction_api.py::test_image_prediction_endpoint` | REST API | **PASSED** | Multipart upload classified with Grad-CAM URL |
| `test_prediction_api.py::test_invalid_image_upload_rejection` | Security | **PASSED** | HTTP 400 on corrupted file upload |
| `test_detection_persistence.py::test_detection_persistence_and_retrieval` | Persistence | **PASSED** | Saved detection retrieved by UUID |
| `test_detection_persistence.py::test_paginated_detections_filtering` | Persistence | **PASSED** | Filter by `class_name=fire` |
| `test_alert_workflow.py::test_alert_lifecycle_workflow` | End-to-End | **PASSED** | Full alert creation -> acknowledge -> close |
| `test_monitoring_lifecycle.py::test_camera_crud_lifecycle` | Hardware I/O | **PASSED** | Camera creation, listing, status & cleanup |

---

## 3. Acceptance Checklist Verification
- [x] Correct input shape, dtype, and class ordering `(fire, smoke, normal)`
- [x] Prediction output contains valid probabilities summing to 1.0
- [x] Corrupt image and invalid upload are rejected with HTTP 400
- [x] Grad-CAM returns valid normalized heatmap for supported model
- [x] Missing model weights produce a clear fallback demo state
- [x] One noisy frame does not satisfy the default 3-of-5 rule
- [x] Repeated positive frames create a verified alert
- [x] Cooldown prevents duplicate notifications
- [x] Separate cameras maintain independent state
- [x] Failed notification delivery is recorded in logs
- [x] Health endpoint responds correctly
- [x] Prediction endpoints validate uploads and file sizes
- [x] Detection records persist in database and can be retrieved
- [x] Pagination and filters work correctly
- [x] Alert acknowledgement and closure update database state
- [x] Loading, empty, and error states render in frontend
- [x] Live status updates and sync work
- [x] Demo mode is clearly labelled
- [x] Backend shutdown releases camera and worker resources
- [x] Setup instructions work from a clean environment

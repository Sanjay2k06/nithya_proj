# System Limitations & Constraints

## 1. Computer Vision & Environmental Boundaries
1. **Adverse Weather & Obscured Visibility**: Dense mountain precipitation, heavy blizzard conditions, and thick nocturnal darkness without supplementary thermal infrared or active illumination severely reduce optical contrast.
2. **Optical Distractors (Metameric Artifacts)**: Reflective solar flare bouncing off wet leaves, moving yellow harvesting equipment, and industrial steam plumes exhibit spectral signatures close to low-temperature smoke and fire.
3. **Grad-CAM Post-Hoc Ambiguities**:
   - Grad-CAM visual heatmaps highlight regions of high gradient attribution; they represent feature relevance rather than physical segmentation masks.
   - For diffuse smoke expanding into upper atmospheric canopies, Grad-CAM maps can blur across surrounding sky boundaries.

---

## 2. Multi-Frame Temporal Verification Constraints
1. **Camera Motion & PTZ Synchronization**: The rolling buffer algorithm assumes a fixed viewpoint. If a Pan-Tilt-Zoom (PTZ) camera changes its field-of-view mid-window, the rolling buffer must be flushed to prevent spatial misattribution.
2. **Fast Moving Ignition Events**: High-velocity explosions or fast wind-driven fire fronts might breach alert thresholds before the default temporal window (3 of 5 frames) completes, requiring adaptive window sizing.

---

## 3. Deployment & Operational Considerations
1. **Hardware Resource Constraints**: On extreme edge nodes (e.g. Raspberry Pi 4 without GPU acceleration), inference at full 30 FPS requires downsampling frame ingestion rate to 2–5 FPS.
2. **Single-Operator Prototype**: The current architecture is designed for academic evaluation and single-operator monitoring stations. Enterprise multi-tenant deployments require OAuth2/OIDC integration and role-based access control (RBAC).

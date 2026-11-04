# Problem Statement & Research Objectives

## 1. Problem Statement
Wildfires and forest fires cause catastrophic ecological destruction, endanger biodiversity, release vast carbon emissions, and threaten human settlements and infrastructure. Key operational challenges in current surveillance systems include:

1. **High Latency of Satellite Systems**: Low-Earth orbit and geostationary environmental satellites (e.g., MODIS, VIIRS) offer revisit times varying from hours to days, which is inadequate for early flame and smoke suppression within the first critical 15 minutes of ignition.
2. **Cloud Dependency in Remote Regions**: Wilderness regions often suffer from intermittent or non-existent cellular and satellite uplink bandwidth, rendering heavy cloud-dependent deep neural networks impractical.
3. **Severe False Alarm Rates**: Conventional vision systems frequently trigger false alerts due to optical distractors such as sun glare, moving dust clouds, atmospheric haze, industrial steam, yellow/orange autumn foliage, and camera sensor noise.
4. **Black-Box Decision Making**: Deep learning classifiers output a scalar probability without interpretable visual evidence, making emergency responders hesitant to deploy expensive aerial or ground firefighting teams without visual verification.
5. **Single-Frame Instability**: Isolated transient predictions on individual video frames lead to flickering false alarms unless verified coherently across temporal observation windows.

---

## 2. Research Objectives
To overcome these limitations, this project develops and benchmarks **"Real-Time Detection of Forest Fires Using FireNet-CNN and Explainable AI Techniques"**:

1. **Develop a Compact 3-Class Deep Neural Network (`FireNetCNN`)**:
   - Classify input frames into `fire`, `smoke`, and `normal` scenes.
   - Maintain a compact parameter footprint (< 3 million parameters) capable of achieving > 30 FPS on standard edge hardware.

2. **Implement Grounded Explainable AI (Grad-CAM)**:
   - Provide real-time class activation maps overlaid on original frames to pinpoint the exact visual features (flame contours, smoke plumes) driving the model's decision.
   - Provide transparency for monitoring operators to distinguish genuine ignitions from misleading artifacts.

3. **Incorporate Multi-Frame Temporal Verification**:
   - Formulate a configurable sliding window verifier (e.g., 3 positive frames within a 5-frame window) with camera-specific cooldown mechanisms to eliminate transient false positives.

4. **Deliver a Full-Stack Surveillance Platform**:
   - Real-time video ingestion, background video analysis worker, persistent incident storage, alert acknowledgement workflows, and a responsive web monitoring dashboard.

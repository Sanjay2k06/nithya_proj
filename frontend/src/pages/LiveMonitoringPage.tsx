import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Clock3,
  Flame,
  LoaderCircle,
  Play,
  Radio,
  ShieldAlert,
  Square,
  Wind,
  XCircle
} from 'lucide-react';
import { api, resolveMediaUrl } from '../services/api';
import { DemoCctvSource, DemoMonitoringStatus, PredictionResponse } from '../types';

type MonitorState = DemoMonitoringStatus['status'];

function formatTime(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || !Number.isFinite(seconds)) return 'NOT PROCESSED YET';
  const minutes = Math.floor(seconds / 60).toString().padStart(2, '0');
  const remainder = Math.floor(seconds % 60).toString().padStart(2, '0');
  return `${minutes}:${remainder}`;
}

export const LiveMonitoringPage: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const pollingRef = useRef(false);
  const mountedRef = useRef(true);
  const [sources, setSources] = useState<DemoCctvSource[]>([]);
  const [selectedSource, setSelectedSource] = useState<DemoCctvSource | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [monitorState, setMonitorState] = useState<MonitorState>('IDLE');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isVideoPlaying, setIsVideoPlaying] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const [modelError, setModelError] = useState<string | null>(null);
  const [geminiConfigured, setGeminiConfigured] = useState(false);
  const [loading, setLoading] = useState(true);
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastVideoTimestamp, setLastVideoTimestamp] = useState<number | null>(null);
  const [processingDelay, setProcessingDelay] = useState<number | null>(null);
  const [processedFrames, setProcessedFrames] = useState(0);

  const applyStatus = useCallback((status: DemoMonitoringStatus) => {
    if (!mountedRef.current) return;
    setMonitorState(status.status);
    setIsProcessing(status.is_processing);
    setPrediction(status.latest_detection);
    setLastVideoTimestamp(status.last_processed_video_seconds);
    setProcessingDelay(status.processing_delay_ms);
    setProcessedFrames(status.processed_frames);
    if (status.selected_source) {
      setSelectedSource(status.selected_source);
    } else {
      setSelectedSource(null);
    }
    if (status.status === 'ERROR') {
      setError(status.error || 'The backend video-processing task failed.');
      setPrediction(null);
      videoRef.current?.pause();
    } else {
      setError(status.error || null);
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    let active = true;
    const initialize = async () => {
      try {
        const [availableSources, modelStatus] = await Promise.all([
          api.getDemoSources(),
          api.getModelStatus()
        ]);
        if (!active) return;
        setSources(availableSources);
        setDemoMode(modelStatus.demo_mode);
        setGeminiConfigured(modelStatus.gemini_configured);
        if (!modelStatus.loaded || modelStatus.demo_mode) {
          setModelError(
            modelStatus.error ||
            `Trained FireNet-CNN checkpoint is unavailable or unverified: ${modelStatus.checkpoint_path}`
          );
        }

        const firstAvailable = availableSources.find(
          (source) => source.source_id === 'cam01-normal' && source.available
        ) ?? availableSources.find((source) => source.available);
        if (!firstAvailable) {
          throw new Error('No simulated CCTV video files are available in image_fire.');
        }
        await api.selectDemoSource(firstAvailable.source_id);
        if (!active) return;
        setSelectedSource(firstAvailable);
        applyStatus(await api.getDemoMonitoringStatus());
      } catch (reason) {
        if (active) {
          setError(reason instanceof Error ? reason.message : 'Could not load CCTV monitoring.');
          setMonitorState('ERROR');
        }
      } finally {
        if (active) setLoading(false);
      }
    };
    void initialize();
    return () => {
      active = false;
      mountedRef.current = false;
      void api.stopDemoMonitoring().catch(() => undefined);
    };
  }, [applyStatus]);

  useEffect(() => {
    if (loading) return undefined;
    const poll = async () => {
      if (pollingRef.current) return;
      pollingRef.current = true;
      try {
        applyStatus(await api.getDemoMonitoringStatus());
      } catch (reason) {
        setMonitorState('ERROR');
        setIsProcessing(false);
        setError(reason instanceof Error ? reason.message : 'Monitoring status is unavailable.');
      } finally {
        pollingRef.current = false;
      }
    };
    const intervalId = window.setInterval(() => void poll(), 900);
    return () => window.clearInterval(intervalId);
  }, [applyStatus, loading]);

  const startMonitoring = async () => {
    if (!selectedSource || switching) return;
    setError(null);
    setPrediction(null);
    setLastVideoTimestamp(null);
    setProcessingDelay(null);
    setProcessedFrames(0);
    if (videoRef.current) videoRef.current.currentTime = 0;
    try {
      applyStatus(await api.startDemoMonitoring());
      await videoRef.current?.play();
    } catch (reason) {
      const startError = reason instanceof Error ? reason.message : 'Could not start backend monitoring.';
      setMonitorState('ERROR');
      videoRef.current?.pause();
      try {
        applyStatus(await api.stopDemoMonitoring());
        setError(startError);
      } catch (stopReason) {
        setError(
          `${startError} ` +
          `Stop request also failed: ${stopReason instanceof Error ? stopReason.message : 'backend unavailable.'}`
        );
      }
      setMonitorState('ERROR');
    }
  };

  const stopMonitoring = async () => {
    videoRef.current?.pause();
    setIsVideoPlaying(false);
    try {
      applyStatus(await api.stopDemoMonitoring());
      setPrediction(null);
      setLastVideoTimestamp(null);
      setProcessingDelay(null);
    } catch (reason) {
      setMonitorState('ERROR');
      setError(reason instanceof Error ? reason.message : 'Could not stop backend monitoring.');
    }
  };

  const switchSource = async (source: DemoCctvSource) => {
    if (source.source_id === selectedSource?.source_id || !source.available || switching) return;
    setSwitching(true);
    setError(null);
    videoRef.current?.pause();
    setIsVideoPlaying(false);
    try {
      applyStatus(await api.stopDemoMonitoring());
      await api.selectDemoSource(source.source_id);
      setSelectedSource(source);
      setPrediction(null);
      setLastVideoTimestamp(null);
      setProcessingDelay(null);
      setProcessedFrames(0);
      setMonitorState('IDLE');
      setError(null);
    } catch (reason) {
      setMonitorState('ERROR');
      setError(reason instanceof Error ? reason.message : 'Could not switch CCTV source.');
    } finally {
      setSwitching(false);
    }
  };

  const temporal = prediction?.temporal_state;
  const isGeminiResult = prediction?.analysis_provider === 'gemini';
  const isVerifiedFire = monitorState === 'VERIFIED'
    && temporal?.verified_class === 'fire'
    && temporal.is_temporally_verified;
  const isVerifiedSmoke = monitorState === 'VERIFIED'
    && temporal?.verified_class === 'smoke'
    && temporal.is_temporally_verified;
  const isCandidate = monitorState === 'VERIFYING';
  const mainResult = monitorState === 'ERROR'
    ? 'MONITORING ERROR'
    : isGeminiResult && prediction.predicted_class === 'fire'
      ? 'FIRE OBSERVED - GEMINI (UNVERIFIED)'
      : isGeminiResult && prediction.predicted_class === 'smoke'
        ? 'SMOKE OBSERVED - GEMINI (UNVERIFIED)'
        : isGeminiResult && prediction.predicted_class === 'uncertain'
          ? 'GEMINI RESULT UNCERTAIN'
          : isGeminiResult && prediction.predicted_class === 'normal'
            ? 'NO FIRE OBSERVED IN THIS FRAME'
    : isVerifiedFire
      ? 'FIRE DETECTED'
      : isVerifiedSmoke
        ? 'SMOKE DETECTED'
        : isCandidate
          ? prediction?.predicted_class === 'smoke'
            ? 'SMOKE DETECTED - VERIFICATION IN PROGRESS'
            : 'FIRE CANDIDATE - VERIFICATION IN PROGRESS'
          : prediction?.predicted_class === 'normal'
            ? 'NO FIRE DETECTED'
            : monitorState === 'STOPPED'
              ? 'MONITORING STOPPED'
              : monitorState === 'IDLE'
                ? 'MONITORING IDLE'
                : 'MONITORING ACTIVE - WAITING FOR FRAME';
  const resultTone = isVerifiedFire ? 'fire' : isVerifiedSmoke || isCandidate || (isGeminiResult && prediction.predicted_class !== 'normal') ? 'caution' : 'normal';
  const notificationStatus = isVerifiedFire
    ? prediction?.notification_status ?? 'PENDING'
    : 'NOT SENT';
  const isBackendMonitoring = ['IN_PROGRESS', 'VERIFYING', 'VERIFIED'].includes(monitorState);
  const processingIsDelayed = (processingDelay ?? 0) > 1800;

  return (
    <div className="page-container demo-monitoring-page">
      <header className="demo-page-heading reveal-up">
        <div>
          <p className="demo-eyebrow">SIMULATED CCTV DEMONSTRATION SOURCE</p>
          <h1>Live Monitoring</h1>
          <p>The backend decodes and analyzes frames from the selected local video. These are simulated videos, not physical forest cameras.</p>
        </div>
        <div className={`demo-live-pill ${monitorState === 'IN_PROGRESS' || isCandidate || isVerifiedFire || isVerifiedSmoke ? 'is-live' : ''}`}>
          <span />
          {monitorState.replace(/_/g, ' ')}
        </div>
      </header>

      <div className="demo-source-selectors reveal-up delay-1" role="group" aria-label="Select demo camera">
        {sources.map((source) => (
          <button
            key={source.source_id}
            className={`demo-source-button ${selectedSource?.source_id === source.source_id ? 'active' : ''}`}
            onClick={() => void switchSource(source)}
            disabled={loading || switching || !source.available}
            aria-pressed={selectedSource?.source_id === source.source_id}
          >
            <Radio size={18} />
            <span>{source.name}</span>
            {!source.available && <small>VIDEO UNAVAILABLE</small>}
          </button>
        ))}
      </div>

      {error && <div className="demo-error" role="alert"><XCircle size={18} />{error}</div>}
      {modelError && (
        <div className="demo-warning" role="status">
          <AlertTriangle size={18} />
          {demoMode
            ? 'FireNet demo inference is not used. Gemini monitoring is informational only and cannot create verified incidents or Telegram alerts.'
            : `Trained FireNet-CNN is unavailable (${modelError}). ${geminiConfigured ? 'Gemini can analyze sampled simulated-video frames for informational use only.' : 'Add GEMINI_API_KEY to enable informational frame analysis.'}`}
        </div>
      )}

      <div className="demo-monitoring-grid reveal-up delay-2">
        <section className="demo-video-card reveal-left">
          <div className="demo-video-header">
            <div>
              <strong>{selectedSource?.name ?? 'No source selected'}</strong>
              <span>BACKEND VIDEO DECODE + {geminiConfigured ? 'GEMINI INFORMATIONAL FRAME ANALYSIS' : 'ANALYSIS UNAVAILABLE'}</span>
            </div>
            <span className={`demo-playback-state ${isVideoPlaying ? 'active' : ''}`}>
              {isProcessing ? 'PROCESSING FRAME' : isVideoPlaying && !isBackendMonitoring ? 'PREVIEW ONLY' : isVideoPlaying ? 'PLAYING' : 'STOPPED'}
            </span>
          </div>
          <div className="demo-video-stage">
            {selectedSource ? (
              <video
                key={selectedSource.source_id}
                ref={videoRef}
                src={resolveMediaUrl(selectedSource.video_url)}
                controls={!isBackendMonitoring}
                loop
                playsInline
                preload="metadata"
                onError={() => {
                  setMonitorState('ERROR');
                  setError('The selected video could not be played. Stop monitoring and check that the source file is available.');
                  void api.stopDemoMonitoring().catch((reason) => {
                    setError(reason instanceof Error ? reason.message : 'Could not stop monitoring after video playback failed.');
                  });
                }}
                onPlay={() => setIsVideoPlaying(true)}
                onPause={() => setIsVideoPlaying(false)}
              />
            ) : (
              <div className="demo-video-empty">{loading ? 'Loading video sources...' : 'No video source is available.'}</div>
            )}
            {isProcessing && <div className="demo-processing-overlay"><LoaderCircle className="spin" size={18} /> Backend is analyzing a video frame</div>}
          </div>
          <div className="demo-video-controls">
            <button
              className="demo-action-button primary"
              onClick={() => void startMonitoring()}
              disabled={!selectedSource || !geminiConfigured || monitorState === 'IN_PROGRESS' || isCandidate || isVerifiedFire || isVerifiedSmoke || loading || switching}
            >
              <Play size={16} /> Start monitoring
            </button>
            <button
              className="demo-action-button"
              onClick={() => void stopMonitoring()}
              disabled={!['IN_PROGRESS', 'VERIFYING', 'VERIFIED'].includes(monitorState)}
            >
              <Square size={15} /> Stop monitoring
            </button>
            <span className="demo-timeline"><Clock3 size={15} /> Processed video time: {formatTime(lastVideoTimestamp)}</span>
          </div>
        </section>

        <aside className={`demo-result-card tone-${resultTone}`} aria-live="polite">
          <p className="demo-eyebrow">LATEST BACKEND MODEL RESULT</p>
          <h2>{mainResult}</h2>
          <p className="demo-result-summary">
            {isGeminiResult
              ? prediction.analysis_caveat
                ?? 'Gemini is informational only. Its classifications are not calibrated and are not temporally verified.'
              : monitorState === 'ERROR'
              ? 'The processing task failed. No stale classification is shown as current.'
              : isVerifiedFire
                ? 'A fire classification passed the configured temporal verification threshold.'
                : isVerifiedSmoke
                  ? 'Smoke was verified separately; it is not labeled as a confirmed fire.'
                  : isCandidate
                    ? `${prediction?.predicted_class.toUpperCase()} candidate is being evaluated across consecutive frames.`
                    : prediction?.predicted_class === 'normal'
                      ? 'ENVIRONMENT APPEARS NORMAL based on the latest frame; a single classification does not certify that the area is safe.'
                      : monitorState === 'STOPPED'
                        ? 'Start monitoring to analyze frames from the selected video.'
                        : monitorState === 'IN_PROGRESS'
                          ? 'Monitoring is active; waiting for the first processed frame.'
                          : 'Start monitoring to analyze frames from the selected video.'}
          </p>
          <div className="demo-result-divider" />
          <div className="demo-result-row"><span>Classification</span><strong>{prediction?.predicted_class?.toUpperCase() ?? 'NOT AVAILABLE'}</strong></div>
          <div className="demo-result-row"><span>Source</span><strong>{selectedSource?.name ?? 'NOT AVAILABLE'}</strong></div>
          <div className="demo-result-row"><span>Confidence</span><strong>{prediction?.confidence != null ? `${(prediction.confidence * 100).toFixed(1)}%` : isGeminiResult ? 'NOT CALIBRATED' : 'NOT AVAILABLE'}</strong></div>
          <div className="demo-result-row"><span>Monitoring</span><strong>{monitorState.replace(/_/g, ' ')}</strong></div>
          <div className="demo-result-row"><span>Temporal verification</span><strong>{isGeminiResult ? 'NOT APPLICABLE' : prediction ? monitorState : 'IDLE'}</strong></div>
          <div className="demo-result-row"><span>Telegram</span><strong>{isGeminiResult ? 'NOT SENT - INFORMATIONAL ONLY' : notificationStatus}</strong></div>
          {isGeminiResult && prediction.analysis_text && (
            <p className="demo-result-summary">{prediction.analysis_text}</p>
          )}
          {isGeminiResult && prediction.analysis_evidence && prediction.analysis_evidence.length > 0 && (
            <ul className="demo-empty-state">
              {prediction.analysis_evidence.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}
            </ul>
          )}
          {!prediction && (
            <p className="demo-empty-state">
              {monitorState === 'STOPPED'
                ? 'Start monitoring to analyze frames from the selected video.'
                : 'No classification is shown until the backend processes a frame.'}
            </p>
          )}
        </aside>
      </div>

      <section className="demo-detail-grid">
        <div className="demo-stat-card"><Activity size={18} /><span>Last processed video time</span><strong>{formatTime(lastVideoTimestamp)}</strong></div>
        <div className="demo-stat-card"><Clock3 size={18} /><span>Processing delay vs video timeline</span><strong>{processingDelay === null ? '—' : `${processingDelay.toFixed(0)} ms${processingIsDelayed ? ' - DELAYED' : ''}`}</strong></div>
        <div className="demo-stat-card"><Flame size={18} /><span>Positive fire frames</span><strong>{temporal?.positive_fire_count ?? '—'} / {temporal?.window_size ?? '—'}</strong></div>
        <div className="demo-stat-card"><Wind size={18} /><span>Positive smoke frames</span><strong>{temporal?.positive_smoke_count ?? '—'} / {temporal?.window_size ?? '—'}</strong></div>
      </section>

      <p className="demo-empty-state">Backend-processed frames: {processedFrames}. Start time and latest result are synchronized from the FastAPI monitoring status endpoint.</p>

      <details className="demo-technical-details">
        <summary><ShieldAlert size={17} /> Technical details and evidence</summary>
        {prediction ? (
          <div className="demo-technical-content">
            <div className="demo-technical-metrics">
              <span>Processed timestamp <strong>{formatTime(lastVideoTimestamp)}</strong></span>
              <span>Inference <strong>{prediction.inference_ms.toFixed(1)} ms</strong></span>
              <span>Temporal verification <strong>{isGeminiResult ? 'NOT APPLICABLE' : `${temporal?.positive_fire_count ?? 0} / ${temporal?.window_size ?? 5} fire-positive frames`}</strong></span>
              <span>Threshold <strong>{isGeminiResult ? 'NOT APPLICABLE' : `${temporal?.required_positives ?? 3} positive frames required`}</strong></span>
              <span>Analysis provider <strong>{isGeminiResult ? `GEMINI (${prediction.model_version}) - INFORMATIONAL` : prediction.demo_mode ? 'UNTRAINED DEMO - NOT OPERATIONAL' : 'TRAINED CHECKPOINT'}</strong></span>
            </div>
            {isGeminiResult && prediction.analysis_text && (
              <p className="demo-result-summary">{prediction.analysis_text}</p>
            )}
            <div className="demo-probability-list">
              {Object.entries(prediction.probabilities).map(([label, probability]) => (
                <div key={label} className="demo-probability-row">
                  <span>{label.toUpperCase()}</span>
                  <div><i style={{ width: `${Math.max(0, Math.min(100, probability * 100))}%` }} /></div>
                  <strong>{(probability * 100).toFixed(1)}%</strong>
                </div>
              ))}
            </div>
            {prediction.heatmap_image_url && (
              <img className="demo-evidence-image" src={resolveMediaUrl(prediction.heatmap_image_url)} alt="Grad-CAM explanation for the latest backend-processed frame" />
            )}
          </div>
        ) : (
          <p className="demo-empty-state">Frame evidence appears here after a backend analysis result is received.</p>
        )}
      </details>
    </div>
  );
};

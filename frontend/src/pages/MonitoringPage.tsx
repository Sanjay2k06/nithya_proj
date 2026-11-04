import React, { useState, useEffect, useRef } from 'react';
import {
  Radio,
  Play,
  Square,
  Upload,
  Eye,
  Camera as CameraIcon,
  Video,
  Flame,
  AlertTriangle,
  CheckCircle,
  Clock,
  Layers,
  Sparkles,
  RefreshCw
} from 'lucide-react';
import { api } from '../services/api';
import { Camera, PredictionResponse, ClassLabel } from '../types';
import { Badge } from '../components/common/Badge';

export const MonitoringPage: React.FC = () => {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [selectedCameraId, setSelectedCameraId] = useState<string>('');
  const [isMonitoring, setIsMonitoring] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'upload' | 'stream' | 'video'>('upload');

  // Single Image State
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [viewMode, setViewMode] = useState<'blended' | 'split'>('split');

  // Video Upload State
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoTaskId, setVideoTaskId] = useState<string | null>(null);
  const [videoTaskStatus, setVideoTaskStatus] = useState<any>(null);
  const [isUploadingVideo, setIsUploadingVideo] = useState<boolean>(false);

  // Webcam live stream simulation/capture
  const videoRef = useRef<HTMLVideoElement>(null);
  const [webcamActive, setWebcamActive] = useState<boolean>(false);
  const streamIntervalRef = useRef<any>(null);

  useEffect(() => {
    loadCameras();
    return () => {
      stopWebcam();
    };
  }, []);

  const loadCameras = async () => {
    try {
      const cams = await api.getCameras();
      setCameras(cams);
      if (cams.length > 0 && !selectedCameraId) {
        setSelectedCameraId(cams[0].id);
      }
    } catch (err) {
      console.error('Failed to load cameras:', err);
    }
  };

  const handleStartStream = async () => {
    if (!selectedCameraId) return;
    try {
      await api.startMonitoring(selectedCameraId);
      setIsMonitoring(true);
      loadCameras();
    } catch (err) {
      console.error('Failed to start stream:', err);
    }
  };

  const handleStopStream = async () => {
    if (!selectedCameraId) return;
    try {
      await api.stopMonitoring(selectedCameraId);
      setIsMonitoring(false);
      loadCameras();
    } catch (err) {
      console.error('Failed to stop stream:', err);
    }
  };

  // Image analysis
  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedImage(file);
      setImagePreview(URL.createObjectURL(file));
      setPrediction(null);
    }
  };

  const handleRunInference = async () => {
    if (!selectedImage) return;
    try {
      setIsAnalyzing(true);
      const res = await api.predictImage(selectedImage, selectedCameraId || undefined);
      setPrediction(res);
    } catch (err: any) {
      alert(`Inference failed: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Video Upload
  const handleVideoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setVideoFile(e.target.files[0]);
      setVideoTaskId(null);
      setVideoTaskStatus(null);
    }
  };

  const handleUploadVideo = async () => {
    if (!videoFile) return;
    try {
      setIsUploadingVideo(true);
      const res = await api.uploadVideo(videoFile);
      setVideoTaskId(res.task_id);
      pollVideoTask(res.task_id);
    } catch (err: any) {
      alert(`Video upload failed: ${err.message}`);
      setIsUploadingVideo(false);
    }
  };

  const pollVideoTask = (taskId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const status = await api.getVideoTaskStatus(taskId);
        setVideoTaskStatus(status);
        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(pollInterval);
          setIsUploadingVideo(false);
        }
      } catch {
        clearInterval(pollInterval);
        setIsUploadingVideo(false);
      }
    }, 1500);
  };

  // Local Webcam Toggle
  const startWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        setWebcamActive(true);

        // Capture frame every 1.5 seconds for analysis
        streamIntervalRef.current = setInterval(() => {
          captureWebcamFrame();
        }, 1500);
      }
    } catch (err) {
      alert(`Cannot access webcam: ${err}`);
    }
  };

  const stopWebcam = () => {
    if (streamIntervalRef.current) {
      clearInterval(streamIntervalRef.current);
    }
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }
    setWebcamActive(false);
  };

  const captureWebcamFrame = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = 640;
    canvas.height = 480;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(async (blob) => {
      if (!blob) return;
      const file = new File([blob], 'webcam_frame.jpg', { type: 'image/jpeg' });
      try {
        const res = await api.predictImage(file, selectedCameraId || undefined);
        setPrediction(res);
      } catch (err) {
        console.error('Frame inference error:', err);
      }
    }, 'image/jpeg', 0.85);
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.85rem', color: '#fff', marginBottom: '6px' }}>Live Video & XAI Inspection</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem' }}>
            Real-time multi-camera monitoring, interactive frame upload, and Grad-CAM visual heatmaps.
          </p>
        </div>

        {/* Tab Controls */}
        <div style={{ display: 'flex', gap: '8px', background: 'rgba(255,255,255,0.04)', padding: '4px', borderRadius: 'var(--radius-sm)' }}>
          <button
            onClick={() => setActiveTab('upload')}
            className={`btn ${activeTab === 'upload' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '8px 14px', fontSize: '0.85rem' }}
          >
            <Upload size={15} />
            <span>Image Analysis</span>
          </button>
          <button
            onClick={() => setActiveTab('video')}
            className={`btn ${activeTab === 'video' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '8px 14px', fontSize: '0.85rem' }}
          >
            <Video size={15} />
            <span>Video Upload</span>
          </button>
          <button
            onClick={() => setActiveTab('stream')}
            className={`btn ${activeTab === 'stream' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '8px 14px', fontSize: '0.85rem' }}
          >
            <CameraIcon size={15} />
            <span>Live Stream</span>
          </button>
        </div>
      </div>

      {/* Camera Selection Bar */}
      <div className="glass-card" style={{ padding: '16px 22px', marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Radio size={18} color="var(--color-flame)" />
          <span style={{ fontWeight: 600, fontSize: '0.92rem', color: '#fff' }}>Surveillance Station:</span>
          <select
            value={selectedCameraId}
            onChange={(e) => setSelectedCameraId(e.target.value)}
            style={{
              background: 'var(--bg-secondary)',
              color: '#fff',
              border: '1px solid var(--border-subtle)',
              padding: '8px 14px',
              borderRadius: '6px',
              fontSize: '0.88rem',
              outline: 'none',
              cursor: 'pointer'
            }}
          >
            {cameras.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.location_label || c.source_type})
              </option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)' }}>
            Status: <strong style={{ color: isMonitoring ? 'var(--color-normal)' : 'var(--text-muted)' }}>{isMonitoring ? 'STREAMING' : 'IDLE'}</strong>
          </span>
          {isMonitoring ? (
            <button onClick={handleStopStream} className="btn btn-danger" style={{ padding: '7px 14px', fontSize: '0.82rem' }}>
              <Square size={14} />
              <span>Stop Stream</span>
            </button>
          ) : (
            <button onClick={handleStartStream} className="btn btn-secondary" style={{ padding: '7px 14px', fontSize: '0.82rem' }}>
              <Play size={14} />
              <span>Start Stream</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Workspace Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '24px' }}>
        {/* Left Column: Visual Media Display */}
        <div className="glass-card" style={{ padding: '24px' }}>
          {activeTab === 'upload' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '1.1rem', color: '#fff' }}>Optical Frame & XAI Heatmap</h3>
                {prediction && (
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button
                      onClick={() => setViewMode('split')}
                      className={`btn ${viewMode === 'split' ? 'btn-primary' : 'btn-secondary'}`}
                      style={{ padding: '6px 10px', fontSize: '0.78rem' }}
                    >
                      Side-by-Side
                    </button>
                    <button
                      onClick={() => setViewMode('blended')}
                      className={`btn ${viewMode === 'blended' ? 'btn-primary' : 'btn-secondary'}`}
                      style={{ padding: '6px 10px', fontSize: '0.78rem' }}
                    >
                      Grad-CAM Overlay
                    </button>
                  </div>
                )}
              </div>

              {/* Image Preview Box */}
              <div style={{
                width: '100%',
                minHeight: '360px',
                background: 'rgba(0,0,0,0.3)',
                borderRadius: 'var(--radius-sm)',
                border: '1px dashed var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                overflow: 'hidden',
                position: 'relative'
              }}>
                {imagePreview ? (
                  viewMode === 'split' && prediction?.heatmap_image_url ? (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', width: '100%', padding: '8px' }}>
                      <div style={{ position: 'relative' }}>
                        <img src={imagePreview} alt="Original" style={{ width: '100%', height: '320px', objectFit: 'contain', borderRadius: '6px' }} />
                        <span style={{ position: 'absolute', bottom: '8px', left: '8px', background: 'rgba(0,0,0,0.7)', color: '#fff', fontSize: '0.72rem', padding: '3px 8px', borderRadius: '4px' }}>
                          Original RGB
                        </span>
                      </div>
                      <div style={{ position: 'relative' }}>
                        <img src={prediction.heatmap_image_url} alt="Grad-CAM" style={{ width: '100%', height: '320px', objectFit: 'contain', borderRadius: '6px' }} />
                        <span style={{ position: 'absolute', bottom: '8px', left: '8px', background: 'rgba(0,0,0,0.7)', color: '#ff8a65', fontSize: '0.72rem', padding: '3px 8px', borderRadius: '4px' }}>
                          Grad-CAM Heatmap
                        </span>
                      </div>
                    </div>
                  ) : (
                    <img
                      src={prediction?.heatmap_image_url || imagePreview}
                      alt="Surveillance Feed"
                      style={{ width: '100%', maxHeight: '420px', objectFit: 'contain' }}
                    />
                  )
                ) : (
                  <div style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '40px' }}>
                    <Upload size={40} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
                    <p style={{ fontWeight: 600, color: 'var(--text-muted)' }}>Choose an image or drop surveillance frame</p>
                    <p style={{ fontSize: '0.8rem', marginTop: '4px' }}>JPG, PNG, WEBP (Max {25} MB)</p>
                  </div>
                )}
              </div>

              {/* Upload Controls */}
              <div style={{ display: 'flex', gap: '14px', marginTop: '20px' }}>
                <input
                  type="file"
                  id="imageUploadInput"
                  accept="image/*"
                  onChange={handleImageSelect}
                  style={{ display: 'none' }}
                />
                <label htmlFor="imageUploadInput" className="btn btn-secondary" style={{ cursor: 'pointer' }}>
                  <Upload size={16} />
                  <span>Choose Image File</span>
                </label>
                {selectedImage && (
                  <button
                    onClick={handleRunInference}
                    disabled={isAnalyzing}
                    className="btn btn-primary"
                  >
                    <Sparkles size={16} />
                    <span>{isAnalyzing ? 'Evaluating FireNet...' : 'Run Explainable Inference'}</span>
                  </button>
                )}
              </div>
            </div>
          )}

          {activeTab === 'video' && (
            <div>
              <h3 style={{ fontSize: '1.1rem', color: '#fff', marginBottom: '16px' }}>Offline Video File Surveillance</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginBottom: '20px' }}>
                Upload drone footage or CCTV archive. The background worker analyzes frames at 2 FPS and triggers verified alerts.
              </p>

              <div style={{
                padding: '36px',
                border: '2px dashed var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                textAlign: 'center',
                background: 'rgba(0,0,0,0.2)'
              }}>
                <Video size={42} style={{ margin: '0 auto 12px', color: 'var(--color-accent)' }} />
                <div style={{ fontWeight: 600, color: '#fff', marginBottom: '6px' }}>
                  {videoFile ? videoFile.name : 'Select Wildfire Surveillance Video'}
                </div>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-dim)', marginBottom: '18px' }}>
                  MP4, AVI, MOV (Max 120 seconds sampled duration)
                </div>

                <input
                  type="file"
                  id="videoUploadInput"
                  accept="video/*"
                  onChange={handleVideoSelect}
                  style={{ display: 'none' }}
                />
                <label htmlFor="videoUploadInput" className="btn btn-secondary" style={{ cursor: 'pointer', marginRight: '10px' }}>
                  Choose Video File
                </label>
                {videoFile && (
                  <button
                    onClick={handleUploadVideo}
                    disabled={isUploadingVideo}
                    className="btn btn-primary"
                  >
                    {isUploadingVideo ? 'Analyzing Frames...' : 'Process Video Stream'}
                  </button>
                )}
              </div>

              {/* Video Progress Card */}
              {videoTaskStatus && (
                <div style={{ marginTop: '24px', padding: '18px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Analysis Task Status</span>
                    <span className={`badge ${videoTaskStatus.status === 'completed' ? 'badge-normal' : 'badge-active'}`}>
                      {videoTaskStatus.status.toUpperCase()}
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginTop: '12px' }}>
                    <div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Frames Processed</span>
                      <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#fff' }}>{videoTaskStatus.processed_frames ?? 0}</div>
                    </div>
                    <div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Detections Found</span>
                      <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-flame)' }}>{videoTaskStatus.detections_count ?? 0}</div>
                    </div>
                    <div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Verified Alerts</span>
                      <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-accent)' }}>{videoTaskStatus.alerts_count ?? 0}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'stream' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '1.1rem', color: '#fff' }}>Local Hardware Camera Feed</h3>
                <button
                  onClick={webcamActive ? stopWebcam : startWebcam}
                  className={`btn ${webcamActive ? 'btn-danger' : 'btn-primary'}`}
                  style={{ padding: '7px 14px', fontSize: '0.82rem' }}
                >
                  <CameraIcon size={14} />
                  <span>{webcamActive ? 'Stop Camera' : 'Connect Local Webcam'}</span>
                </button>
              </div>

              <div style={{
                width: '100%',
                height: '380px',
                background: '#000',
                borderRadius: 'var(--radius-sm)',
                overflow: 'hidden',
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <video
                  ref={videoRef}
                  style={{ width: '100%', height: '100%', objectFit: 'cover', display: webcamActive ? 'block' : 'none' }}
                  muted
                  playsInline
                />
                {!webcamActive && (
                  <div style={{ textAlign: 'center', color: 'var(--text-dim)' }}>
                    <CameraIcon size={44} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
                    <p>Webcam inactive. Click "Connect Local Webcam" to begin live frame sampling.</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Telemetry & Temporal Verification Dashboard */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Classification & Confidence Card */}
          <div className="glass-card" style={{ padding: '22px' }}>
            <h3 style={{ fontSize: '1.05rem', color: '#fff', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={18} color="var(--color-flame)" />
              <span>Inference Telemetry</span>
            </h3>

            {prediction ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>Classified As</span>
                  <Badge type={prediction.predicted_class} />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Top Confidence</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#fff' }}>
                      {(prediction.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div style={{ height: '8px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{
                      width: `${prediction.confidence * 100}%`,
                      height: '100%',
                      background: prediction.predicted_class === 'fire' ? 'var(--color-flame)' : prediction.predicted_class === 'smoke' ? 'var(--color-smoke)' : 'var(--color-normal)'
                    }} />
                  </div>
                </div>

                {/* Probabilities Breakdown */}
                <div style={{ background: 'rgba(255,255,255,0.02)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: '10px' }}>
                    Calibrated Softmax Probabilities
                  </div>
                  {(['fire', 'smoke', 'normal'] as ClassLabel[]).map((c) => (
                    <div key={c} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px', fontSize: '0.85rem' }}>
                      <span style={{ textTransform: 'capitalize', color: 'var(--text-muted)' }}>{c}:</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#fff' }}>
                        {((prediction.probabilities?.[c] ?? 0) * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', color: 'var(--text-dim)', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
                  <span>Compute Latency:</span>
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-accent)' }}>{prediction.inference_ms} ms</span>
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-dim)' }}>
                <Clock size={32} style={{ margin: '0 auto 10px', opacity: 0.4 }} />
                <p style={{ fontSize: '0.88rem' }}>Awaiting frame evaluation...</p>
              </div>
            )}
          </div>

          {/* Temporal Verification State Card */}
          <div className="glass-card" style={{ padding: '22px' }}>
            <h3 style={{ fontSize: '1.05rem', color: '#fff', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Clock size={18} color="var(--color-accent)" />
              <span>Multi-Frame Temporal Verifier</span>
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Verification State:</span>
                <span style={{
                  fontSize: '0.82rem',
                  fontWeight: 700,
                  color: prediction?.temporally_verified ? 'var(--color-normal)' : 'var(--text-dim)'
                }}>
                  {prediction?.temporally_verified ? 'VERIFIED INCIDENT' : 'PENDING FILTER'}
                </span>
              </div>

              {/* Sliding Window Visualization */}
              <div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginBottom: '8px' }}>
                  Sliding Buffer (3 of 5 Positives Threshold)
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  {[1, 2, 3, 4, 5].map((idx) => {
                    const isPositive = idx <= 3 && prediction?.temporally_verified;
                    return (
                      <div
                        key={idx}
                        style={{
                          flex: 1,
                          height: '28px',
                          borderRadius: '4px',
                          background: isPositive ? 'rgba(255, 87, 34, 0.4)' : 'rgba(255, 255, 255, 0.05)',
                          border: isPositive ? '1px solid var(--color-flame)' : '1px solid var(--border-subtle)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '0.75rem',
                          fontFamily: 'var(--font-mono)',
                          color: isPositive ? '#ff8a65' : 'var(--text-dim)'
                        }}
                      >
                        F{idx}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div style={{ padding: '12px', background: 'rgba(255,255,255,0.02)', borderRadius: '6px', fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                A candidate detection triggers dispatch alerts only when at least 3 positive frames occur within a 5-frame window.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

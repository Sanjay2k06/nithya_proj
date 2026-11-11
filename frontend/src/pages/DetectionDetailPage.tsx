import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  Flame,
  Info,
  Clock,
  Layers,
  Camera,
  CheckCircle,
  AlertTriangle,
  RefreshCw
} from 'lucide-react';
import { api, resolveMediaUrl } from '../services/api';
import { Detection, ClassLabel } from '../types';
import { Badge } from '../components/common/Badge';

interface DetectionDetailPageProps {
  detectionId: string;
  onNavigate: (path: string) => void;
}

export const DetectionDetailPage: React.FC<DetectionDetailPageProps> = ({
  detectionId,
  onNavigate
}) => {
  const [detection, setDetection] = useState<Detection | null>(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'heatmap' | 'original' | 'split'>('split');

  useEffect(() => {
    setLoading(true);
    api.getDetection(detectionId)
      .then(setDetection)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [detectionId]);

  if (loading) {
    return (
      <div className="page-container" style={{ textAlign: 'center', padding: '80px 0' }}>
        <RefreshCw size={36} className="animate-spin" style={{ margin: '0 auto 16px', color: 'var(--color-flame)' }} />
        <h2 style={{ color: '#fff' }}>Loading Explainable AI Evidence...</h2>
      </div>
    );
  }

  if (!detection) {
    return (
      <div className="page-container" style={{ textAlign: 'center', padding: '80px 0' }}>
        <AlertTriangle size={42} style={{ margin: '0 auto 16px', color: '#ef4444' }} />
        <h2 style={{ color: '#fff', marginBottom: '8px' }}>Detection Record Not Found</h2>
        <button onClick={() => onNavigate('/detections')} className="btn btn-secondary">
          <ArrowLeft size={16} />
          <span>Return to Detection History</span>
        </button>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Top Navigation Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <button onClick={() => onNavigate('/detections')} className="btn btn-secondary" style={{ fontSize: '0.85rem' }}>
          <ArrowLeft size={16} />
          <span>Back to Detection History</span>
        </button>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setViewMode('split')}
            className={`btn ${viewMode === 'split' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            Side-by-Side
          </button>
          <button
            onClick={() => setViewMode('heatmap')}
            className={`btn ${viewMode === 'heatmap' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            Grad-CAM Heatmap
          </button>
          <button
            onClick={() => setViewMode('original')}
            className={`btn ${viewMode === 'original' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            Original RGB
          </button>
        </div>
      </div>

      {/* XAI Disclaimer Alert */}
      <div className="glass-card" style={{
        padding: '16px 20px',
        marginBottom: '24px',
        display: 'flex',
        alignItems: 'center',
        gap: '14px',
        background: 'rgba(56, 189, 248, 0.08)',
        borderColor: 'rgba(56, 189, 248, 0.3)'
      }}>
        <Info size={22} color="var(--color-accent)" style={{ flexShrink: 0 }} />
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
          <strong style={{ color: '#fff' }}>Post-Hoc Explainability Note:</strong> Grad-CAM highlights image regions whose convolutional activations positively influenced the classifier. It represents feature attribution rather than a definitive physical guarantee of fire.
        </p>
      </div>

      {/* Main Content Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 0.7fr', gap: '24px' }}>
        {/* Visual Inspection Card */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <h2 style={{ fontSize: '1.2rem', color: '#fff', marginBottom: '18px' }}>Visual Evidence & Feature Attribution</h2>

          <div style={{
            width: '100%',
            minHeight: '400px',
            background: '#070a10',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-subtle)',
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '12px'
          }}>
            {viewMode === 'split' ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', width: '100%' }}>
                <div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginBottom: '8px', textTransform: 'uppercase' }}>Original Frame</div>
                  <img
                    src={resolveMediaUrl(detection.image_path)}
                    alt="Original Frame"
                    style={{ width: '100%', height: '360px', objectFit: 'contain', borderRadius: '6px', background: '#000' }}
                  />
                </div>
                <div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--color-flame)', marginBottom: '8px', textTransform: 'uppercase' }}>Grad-CAM Activation Map</div>
                  <img
                    src={resolveMediaUrl(detection.heatmap_path || detection.image_path)}
                    alt="Grad-CAM Explanation"
                    style={{ width: '100%', height: '360px', objectFit: 'contain', borderRadius: '6px', background: '#000' }}
                  />
                </div>
              </div>
            ) : viewMode === 'heatmap' ? (
              <img
                src={resolveMediaUrl(detection.heatmap_path || detection.image_path)}
                alt="Grad-CAM Explanation"
                style={{ width: '100%', maxHeight: '480px', objectFit: 'contain' }}
              />
            ) : (
              <img
                src={resolveMediaUrl(detection.image_path)}
                alt="Original Frame"
                style={{ width: '100%', maxHeight: '480px', objectFit: 'contain' }}
              />
            )}
          </div>
        </div>

        {/* Inference Telemetry & Metadata Card */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="glass-card" style={{ padding: '22px' }}>
            <h3 style={{ fontSize: '1.1rem', color: '#fff', marginBottom: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={18} color="var(--color-flame)" />
              <span>Prediction Breakdown</span>
            </h3>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>Class Label</span>
              <Badge type={detection.predicted_class} />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Top Confidence</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#fff' }}>
                  {(detection.confidence * 100).toFixed(2)}%
                </span>
              </div>
              <div style={{ height: '8px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{
                  width: `${detection.confidence * 100}%`,
                  height: '100%',
                  background: detection.predicted_class === 'fire' ? 'var(--color-flame)' : detection.predicted_class === 'smoke' ? 'var(--color-smoke)' : 'var(--color-normal)'
                }} />
              </div>
            </div>

            {/* Class distribution */}
            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginBottom: '10px', textTransform: 'uppercase' }}>
                Softmax Logit Calibration
              </div>
              {Object.entries(detection.probabilities_json || {}).map(([c, prob]) => (
                <div key={c} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '0.85rem' }}>
                  <span style={{ textTransform: 'capitalize', color: 'var(--text-muted)' }}>{c}:</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#fff' }}>
                    {((prob as number) * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Metadata Card */}
          <div className="glass-card" style={{ padding: '22px' }}>
            <h3 style={{ fontSize: '1.05rem', color: '#fff', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Camera size={18} color="var(--color-accent)" />
              <span>Surveillance Metadata</span>
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.86rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
                <span style={{ color: 'var(--text-dim)' }}>Record ID:</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{detection.id.substring(0, 13)}...</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
                <span style={{ color: 'var(--text-dim)' }}>Surveillance Feed:</span>
                <span style={{ color: '#fff', fontWeight: 600 }}>{detection.camera_name || 'Upload Stream'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
                <span style={{ color: 'var(--text-dim)' }}>Inference Latency:</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-normal)' }}>{detection.inference_ms} ms</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
                <span style={{ color: 'var(--text-dim)' }}>Model Architecture:</span>
                <span style={{ color: '#fff' }}>FireNet-CNN ({detection.model_version})</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-dim)' }}>Captured At:</span>
                <span style={{ color: 'var(--text-muted)' }}>{new Date(detection.created_at).toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import {
  Eye,
  Filter,
  Download,
  Search,
  ChevronLeft,
  ChevronRight,
  Flame,
  Cloud,
  CheckCircle,
  RefreshCw
} from 'lucide-react';
import { api } from '../services/api';
import { Detection, Camera } from '../types';
import { Badge } from '../components/common/Badge';

interface DetectionsPageProps {
  onNavigate: (path: string) => void;
}

export const DetectionsPage: React.FC<DetectionsPageProps> = ({ onNavigate }) => {
  const [detections, setDetections] = useState<Detection[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);

  // Filters
  const [selectedClass, setSelectedClass] = useState<string>('');
  const [selectedCamera, setSelectedCamera] = useState<string>('');
  const [minConfidence, setMinConfidence] = useState<number>(0.0);

  const fetchDetections = async () => {
    setLoading(true);
    try {
      const data = await api.getDetections(
        page,
        pageSize,
        selectedCamera || undefined,
        selectedClass || undefined,
        minConfidence > 0 ? minConfidence : undefined
      );
      setDetections(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error('Failed to load detections:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    api.getCameras().then(setCameras).catch(console.error);
  }, []);

  useEffect(() => {
    fetchDetections();
  }, [page, selectedClass, selectedCamera, minConfidence]);

  const exportCSV = () => {
    if (detections.length === 0) return;
    const headers = ['ID', 'Class', 'Confidence', 'Camera', 'Source', 'Latency_ms', 'Timestamp'];
    const rows = detections.map((d) => [
      d.id,
      d.predicted_class,
      (d.confidence * 100).toFixed(2),
      d.camera_name || 'Upload',
      d.source_type,
      d.inference_ms,
      d.created_at
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `detections_export_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.85rem', color: '#fff', marginBottom: '6px' }}>Detection Log & Audit Registry</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem' }}>
            Historical record of model predictions, confidence scores, and XAI feature attributions.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={exportCSV} className="btn btn-secondary" style={{ fontSize: '0.85rem' }}>
            <Download size={15} />
            <span>Export CSV</span>
          </button>
          <button onClick={fetchDetections} className="btn btn-secondary" style={{ fontSize: '0.85rem' }}>
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="glass-card" style={{ padding: '16px 20px', marginBottom: '24px', display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={16} color="var(--text-dim)" />
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Class:</span>
          <select
            value={selectedClass}
            onChange={(e) => { setSelectedClass(e.target.value); setPage(1); }}
            style={{ background: 'var(--bg-secondary)', color: '#fff', border: '1px solid var(--border-subtle)', padding: '6px 12px', borderRadius: '6px', fontSize: '0.85rem' }}
          >
            <option value="">All Classes</option>
            <option value="fire">Fire</option>
            <option value="smoke">Smoke</option>
            <option value="normal">Normal</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Camera:</span>
          <select
            value={selectedCamera}
            onChange={(e) => { setSelectedCamera(e.target.value); setPage(1); }}
            style={{ background: 'var(--bg-secondary)', color: '#fff', border: '1px solid var(--border-subtle)', padding: '6px 12px', borderRadius: '6px', fontSize: '0.85rem' }}
          >
            <option value="">All Feeds</option>
            {cameras.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Min Confidence:</span>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={minConfidence}
            onChange={(e) => { setMinConfidence(parseFloat(e.target.value)); setPage(1); }}
            style={{ width: '100px' }}
          />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', color: 'var(--color-accent)' }}>
            {(minConfidence * 100).toFixed(0)}%
          </span>
        </div>

        <div style={{ marginLeft: 'auto', fontSize: '0.82rem', color: 'var(--text-dim)' }}>
          Showing {detections.length} of {total} records
        </div>
      </div>

      {/* Detections Table */}
      <div className="glass-card" style={{ padding: '0px', overflow: 'hidden' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-dim)' }}>
            <RefreshCw size={28} className="animate-spin" style={{ margin: '0 auto 12px' }} />
            <p>Loading detections...</p>
          </div>
        ) : detections.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-dim)' }}>
            <Search size={32} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
            <p>No detection records match your current filter parameters.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Class</th>
                  <th>Confidence</th>
                  <th>Source</th>
                  <th>Inference Latency</th>
                  <th>Temporal Verification</th>
                  <th>Recorded At</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {detections.map((det) => (
                  <tr key={det.id}>
                    <td>
                      <Badge type={det.predicted_class} />
                    </td>
                    <td>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: det.confidence > 0.75 ? '#ff8a65' : '#fff' }}>
                        {(det.confidence * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td>{det.camera_name || 'Upload Stream'}</td>
                    <td>
                      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
                        {det.inference_ms} ms
                      </span>
                    </td>
                    <td>
                      {det.temporal_state?.is_temporally_verified ? (
                        <span style={{ color: 'var(--color-normal)', fontSize: '0.82rem', fontWeight: 600 }}>
                          Verified
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-dim)', fontSize: '0.82rem' }}>
                          Standard
                        </span>
                      )}
                    </td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                      {new Date(det.created_at).toLocaleString()}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button
                        onClick={() => onNavigate(`/detections/${det.id}`)}
                        className="btn btn-secondary"
                        style={{ padding: '6px 12px', fontSize: '0.8rem' }}
                      >
                        <Eye size={13} />
                        <span>Inspect XAI</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)' }}>
              Page {page} of {totalPages}
            </span>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="btn btn-secondary"
                style={{ padding: '6px 10px', fontSize: '0.8rem' }}
              >
                <ChevronLeft size={16} />
                <span>Previous</span>
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
                className="btn btn-secondary"
                style={{ padding: '6px 10px', fontSize: '0.8rem' }}
              >
                <span>Next</span>
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

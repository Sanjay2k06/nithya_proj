import React, { useEffect, useState } from 'react';
import {
  Flame,
  AlertTriangle,
  Radio,
  Clock,
  ArrowRight,
  ShieldAlert,
  CheckCircle,
  Eye,
  RefreshCw
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import { api } from '../services/api';
import { AnalyticsSummary, Detection, Alert } from '../types';
import { StatCard } from '../components/common/StatCard';
import { Badge } from '../components/common/Badge';

interface DashboardPageProps {
  onNavigate: (path: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate }) => {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [recentDetections, setRecentDetections] = useState<Detection[]>([]);
  const [activeAlerts, setActiveAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [sumData, detData, alertData] = await Promise.all([
        api.getAnalyticsSummary(),
        api.getDetections(1, 6),
        api.getAlerts(1, 5, 'ACTIVE')
      ]);
      setSummary(sumData);
      setRecentDetections(detData.items);
      setActiveAlerts(alertData.items);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="page-container">
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '1.85rem', color: '#fff', marginBottom: '6px' }}>Surveillance Overview</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem' }}>
            Real-time optical fire monitoring, Grad-CAM feature attribution & multi-frame temporal alerts.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button onClick={() => onNavigate('/monitoring')} className="btn btn-primary">
            <Radio size={16} />
            <span>Open Live Feeds</span>
          </button>
          <button onClick={fetchData} className="btn btn-secondary">
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Active Incidents Banner */}
      {activeAlerts.length > 0 && (
        <div className="glass-card" style={{
          marginBottom: '28px',
          padding: '20px 24px',
          background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.05) 100%)',
          borderColor: 'rgba(239, 68, 68, 0.4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{
              width: '44px',
              height: '44px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ef4444'
            }}>
              <ShieldAlert size={24} />
            </div>
            <div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f87171' }}>
                {activeAlerts.length} Active Verified Incident{activeAlerts.length > 1 ? 's' : ''} Require Immediate Attention
              </div>
              <div style={{ fontSize: '0.86rem', color: 'var(--text-muted)' }}>
                Latest detection on {activeAlerts[0]?.camera_name || 'Observation Stream'} ({activeAlerts[0]?.alert_type?.toUpperCase()})
              </div>
            </div>
          </div>
          <button onClick={() => onNavigate('/alerts')} className="btn btn-danger">
            <span>Triage Alerts</span>
            <ArrowRight size={16} />
          </button>
        </div>
      )}

      {/* Stats Metric Cards */}
      <div className="grid-4" style={{ marginBottom: '28px' }}>
        <StatCard
          title="Total Detections"
          value={summary?.total_detections ?? 0}
          subtext={`Fire: ${summary?.classes.fire ?? 0} · Smoke: ${summary?.classes.smoke ?? 0} · Normal: ${summary?.classes.normal ?? 0}`}
          icon={<Flame size={20} />}
          accentColor="var(--color-flame)"
        />
        <StatCard
          title="Active Verified Incidents"
          value={summary?.active_alerts ?? 0}
          subtext={`Total incidents: ${summary?.total_alerts ?? 0}`}
          icon={<AlertTriangle size={20} />}
          accentColor={summary && summary.active_alerts > 0 ? '#ef4444' : 'var(--color-normal)'}
        />
        <StatCard
          title="Surveillance Feeds"
          value={`${summary?.active_cameras ?? 0} / ${summary?.total_cameras ?? 0}`}
          subtext="Active streaming cameras"
          icon={<Radio size={20} />}
          accentColor="var(--color-accent)"
        />
        <StatCard
          title="Inference Latency"
          value={`${summary?.avg_inference_ms ?? 12.5} ms`}
          subtext="Per-frame computation time on CPU"
          icon={<Clock size={20} />}
          accentColor="var(--color-normal)"
        />
      </div>

      {/* Charts & Recent Activity */}
      <div className="grid-2" style={{ marginBottom: '28px' }}>
        {/* Trend Area Chart */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '1.1rem', color: '#fff' }}>7-Day Surveillance Timeline</h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Detections vs Verified Alerts</span>
          </div>
          <div style={{ width: '100%', height: 260 }}>
            {summary?.daily_trend && summary.daily_trend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={summary.daily_trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorDetections" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ff5722" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#ff5722" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="colorAlerts" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                  <XAxis dataKey="date" stroke="var(--text-dim)" fontSize={12} tickLine={false} />
                  <YAxis stroke="var(--text-dim)" fontSize={12} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(15, 22, 36, 0.95)',
                      borderColor: 'var(--border-subtle)',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '0.85rem'
                    }}
                  />
                  <Area type="monotone" dataKey="detections" stroke="#ff5722" strokeWidth={2} fillOpacity={1} fill="url(#colorDetections)" name="Raw Inferences" />
                  <Area type="monotone" dataKey="alerts" stroke="#38bdf8" strokeWidth={2} fillOpacity={1} fill="url(#colorAlerts)" name="Verified Incidents" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-dim)' }}>
                No activity recorded in the past 7 days.
              </div>
            )}
          </div>
        </div>

        {/* Temporal Verification Efficacy */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '1.1rem', color: '#fff' }}>Temporal Noise Suppression</h3>
              <span className="badge badge-normal">XAI Filter Active</span>
            </div>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: '20px', lineHeight: 1.5 }}>
              The multi-frame sliding window verifier requires consecutive positive detections across 5 sampled frames before triggering dispatch, effectively suppressing transient sensor noise and sun glare.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Suppressed Transient False Alarms</span>
                  <span style={{ color: 'var(--color-normal)', fontWeight: 600 }}>
                    {summary?.suppression_efficiency.suppression_percentage ?? 0}% Suppression
                  </span>
                </div>
                <div style={{ height: '8px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{
                    width: `${Math.min(summary?.suppression_efficiency.suppression_percentage ?? 0, 100)}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #10b981 0%, #38bdf8 100%)',
                    borderRadius: '4px'
                  }} />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '8px' }}>
                <div style={{ padding: '14px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>Raw Positives</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#fff', marginTop: '4px' }}>
                    {summary?.suppression_efficiency.raw_positives ?? 0}
                  </div>
                </div>
                <div style={{ padding: '14px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>Verified Incidents</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--color-accent)', marginTop: '4px' }}>
                    {summary?.suppression_efficiency.verified_alerts ?? 0}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)' }}>Default Window: 3 of 5 frames · Cooldown: 60s</span>
            <button onClick={() => onNavigate('/settings')} className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
              Tune Rules
            </button>
          </div>
        </div>
      </div>

      {/* Recent Detections Log */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', color: '#fff' }}>Recent Inference Stream</h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Latest model decisions and Grad-CAM evidence</p>
          </div>
          <button onClick={() => onNavigate('/detections')} className="btn btn-secondary" style={{ fontSize: '0.82rem' }}>
            <span>View Full Log</span>
            <ArrowRight size={14} />
          </button>
        </div>

        {recentDetections.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)' }}>
            <Eye size={36} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
            <p>No detection records found in database.</p>
            <p style={{ fontSize: '0.82rem', marginTop: '4px' }}>Start a live camera stream or upload a video from the Monitoring page.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Class</th>
                  <th>Confidence</th>
                  <th>Source / Camera</th>
                  <th>Inference</th>
                  <th>Temporal Status</th>
                  <th>Timestamp</th>
                  <th style={{ textAlign: 'right' }}>XAI Evidence</th>
                </tr>
              </thead>
              <tbody>
                {recentDetections.map((det) => (
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
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--text-dim)' }}>
                        {det.inference_ms} ms
                      </span>
                    </td>
                    <td>
                      {det.temporal_state?.is_temporally_verified ? (
                        <span style={{ color: 'var(--color-normal)', fontSize: '0.82rem', fontWeight: 600 }}>
                          Verified ({det.temporal_state.positive_fire_count + det.temporal_state.positive_smoke_count}/5)
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-dim)', fontSize: '0.82rem' }}>
                          Standard ({det.temporal_state?.positive_fire_count ?? 0}/5)
                        </span>
                      )}
                    </td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                      {new Date(det.created_at).toLocaleTimeString()}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button
                        onClick={() => onNavigate(`/detections/${det.id}`)}
                        className="btn btn-secondary"
                        style={{ padding: '6px 12px', fontSize: '0.78rem' }}
                      >
                        <Eye size={13} />
                        <span>Grad-CAM</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

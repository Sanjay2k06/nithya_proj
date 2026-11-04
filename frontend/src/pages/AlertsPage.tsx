import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  ShieldCheck,
  Clock,
  CheckCircle,
  Eye,
  Filter,
  RefreshCw,
  Flame,
  Cloud
} from 'lucide-react';
import { api } from '../services/api';
import { Alert } from '../types';
import { Badge } from '../components/common/Badge';

interface AlertsPageProps {
  onNavigate: (path: string) => void;
}

export const AlertsPage: React.FC<AlertsPageProps> = ({ onNavigate }) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const data = await api.getAlerts(page, 20, statusFilter || undefined);
      setAlerts(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [page, statusFilter]);

  const handleUpdateStatus = async (alertId: string, newStatus: 'ACKNOWLEDGED' | 'CLOSED') => {
    try {
      await api.updateAlertStatus(alertId, newStatus);
      fetchAlerts();
    } catch (err) {
      alert(`Failed to update alert: ${err}`);
    }
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.85rem', color: '#fff', marginBottom: '6px' }}>Incident Triage & Alert Console</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem' }}>
            Multi-frame verified incidents, operator acknowledgement logs, and dispatch audit trails.
          </p>
        </div>
        <button onClick={fetchAlerts} className="btn btn-secondary">
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Incidents</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
        {[
          { label: 'All Incidents', val: '' },
          { label: 'Active', val: 'ACTIVE' },
          { label: 'Acknowledged', val: 'ACKNOWLEDGED' },
          { label: 'Resolved / Closed', val: 'CLOSED' }
        ].map((tab) => (
          <button
            key={tab.val}
            onClick={() => { setStatusFilter(tab.val); setPage(1); }}
            className={`btn ${statusFilter === tab.val ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.85rem', padding: '8px 16px' }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Alert Cards List */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-dim)' }}>
          <RefreshCw size={28} className="animate-spin" style={{ margin: '0 auto 12px' }} />
          <p>Loading alerts...</p>
        </div>
      ) : alerts.length === 0 ? (
        <div className="glass-card" style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-dim)' }}>
          <CheckCircle size={44} style={{ margin: '0 auto 12px', color: 'var(--color-normal)', opacity: 0.8 }} />
          <h3 style={{ color: '#fff', marginBottom: '6px' }}>Zero Active Incident Warnings</h3>
          <p style={{ fontSize: '0.88rem' }}>All surveillance sectors are currently clear or resolved.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {alerts.map((al) => (
            <div
              key={al.id}
              className="glass-card"
              style={{
                padding: '20px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderLeft: al.status === 'ACTIVE' ? '4px solid #ef4444' : '1px solid var(--border-glass)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '18px' }}>
                <div style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '10px',
                  background: al.alert_type === 'fire' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(148, 163, 184, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: al.alert_type === 'fire' ? '#ef4444' : '#cbd5e1'
                }}>
                  {al.alert_type === 'fire' ? <Flame size={22} /> : <Cloud size={22} />}
                </div>

                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                    <h3 style={{ fontSize: '1.05rem', color: '#fff' }}>
                      {al.camera_name || 'Observation Stream'} · {al.alert_type.toUpperCase()} ALERT
                    </h3>
                    <Badge type={al.status} />
                    <span className={`badge ${al.severity === 'CRITICAL' ? 'badge-fire' : 'badge-smoke'}`}>
                      {al.severity}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-dim)', display: 'flex', gap: '16px' }}>
                    <span>First Seen: {new Date(al.first_seen_at).toLocaleTimeString()}</span>
                    <span>Last Updated: {new Date(al.last_seen_at).toLocaleTimeString()}</span>
                    <span>Dispatch Notification: <strong style={{ color: al.notification_status === 'DELIVERED' ? 'var(--color-normal)' : '#ef4444' }}>{al.notification_status}</strong></span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                {al.detection_id && (
                  <button
                    onClick={() => onNavigate(`/detections/${al.detection_id}`)}
                    className="btn btn-secondary"
                    style={{ padding: '7px 12px', fontSize: '0.8rem' }}
                  >
                    <Eye size={14} />
                    <span>View Evidence</span>
                  </button>
                )}

                {al.status === 'ACTIVE' && (
                  <button
                    onClick={() => handleUpdateStatus(al.id, 'ACKNOWLEDGED')}
                    className="btn btn-secondary"
                    style={{ padding: '7px 12px', fontSize: '0.8rem' }}
                  >
                    <Clock size={14} />
                    <span>Acknowledge</span>
                  </button>
                )}

                {al.status !== 'CLOSED' && (
                  <button
                    onClick={() => handleUpdateStatus(al.id, 'CLOSED')}
                    className="btn btn-primary"
                    style={{ padding: '7px 14px', fontSize: '0.8rem', background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}
                  >
                    <ShieldCheck size={14} />
                    <span>Resolve / Close</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

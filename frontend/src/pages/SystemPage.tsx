import React, { useState, useEffect } from 'react';
import { Cpu, Server, Database, Radio, RefreshCw, CheckCircle, ShieldAlert } from 'lucide-react';
import { api } from '../services/api';
import { EnvironmentalReading, ModelStatus, TelegramStatus } from '../types';

export const SystemPage: React.FC = () => {
  const [health, setHealth] = useState<any>(null);
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [monitoringStatus, setMonitoringStatus] = useState<any>(null);
  const [demoMonitoringStatus, setDemoMonitoringStatus] = useState<any>(null);
  const [telegramStatus, setTelegramStatus] = useState<TelegramStatus | null>(null);
  const [environmentReadings, setEnvironmentReadings] = useState<EnvironmentalReading[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDiagnostics = async () => {
    setLoading(true);
    try {
      const [h, m, mon, demo, telegram, readings] = await Promise.all([
        api.getHealth(),
        api.getModelStatus(),
        api.getMonitoringStatus(),
        api.getDemoMonitoringStatus(),
        api.getTelegramStatus(),
        api.getEnvironmentalReadings(10)
      ]);
      setHealth(h);
      setModelStatus(m);
      setMonitoringStatus(mon);
      setDemoMonitoringStatus(demo);
      setTelegramStatus(telegram);
      setEnvironmentReadings(readings);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load system diagnostics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDiagnostics();
  }, []);

  return (
    <div className="page-container">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '1.85rem', color: '#fff', marginBottom: '6px' }}>System Diagnostics & Core Health</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem' }}>
            Underlying deep learning runtime, database status, checkpoint metadata, and active streaming threads.
          </p>
        </div>
        <button onClick={fetchDiagnostics} className="btn btn-secondary">
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Diagnostics</span>
        </button>
      </div>

      <div className="grid-2" style={{ gap: '24px' }}>
        {/* Model Card */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '18px' }}>
            <Cpu size={20} color="var(--color-flame)" />
            <h2 style={{ fontSize: '1.15rem', color: '#fff' }}>Deep Learning Inference Core</h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.88rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-dim)' }}>Architecture:</span>
              <span style={{ color: '#fff', fontWeight: 600 }}>{modelStatus?.model_name || 'FireNetCNN'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-dim)' }}>Status:</span>
              <span style={{ color: modelStatus?.loaded ? 'var(--color-normal)' : '#ef4444', fontWeight: 600 }}>
                {modelStatus?.loaded ? 'Loaded in Memory' : 'Unloaded'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-dim)' }}>Execution Device:</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-accent)' }}>{modelStatus?.device?.toUpperCase() || 'CPU'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-dim)' }}>Output Classes:</span>
              <span style={{ color: '#fff' }}>{modelStatus?.classes.join(', ')}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-dim)' }}>Demo Fixture Mode:</span>
              <span style={{ color: modelStatus?.demo_mode ? 'var(--color-warning)' : 'var(--color-normal)' }}>
                {modelStatus?.demo_mode ? 'Active (Untrained Test Weights)' : 'Disabled (Production Weights)'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-dim)' }}>Active Weights File:</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {modelStatus?.checkpoint_path}
              </span>
            </div>
          </div>

          {error && <div className="demo-error" role="alert">{error}</div>}
          <div className="system-extra-grid">
            <section className="glass-card system-extra-card">
              <div className="system-extra-title">
                <ShieldAlert size={19} />
                <h2>Optional Environmental Inputs</h2>
              </div>
              {environmentReadings.length === 0 ? (
                <p className="demo-empty-state">No sensor readings have been received. No environmental values are fabricated or inferred.</p>
              ) : (
                <div className="environment-readings">
                  {environmentReadings.map((reading) => (
                    <article key={reading.id} className="environment-reading">
                      <strong>{reading.source_id}</strong>
                      <time>{new Date(reading.recorded_at).toLocaleString()}</time>
                      <span>Temperature: {reading.temperature_c ?? '—'} °C</span>
                      <span>Humidity: {reading.humidity_percent ?? '—'}%</span>
                      <span>Wind: {reading.wind_speed_mps ?? '—'} m/s</span>
                      <span>Smoke sensor: {reading.smoke_sensor_value ?? '—'}</span>
                    </article>
                  ))}
                </div>
              )}
              <p className="system-extra-note">Sensor readings are supplementary decision support; they do not replace visual classification.</p>
            </section>

            <section className="glass-card system-extra-card">
              <div className="system-extra-title">
                <Radio size={19} />
                <h2>Monitoring and Notification Services</h2>
              </div>
              <div className="system-extra-row"><span>Video monitoring</span><strong>{demoMonitoringStatus?.is_monitoring || monitoringStatus?.active_workers_count ? 'RUNNING' : 'STOPPED'}</strong></div>
              <div className="system-extra-row"><span>Telegram</span><strong>{telegramStatus?.connection_status?.toUpperCase() ?? 'UNKNOWN'}</strong></div>
              <div className="system-extra-row"><span>Telegram enabled</span><strong>{telegramStatus?.enabled ? 'YES' : 'NO'}</strong></div>
              <div className="system-extra-row"><span>Recipient</span><strong>{telegramStatus?.recipient_hint ?? 'Not configured'}</strong></div>
              <p className="system-extra-note">Bot tokens are never returned by status APIs.</p>
            </section>
          </div>
        </div>

        {/* Database & API Backend */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '18px' }}>
            <Database size={20} color="var(--color-accent)" />
            <h2 style={{ fontSize: '1.15rem', color: '#fff' }}>Backend & Persistence Status</h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.88rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-dim)' }}>API Gateway:</span>
              <span style={{ color: 'var(--color-normal)', fontWeight: 600 }}>FastAPI (Uvicorn Async)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-dim)' }}>Database Engine:</span>
              <span style={{ color: health?.database === 'connected' ? 'var(--color-normal)' : '#ef4444', fontWeight: 600 }}>
                {health?.database === 'connected' ? 'Connected & Healthy' : 'Degraded'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-dim)' }}>Active Monitoring Threads:</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: '#fff', fontWeight: 700 }}>
                {monitoringStatus?.active_workers_count ?? 0}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-dim)' }}>Explainability Engine:</span>
              <span style={{ color: '#fff' }}>Grad-CAM (PyTorch Backward Hook)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-dim)' }}>Heartbeat Ping:</span>
              <span style={{ color: 'var(--text-muted)' }}>{health ? new Date(health.timestamp).toLocaleTimeString() : 'N/A'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

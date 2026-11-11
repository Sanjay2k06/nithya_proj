import React, { useState, useEffect } from 'react';
import { Settings, Save, RefreshCw, CheckCircle, Sliders, Shield } from 'lucide-react';
import { api } from '../services/api';
import { OperationalSettings } from '../types';

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<OperationalSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await api.getSettings();
      setSettings(data);
    } catch (err) {
      console.error('Failed to load settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!settings) return;
    try {
      setSaving(true);
      await api.updateSettings(settings);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      alert(`Failed to save settings: ${err}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading || !settings) {
    return (
      <div className="page-container" style={{ textAlign: 'center', padding: '60px 0' }}>
        <RefreshCw size={28} className="animate-spin" style={{ margin: '0 auto 12px' }} />
        <p>Loading operational settings...</p>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Header */}
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '1.85rem', color: '#fff', marginBottom: '6px' }}>Operational Configuration</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem' }}>
          Tune fire/smoke probability thresholds, multi-frame temporal windows, and incident cooldown timers.
        </p>
      </div>

      {saveSuccess && (
        <div className="glass-card" style={{
          padding: '14px 20px',
          marginBottom: '24px',
          background: 'rgba(16, 185, 129, 0.15)',
          borderColor: 'rgba(16, 185, 129, 0.4)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          color: '#10b981'
        }}>
          <CheckCircle size={18} />
          <span style={{ fontWeight: 600, fontSize: '0.88rem' }}>Settings updated successfully. Live temporal verifier reconfigured.</span>
        </div>
      )}

      <form onSubmit={handleSave} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Detection Thresholds */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '18px' }}>
            <Sliders size={18} color="var(--color-flame)" />
            <h2 style={{ fontSize: '1.15rem', color: '#fff' }}>Classification Decision Thresholds</h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <label style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>Fire Confidence Threshold</label>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--color-flame)' }}>
                  {(settings.fire_threshold * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0.50"
                max="0.95"
                step="0.05"
                value={settings.fire_threshold}
                onChange={(e) => setSettings({ ...settings, fire_threshold: parseFloat(e.target.value) })}
                style={{ width: '100%' }}
              />
              <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>Minimum softmax probability required to register a positive fire frame.</span>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <label style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>Smoke Confidence Threshold</label>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--color-accent)' }}>
                  {(settings.smoke_threshold * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0.50"
                max="0.95"
                step="0.05"
                value={settings.smoke_threshold}
                onChange={(e) => setSettings({ ...settings, smoke_threshold: parseFloat(e.target.value) })}
                style={{ width: '100%' }}
              />
              <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>Threshold for diffuse smoke column detection.</span>
            </div>
          </div>
        </div>

        {/* Temporal Verification Rules */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '18px' }}>
            <Shield size={18} color="var(--color-accent)" />
            <h2 style={{ fontSize: '1.15rem', color: '#fff' }}>Temporal Noise Filtering</h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            <div>
              <label style={{ fontSize: '0.88rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                Sliding Frame Window Size
              </label>
              <input
                type="number"
                min="3"
                max="20"
                value={settings.temporal_window}
                onChange={(e) => setSettings({ ...settings, temporal_window: parseInt(e.target.value) || 5 })}
                style={{ width: '100%', background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', color: '#fff', padding: '8px 12px', borderRadius: '6px' }}
              />
              <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>Number of consecutive sampled frames tracked in the rolling buffer.</span>
            </div>

            <div>
              <label style={{ fontSize: '0.88rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                Positives Required For Verification
              </label>
              <input
                type="number"
                min="2"
                max="15"
                value={settings.temporal_required_positives}
                onChange={(e) => setSettings({ ...settings, temporal_required_positives: parseInt(e.target.value) || 3 })}
                style={{ width: '100%', background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', color: '#fff', padding: '8px 12px', borderRadius: '6px' }}
              />
              <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>Candidate detections must meet or exceed this count inside the window.</span>
            </div>

            <div>
              <label style={{ fontSize: '0.88rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                Alert Cooldown Window (Seconds)
              </label>
              <input
                type="number"
                min="10"
                max="600"
                value={settings.alert_cooldown_seconds}
                onChange={(e) => setSettings({ ...settings, alert_cooldown_seconds: parseInt(e.target.value) || 60 })}
                style={{ width: '100%', background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', color: '#fff', padding: '8px 12px', borderRadius: '6px' }}
              />
              <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>Prevents duplicate alert dispatch for the same active incident stream.</span>
            </div>
          </div>
        </div>

        {/* Submit */}
        <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
          <button type="submit" disabled={saving} className="btn btn-primary" style={{ padding: '10px 24px' }}>
            <Save size={16} />
            <span>{saving ? 'Applying Settings...' : 'Save & Reconfigure Live Engine'}</span>
          </button>
        </div>
      </form>

      <section className="glass-card optional-input-settings">
        <div>
          <h2>Optional environmental sensor inputs</h2>
          <p>No sensor hardware is configured. Real readings may be posted to the backend ingestion endpoint and will be shown in System Health; missing values are never filled with estimates.</p>
          <code>POST /api/v1/environment/readings</code>
          <p>Temperature, humidity, wind, and smoke-sensor readings remain supplementary decision support and do not replace FireNet-CNN classification.</p>
        </div>
        <div>
          <h2>Simulated CCTV sources</h2>
          <p>CAM 01 and CAM 02 use the local MP4 files and are demonstration footage, not physical camera connections.</p>
        </div>
      </section>
    </div>
  );
};

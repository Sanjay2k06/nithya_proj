import React, { useEffect, useState } from 'react';
import { Shield, Radio, Server, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';

export const Navbar: React.FC = () => {
  const [health, setHealth] = useState<{ status: string; database: string; model_loaded: boolean } | null>(null);
  const [loading, setLoading] = useState(false);

  const checkHealth = async () => {
    setLoading(true);
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch {
      setHealth({ status: 'offline', database: 'disconnected', model_loaded: false });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="top-navbar">
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div className="pulse-dot live" />
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Live Surveillance Core
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '18px' }}>
        {/* Model loaded badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
          <Radio size={14} color="var(--color-accent)" />
          <span>Model:</span>
          <span style={{ color: health?.model_loaded ? 'var(--color-normal)' : 'var(--color-flame)', fontWeight: 600 }}>
            {health?.model_loaded ? 'FireNet-CNN Active' : 'Offline / Standby'}
          </span>
        </div>

        {/* Database status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
          <Server size={14} color="var(--color-accent)" />
          <span>DB:</span>
          <span style={{ color: health?.database === 'connected' ? 'var(--color-normal)' : 'var(--color-flame)', fontWeight: 600 }}>
            {health?.database === 'connected' ? 'Connected' : 'Degraded'}
          </span>
        </div>

        {/* Refresh button */}
        <button
          onClick={checkHealth}
          className="btn btn-secondary"
          style={{ padding: '6px 10px', fontSize: '0.75rem' }}
          title="Refresh Backend Health"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          <span>Sync</span>
        </button>
      </div>
    </header>
  );
};

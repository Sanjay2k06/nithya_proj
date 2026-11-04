import React from 'react';
import {
  Flame,
  LayoutDashboard,
  Radio,
  Eye,
  AlertTriangle,
  BarChart3,
  Cpu,
  Settings
} from 'lucide-react';

interface SidebarProps {
  currentPath: string;
  onNavigate: (path: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentPath, onNavigate }) => {
  const navItems = [
    { path: '/', label: 'Overview', icon: <LayoutDashboard size={18} /> },
    { path: '/monitoring', label: 'Live Monitoring', icon: <Radio size={18} /> },
    { path: '/detections', label: 'Detection History', icon: <Eye size={18} /> },
    { path: '/alerts', label: 'Verified Alerts', icon: <AlertTriangle size={18} /> },
    { path: '/analytics', label: 'Analytics & XAI', icon: <BarChart3 size={18} /> },
    { path: '/system', label: 'System Health', icon: <Cpu size={18} /> },
    { path: '/settings', label: 'Settings', icon: <Settings size={18} /> }
  ];

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '0 8px 24px', borderBottom: '1px solid var(--border-subtle)', marginBottom: '20px' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #ff5722 0%, #ff8a65 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(255, 87, 34, 0.4)'
        }}>
          <Flame size={22} color="#ffffff" />
        </div>
        <div className="brand-text">
          <div style={{ fontSize: '1.05rem', fontWeight: 800, fontFamily: 'var(--font-heading)', color: '#fff' }}>
            FireNet-XAI
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', letterSpacing: '0.04em' }}>
            Edge Surveillance AI
          </div>
        </div>
      </div>

      {/* Nav List */}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px', flex: 1 }}>
        {navItems.map((item) => {
          const isActive = currentPath === item.path || (item.path !== '/' && currentPath.startsWith(item.path));
          return (
            <button
              key={item.path}
              onClick={() => onNavigate(item.path)}
              className={`nav-item ${isActive ? 'active' : ''}`}
              style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left' }}
            >
              {item.icon}
              <span className="nav-text">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* System info footer */}
      <div style={{ padding: '12px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
        <div style={{ fontSize: '0.74rem', color: 'var(--text-dim)', marginBottom: '4px' }}>Model Version</div>
        <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-main)', fontFamily: 'var(--font-mono)' }}>FireNet-CNN v1.0</div>
      </div>
    </aside>
  );
};

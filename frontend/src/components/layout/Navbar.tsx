import React, { useEffect, useState, useRef } from 'react';
import {
  Flame,
  Bell,
  Search,
  Command,
  ExternalLink,
  Cpu,
  Settings,
  Radio,
  Eye,
  AlertTriangle,
  BarChart3,
  RefreshCw,
  X,
  FileCode2,
  Image as ImageIcon,
  Video,
  Activity
} from 'lucide-react';
import { api } from '../../services/api';

interface NavbarProps {
  currentPath?: string;
  onNavigate?: (path: string) => void;
}

interface SearchItem {
  id: string;
  title: string;
  category: string;
  path?: string;
  action?: () => void;
  icon: React.ReactNode;
}

export const Navbar: React.FC<NavbarProps> = ({ currentPath = '/', onNavigate }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchModalOpen, setSearchModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);

  // Backend Health State (Preserved from original)
  const [health, setHealth] = useState<{ status: string; database: string; model_loaded: boolean } | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(false);
  const [activeAlertCount, setActiveAlertCount] = useState<number | null>(null);
  const [activeMonitoringCount, setActiveMonitoringCount] = useState<number | null>(null);
  const [demoMonitoringActive, setDemoMonitoringActive] = useState(false);

  // Refs for accessibility
  const mobileMenuRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const checkHealth = async () => {
    setLoadingHealth(true);
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch {
      setHealth({ status: 'offline', database: 'disconnected', model_loaded: false });
    } finally {
      setLoadingHealth(false);
    }
    try {
      const data = await api.getAlerts(1, 1, 'ACTIVE');
      setActiveAlertCount(data.total);
    } catch {
      setActiveAlertCount(null);
    }
    try {
      const monitoring = await api.getMonitoringStatus();
      setActiveMonitoringCount(monitoring.active_workers_count);
    } catch {
      setActiveMonitoringCount(null);
    }
    try {
      const demoStatus = await api.getDemoMonitoringStatus();
      setDemoMonitoringActive(demoStatus.is_monitoring);
    } catch {
      setDemoMonitoringActive(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    const refreshStatus = async () => {
      try {
        const data = await api.getHealth();
        if (isMounted) setHealth(data);
      } catch {
        if (isMounted) setHealth({ status: 'offline', database: 'disconnected', model_loaded: false });
      }

      try {
        const data = await api.getAlerts(1, 1, 'ACTIVE');
        if (isMounted) setActiveAlertCount(data.total);
      } catch {
        if (isMounted) setActiveAlertCount(null);
      }

      try {
        const monitoring = await api.getMonitoringStatus();
        if (isMounted) setActiveMonitoringCount(monitoring.active_workers_count);
      } catch {
        if (isMounted) setActiveMonitoringCount(null);
      }

      try {
        const demoStatus = await api.getDemoMonitoringStatus();
        if (isMounted) setDemoMonitoringActive(demoStatus.is_monitoring);
      } catch {
        if (isMounted) setDemoMonitoringActive(false);
      }
    };
    void refreshStatus();

    const interval = setInterval(refreshStatus, 15000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const openSearch = () => {
    setSearchQuery('');
    setSelectedIndex(0);
    setSearchModalOpen(true);
  };

  const closeSearch = () => {
    setSearchModalOpen(false);
  };

  // Keyboard shortcut for Cmd+K / Ctrl+K & Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setSearchModalOpen(prev => {
          if (!prev) {
            setSearchQuery('');
            setSelectedIndex(0);
          }
          return !prev;
        });
      } else if (e.key === 'Escape') {
        setSearchModalOpen(false);
        setMobileMenuOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Autofocus search input when modal opens
  useEffect(() => {
    if (searchModalOpen) {
      const timer = setTimeout(() => searchInputRef.current?.focus(), 50);
      return () => clearTimeout(timer);
    }
  }, [searchModalOpen]);

  // Lock body scroll when mobile menu or search modal is open
  useEffect(() => {
    if (mobileMenuOpen || searchModalOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [mobileMenuOpen, searchModalOpen]);

  const handleNav = (path: string) => {
    if (onNavigate) {
      onNavigate(path);
    } else {
      window.history.pushState({}, '', path);
      window.dispatchEvent(new PopStateEvent('popstate'));
    }
    setMobileMenuOpen(false);
    setSearchModalOpen(false);
  };

  const navLinks = [
    { label: 'Overview', path: '/dashboard', icon: <Eye size={17} /> },
    { label: 'Live Monitoring', path: '/monitoring', icon: <Radio size={17} /> },
    { label: 'Image Analysis', path: '/image-analysis', icon: <ImageIcon size={17} /> },
    { label: 'Video Analysis', path: '/video-analysis', icon: <Video size={17} /> },
    { label: 'Detection History', path: '/detections', icon: <Flame size={17} /> },
    { label: 'Incident History', path: '/incidents', icon: <AlertTriangle size={17} /> },
    { label: 'Telegram Notifications', path: '/notifications', icon: <Bell size={17} /> },
    { label: 'Analytics & XAI', path: '/analytics', icon: <BarChart3 size={17} /> },
    { label: 'System Health', path: '/system-health', icon: <Activity size={17} /> },
    { label: 'Settings', path: '/settings', icon: <Settings size={17} /> },
  ];

  const currentPageTitle = currentPath.startsWith('/detections/')
    ? 'Detection Details'
    : currentPath === '/' ? 'Overview'
      : currentPath === '/alerts' ? 'Incident History'
        : currentPath === '/system' ? 'System Health'
          : navLinks.find((link) => link.path === currentPath)?.label ?? 'Overview';

  const searchItems: SearchItem[] = [
    {
      id: 'p-overview',
      title: 'Surveillance Overview Dashboard',
      category: 'Pages',
      path: '/dashboard',
      icon: <Eye size={16} />
    },
    {
      id: 'p-monitoring',
      title: 'Live Camera Streams & Inference',
      category: 'Surveillance',
      path: '/monitoring',
      icon: <Radio size={16} />
    },
    {
      id: 'p-detections',
      title: 'Detection History & Grad-CAM Heatmaps',
      category: 'Computer Vision',
      path: '/detections',
      icon: <Flame size={16} />
    },
    {
      id: 'p-alerts',
      title: 'Verified Incident Triage Console',
      category: 'Incident Response',
      path: '/incidents',
      icon: <AlertTriangle size={16} />
    },
    {
      id: 'p-notifications',
      title: 'Telegram Notification History',
      category: 'Incident Response',
      path: '/notifications',
      icon: <Bell size={16} />
    },
    {
      id: 'p-analytics',
      title: 'Model Benchmarks & Statistical XAI',
      category: 'Model Analytics',
      path: '/analytics',
      icon: <BarChart3 size={16} />
    },
    {
      id: 'p-system',
      title: 'System Diagnostics & GPU/Worker Status',
      category: 'Infrastructure',
      path: '/system-health',
      icon: <Cpu size={16} />
    },
    {
      id: 'p-settings',
      title: 'Surveillance Thresholds & Cameras',
      category: 'Configuration',
      path: '/settings',
      icon: <Settings size={16} />
    },
    {
      id: 'a-docs',
      title: 'Interactive API Documentation (Swagger)',
      category: 'Developer API',
      action: () => window.open('http://127.0.0.1:8010/docs', '_blank'),
      icon: <FileCode2 size={16} />
    }
  ];

  const filteredItems = searchItems.filter(item =>
    item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSelectSearchItem = (item: SearchItem) => {
    if (item.action) {
      item.action();
    } else if (item.path) {
      handleNav(item.path);
    }
    setSearchModalOpen(false);
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev + 1) % (filteredItems.length || 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev - 1 + filteredItems.length) % (filteredItems.length || 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredItems[selectedIndex]) {
        handleSelectSearchItem(filteredItems[selectedIndex]);
      }
    }
  };

  return (
    <>
      <header className="modern-top-nav" role="banner">
        <div className="nav-container">
          {/* Brand and current page */}
          <div className="nav-brand-group">
            <button
              onClick={() => handleNav('/dashboard')}
              className="nav-brand-button"
              aria-label="ForestWatch AI home"
            >
              <div className="brand-title-wrap">
                <span className="brand-name">FORESTWATCH AI</span>
              </div>
            </button>
          </div>

          <div className="nav-current-page" aria-live="polite">{currentPageTitle}</div>

          {/* =========================================================
              RIGHT: Action Area (Search, Theme, CTAs, Mobile Hamburger)
             ========================================================= */}
          <div className="nav-action-area">
            {/* Global Search Trigger (Cmd + K) */}
            <button
              onClick={openSearch}
              className="nav-search-trigger"
              aria-label="Search surveillance system (Press Ctrl+K or Cmd+K)"
              title="Global Search (Ctrl+K / ⌘K)"
            >
              <Search size={14} className="search-icon" />
              <span className="search-placeholder">Quick search...</span>
              <kbd className="search-kbd">
                <Command size={10} />
                <span>K</span>
              </kbd>
            </button>

            <div
              className="nav-health-status"
              title={`Backend: ${health?.status ?? 'connecting'}, active camera workers: ${activeMonitoringCount ?? 'unknown'}, Database: ${health?.database ?? 'unknown'}, Model: ${health?.model_loaded ? 'loaded' : 'unavailable'}`}
            >
              <span className={`status-signal ${health?.status === 'offline' ? 'offline' : health?.status === 'healthy' ? 'live' : 'standby'}`} />
              <span className="status-text">
                {health?.status === 'offline'
                  ? 'Backend offline'
                  : demoMonitoringActive
                    ? 'Demo monitoring active'
                    : activeMonitoringCount && activeMonitoringCount > 0
                      ? `Monitoring ${activeMonitoringCount}`
                    : health?.status === 'healthy'
                      ? 'System online'
                      : 'Connecting'}
              </span>
              <button
                onClick={checkHealth}
                className="status-sync-btn"
                title="Sync Backend State"
                aria-label="Sync Backend State"
              >
                <RefreshCw size={12} className={loadingHealth ? 'spin' : ''} />
              </button>
            </div>

            <button
              onClick={() => handleNav('/alerts')}
              className="nav-notification-button"
              aria-label={activeAlertCount === null ? 'Open verified alerts' : `${activeAlertCount} active alerts`}
              title={activeAlertCount === null ? 'Verified alerts' : `${activeAlertCount} active alerts`}
            >
              <Bell size={17} />
              {activeAlertCount !== null && activeAlertCount > 0 && (
                <span className="nav-notification-count">{activeAlertCount > 99 ? '99+' : activeAlertCount}</span>
              )}
            </button>

            <button
              onClick={() => setMobileMenuOpen(prev => !prev)}
              className={`nav-hamburger-btn ${mobileMenuOpen ? 'open' : ''}`}
              aria-label="Toggle navigation menu"
              aria-expanded={mobileMenuOpen}
            >
              <span className="hamburger-line top" />
              <span className="hamburger-line middle" />
              <span className="hamburger-line bottom" />
            </button>
          </div>
        </div>

        {/* Responsive navigation drawer */}
        {mobileMenuOpen && (
          <div className="mobile-drawer-overlay" onClick={() => setMobileMenuOpen(false)}>
            <div
              className="mobile-drawer-panel"
              ref={mobileMenuRef}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="drawer-header">
                <div className="drawer-brand">
                  <span className="brand-name">FORESTWATCH AI</span>
                </div>
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="drawer-close-btn"
                  aria-label="Close menu"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Mobile Quick Search Button */}
              <div style={{ padding: '12px 16px' }}>
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    openSearch();
                  }}
                  className="mobile-search-trigger"
                >
                  <Search size={14} />
                  <span>Search commands & pages...</span>
                  <kbd className="search-kbd">⌘K</kbd>
                </button>
              </div>

              <div className="drawer-nav-list">
                <div className="drawer-section-label">WORKSPACE</div>
                {navLinks.map((link) => {
                  const isActive = currentPath === link.path
                    || (link.path === '/dashboard' && currentPath === '/')
                    || (link.path !== '/dashboard' && currentPath.startsWith(link.path));
                  return (
                    <button
                      key={link.path}
                      onClick={() => handleNav(link.path)}
                      className={`drawer-link ${isActive ? 'active' : ''}`}
                    >
                      <span className="drawer-link-content">{link.icon}<span>{link.label}</span></span>
                      {isActive && <span className="drawer-active-tag">Current</span>}
                    </button>
                  );
                })}

                <div className="drawer-section-label" style={{ marginTop: '16px' }}>DEVELOPER</div>
                <a
                  href="http://127.0.0.1:8010/docs"
                  target="_blank"
                  rel="noreferrer"
                  className="drawer-link"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    API Reference <ExternalLink size={12} />
                  </span>
                </a>
              </div>

              <div className="drawer-footer">
                <div className="drawer-actions">
                  <button
                    onClick={() => handleNav('/monitoring')}
                    className="nav-cta-primary full-width"
                  >
                    <Radio size={14} />
                    <span>Launch Live Monitor</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </header>

      {/* =========================================================
          GLOBAL COMMAND PALETTE (Cmd+K / Ctrl+K Search Modal)
         ========================================================= */}
      {searchModalOpen && (
        <div className="command-palette-backdrop" onClick={closeSearch}>
          <div
            className="command-palette-card"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Command search palette"
          >
            <div className="command-palette-input-wrapper">
              <Search size={18} className="command-search-icon" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setSelectedIndex(0);
                }}
                onKeyDown={handleSearchKeyDown}
                placeholder="Search surveillance pages, camera streams, diagnostics..."
                className="command-palette-input"
              />
              <kbd className="command-palette-esc" onClick={closeSearch}>
                ESC
              </kbd>
            </div>

            <div className="command-palette-results">
              {filteredItems.length === 0 ? (
                <div className="command-palette-empty">
                  No matching surveillance resources found for "{searchQuery}".
                </div>
              ) : (
                <div className="command-palette-list">
                  {filteredItems.map((item, index) => (
                    <div
                      key={item.id}
                      onClick={() => handleSelectSearchItem(item)}
                      onMouseEnter={() => setSelectedIndex(index)}
                      className={`command-item ${index === selectedIndex ? 'selected' : ''}`}
                      role="button"
                      tabIndex={0}
                    >
                      <div className="command-item-icon-box">
                        {item.icon}
                      </div>
                      <div className="command-item-info">
                        <div className="command-item-title">{item.title}</div>
                        <div className="command-item-category">{item.category}</div>
                      </div>
                      {index === selectedIndex && (
                        <span className="command-item-enter">↵</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="command-palette-footer">
              <div className="command-shortcuts">
                <span><kbd>↑</kbd> <kbd>↓</kbd> Navigate</span>
                <span><kbd>↵</kbd> Select</span>
                <span><kbd>ESC</kbd> Close</span>
              </div>
              <div className="command-system-hint">
                FireNet-CNN Surveillance Core
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

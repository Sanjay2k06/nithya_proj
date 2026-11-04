import React, { useEffect, useState, useRef } from 'react';
import {
  Flame,
  Search,
  Command,
  Sun,
  Moon,
  ChevronDown,
  ExternalLink,
  Cpu,
  Settings,
  Radio,
  Eye,
  AlertTriangle,
  BarChart3,
  RefreshCw,
  X,
  FileCode2
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
  // Navigation & Dropdown State
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchModalOpen, setSearchModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [selectedIndex, setSelectedIndex] = useState(0);

  // Backend Health State (Preserved from original)
  const [health, setHealth] = useState<{ status: string; database: string; model_loaded: boolean } | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(false);

  // Refs for accessibility & outside click
  const dropdownRef = useRef<HTMLDivElement>(null);
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
  };

  useEffect(() => {
    let isMounted = true;
    api.getHealth()
      .then(data => { if (isMounted) setHealth(data); })
      .catch(() => { if (isMounted) setHealth({ status: 'offline', database: 'disconnected', model_loaded: false }); });

    const interval = setInterval(() => {
      api.getHealth()
        .then(data => { if (isMounted) setHealth(data); })
        .catch(() => { if (isMounted) setHealth({ status: 'offline', database: 'disconnected', model_loaded: false }); });
    }, 15000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Sync theme with DOM
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };

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
        setDropdownOpen(false);
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

  // Outside click listener for dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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
    setDropdownOpen(false);
    setMobileMenuOpen(false);
    setSearchModalOpen(false);
  };

  const navLinks = [
    { label: 'Overview', path: '/' },
    { label: 'Live Monitoring', path: '/monitoring' },
    { label: 'Detections', path: '/detections' },
    { label: 'Alerts', path: '/alerts' },
    { label: 'Analytics & XAI', path: '/analytics' },
  ];

  const searchItems: SearchItem[] = [
    {
      id: 'p-overview',
      title: 'Surveillance Overview Dashboard',
      category: 'Pages',
      path: '/',
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
      path: '/alerts',
      icon: <AlertTriangle size={16} />
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
      path: '/system',
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
          {/* =========================================================
              LEFT: Brand Logo & Live Signal
             ========================================================= */}
          <div className="nav-brand-group">
            <button
              onClick={() => handleNav('/')}
              className="nav-brand-button"
              aria-label="FireNet XAI Home"
            >
              <div className="brand-icon-wrapper">
                <Flame size={20} className="brand-flame-icon" />
              </div>
              <div className="brand-title-wrap">
                <span className="brand-name">FireNet<span className="brand-accent">XAI</span></span>
                <span className="brand-sub">SURVEILLANCE</span>
              </div>
            </button>

            {/* Tiny Mint Live Signal (Modern Dark design system token: --dp-color-live) */}
            <div className="nav-live-badge" title="Surveillance Core Live">
              <span className="live-dot" />
              <span className="live-label">LIVE</span>
            </div>
          </div>

          {/* =========================================================
              CENTER: Primary Navigation Links
             ========================================================= */}
          <nav className="nav-center-menu" role="navigation" aria-label="Primary Navigation">
            {navLinks.map((link) => {
              const isActive = currentPath === link.path || (link.path !== '/' && currentPath.startsWith(link.path));
              return (
                <button
                  key={link.path}
                  onClick={() => handleNav(link.path)}
                  className={`nav-pill-link ${isActive ? 'active' : ''}`}
                >
                  {link.label}
                  {isActive && <span className="nav-pill-indicator" />}
                </button>
              );
            })}

            {/* Multi-Level Dropdown: Resources & System */}
            <div className="nav-dropdown-wrapper" ref={dropdownRef}>
              <button
                onClick={() => setDropdownOpen(prev => !prev)}
                className={`nav-pill-link dropdown-trigger ${dropdownOpen ? 'dropdown-open' : ''}`}
                aria-haspopup="true"
                aria-expanded={dropdownOpen}
                aria-label="Open resources and system menu"
              >
                <span>Resources</span>
                <ChevronDown size={14} className={`dropdown-chevron ${dropdownOpen ? 'rotate' : ''}`} />
              </button>

              {dropdownOpen && (
                <div className="nav-dropdown-menu" role="menu">
                  <div className="dropdown-section-title">PLATFORM TOOLS</div>
                  <button
                    onClick={() => handleNav('/system')}
                    className="dropdown-item"
                    role="menuitem"
                  >
                    <div className="dropdown-item-icon">
                      <Cpu size={16} />
                    </div>
                    <div className="dropdown-item-content">
                      <div className="dropdown-item-title">System Diagnostics</div>
                      <div className="dropdown-item-desc">Hardware utilization, worker threads & GPU</div>
                    </div>
                  </button>

                  <button
                    onClick={() => handleNav('/settings')}
                    className="dropdown-item"
                    role="menuitem"
                  >
                    <div className="dropdown-item-icon">
                      <Settings size={16} />
                    </div>
                    <div className="dropdown-item-content">
                      <div className="dropdown-item-title">Surveillance Settings</div>
                      <div className="dropdown-item-desc">Confidence thresholds, camera feeds & alert rules</div>
                    </div>
                  </button>

                  <div className="dropdown-divider" />
                  <div className="dropdown-section-title">SPECIFICATIONS & API</div>

                  <a
                    href="http://127.0.0.1:8010/docs"
                    target="_blank"
                    rel="noreferrer"
                    className="dropdown-item"
                    role="menuitem"
                    onClick={() => setDropdownOpen(false)}
                  >
                    <div className="dropdown-item-icon">
                      <FileCode2 size={16} />
                    </div>
                    <div className="dropdown-item-content">
                      <div className="dropdown-item-title" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        Swagger REST API <ExternalLink size={12} />
                      </div>
                      <div className="dropdown-item-desc">Interactive OpenAPI endpoints & schemas</div>
                    </div>
                  </a>
                </div>
              )}
            </div>
          </nav>

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

            {/* Backend Health Sync & Status */}
            <div className="nav-health-status" title={`Model: ${health?.model_loaded ? 'Active' : 'Standby'}, DB: ${health?.database || 'Pending'}`}>
              <span className={`status-signal ${health?.model_loaded ? 'live' : 'standby'}`} />
              <span className="status-text">{health?.model_loaded ? 'FireNet 1.0' : 'Standby'}</span>
              <button
                onClick={checkHealth}
                className="status-sync-btn"
                title="Sync Backend State"
                aria-label="Sync Backend State"
              >
                <RefreshCw size={12} className={loadingHealth ? 'spin' : ''} />
              </button>
            </div>

            {/* Dark / Light Mode Toggle Switch */}
            <button
              onClick={toggleTheme}
              className="nav-theme-toggle"
              role="switch"
              aria-checked={theme === 'light'}
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            >
              <div className={`theme-toggle-slider ${theme === 'light' ? 'light' : 'dark'}`}>
                {theme === 'dark' ? <Moon size={13} className="theme-icon" /> : <Sun size={13} className="theme-icon" />}
              </div>
            </button>

            {/* Secondary CTA Button ("Docs" / Operator Guide) */}
            <a
              href="http://127.0.0.1:8010/docs"
              target="_blank"
              rel="noreferrer"
              className="nav-cta-secondary"
            >
              Docs
            </a>

            {/* Primary CTA Button ("Live Monitor" - Filled pill with rounded corners) */}
            <button
              onClick={() => handleNav('/monitoring')}
              className="nav-cta-primary"
            >
              <Radio size={14} className="cta-icon" />
              <span>Live Monitor</span>
            </button>

            {/* Mobile Animated Hamburger Trigger */}
            <button
              onClick={() => setMobileMenuOpen(prev => !prev)}
              className={`nav-hamburger-btn ${mobileMenuOpen ? 'open' : ''}`}
              aria-label="Toggle navigation drawer"
              aria-expanded={mobileMenuOpen}
            >
              <span className="hamburger-line top" />
              <span className="hamburger-line middle" />
              <span className="hamburger-line bottom" />
            </button>
          </div>
        </div>

        {/* =========================================================
            MOBILE SLIDE-OUT DRAWER
           ========================================================= */}
        {mobileMenuOpen && (
          <div className="mobile-drawer-overlay" onClick={() => setMobileMenuOpen(false)}>
            <div
              className="mobile-drawer-panel"
              ref={mobileMenuRef}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="drawer-header">
                <div className="drawer-brand">
                  <div className="brand-icon-wrapper small">
                    <Flame size={16} />
                  </div>
                  <span className="brand-name">FireNet<span className="brand-accent">XAI</span></span>
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
                <div className="drawer-section-label">SURVEILLANCE WORKSPACE</div>
                {navLinks.map((link) => {
                  const isActive = currentPath === link.path || (link.path !== '/' && currentPath.startsWith(link.path));
                  return (
                    <button
                      key={link.path}
                      onClick={() => handleNav(link.path)}
                      className={`drawer-link ${isActive ? 'active' : ''}`}
                    >
                      <span>{link.label}</span>
                      {isActive && <span className="drawer-active-tag">Current</span>}
                    </button>
                  );
                })}

                <div className="drawer-section-label" style={{ marginTop: '16px' }}>SYSTEM & ADVANCED</div>
                <button
                  onClick={() => handleNav('/system')}
                  className="drawer-link"
                >
                  <span>System Diagnostics</span>
                </button>
                <button
                  onClick={() => handleNav('/settings')}
                  className="drawer-link"
                >
                  <span>Operator Settings</span>
                </button>
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
                <div className="drawer-theme-row">
                  <span style={{ fontSize: '0.85rem', color: 'var(--dp-color-read)' }}>Color Mode</span>
                  <button
                    onClick={toggleTheme}
                    className="nav-theme-toggle"
                    role="switch"
                    aria-checked={theme === 'light'}
                    aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
                  >
                    <div className={`theme-toggle-slider ${theme === 'light' ? 'light' : 'dark'}`}>
                      {theme === 'dark' ? <Moon size={13} /> : <Sun size={13} />}
                    </div>
                  </button>
                </div>

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

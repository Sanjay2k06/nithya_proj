import React, { useState, useEffect, useCallback } from 'react';
import { Navbar } from './components/layout/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { DetectionsPage } from './pages/DetectionsPage';
import { DetectionDetailPage } from './pages/DetectionDetailPage';
import { AlertsPage } from './pages/AlertsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SettingsPage } from './pages/SettingsPage';
import { SystemPage } from './pages/SystemPage';
import { NotificationsPage } from './pages/NotificationsPage';
import { LiveMonitoringPage } from './pages/LiveMonitoringPage';
import { ImageAnalysisPage } from './pages/ImageAnalysisPage';
import { VideoAnalysisPage } from './pages/VideoAnalysisPage';
import { api } from './services/api';
import { useScrollReveal } from './hooks/useScrollReveal';
import { useParallax } from './hooks/useParallax';

export const App: React.FC = () => {
  const [currentPath, setCurrentPath] = useState<string>(window.location.pathname || '/');
  const [showSplash, setShowSplash] = useState(true);
  const [splashFading, setSplashFading] = useState(false);

  // Activate scroll-reveal and dynamic parallax depth systems
  useScrollReveal(currentPath);
  useParallax();

  const dismissSplash = useCallback(() => {
    setSplashFading(true);
    window.setTimeout(() => {
      setShowSplash(false);
    }, 600);
  }, []);

  useEffect(() => {
    let cancelled = false;
    let dismissTimer: number | undefined;
    const startedAt = Date.now();

    const healthCheck = api.getHealth().catch(() => undefined);
    const initializationDeadline = new Promise<void>((resolve) => {
      window.setTimeout(resolve, 1500);
    });

    Promise.race([healthCheck, initializationDeadline]).then(() => {
      const remainingSplashTime = Math.max(0, 4800 - (Date.now() - startedAt));
      dismissTimer = window.setTimeout(() => {
        if (!cancelled) {
          dismissSplash();
        }
      }, remainingSplashTime);
    });

    return () => {
      cancelled = true;
      if (dismissTimer !== undefined) window.clearTimeout(dismissTimer);
    };
  }, [dismissSplash]);

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname || '/');
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigate = (path: string) => {
    window.history.pushState({}, '', path);
    setCurrentPath(path);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const renderContent = () => {
    if (currentPath === '/' || currentPath === '/dashboard') {
      return <DashboardPage onNavigate={navigate} />;
    }
    if (currentPath === '/monitoring') {
      return <LiveMonitoringPage />;
    }
    if (currentPath === '/image-analysis') {
      return <ImageAnalysisPage />;
    }
    if (currentPath === '/video-analysis') {
      return <VideoAnalysisPage />;
    }
    if (currentPath === '/detections') {
      return <DetectionsPage onNavigate={navigate} />;
    }
    if (currentPath.startsWith('/detections/')) {
      const id = currentPath.split('/')[2];
      return <DetectionDetailPage detectionId={id} onNavigate={navigate} />;
    }
    if (currentPath === '/alerts' || currentPath === '/incidents') {
      return <AlertsPage onNavigate={navigate} />;
    }
    if (currentPath === '/analytics') {
      return <AnalyticsPage />;
    }
    if (currentPath === '/settings') {
      return <SettingsPage />;
    }
    if (currentPath === '/system' || currentPath === '/system-health') {
      return <SystemPage />;
    }
    if (currentPath === '/notifications') {
      return <NotificationsPage />;
    }
    return <DashboardPage onNavigate={navigate} />;
  };

  if (showSplash) {
    return (
      <main
        className={`splash-screen ${splashFading ? 'fade-out' : ''}`}
        aria-label="Starting ForestWatch AI"
      >
        <video
          className="splash-video"
          autoPlay
          loop
          muted
          playsInline
          preload="auto"
          aria-hidden="true"
          tabIndex={-1}
        >
          <source src="/splash.MP4" type="video/mp4" />
          <source src="/splash.mp4" type="video/mp4" />
          <source src="/splash-landscape.mp4" type="video/mp4" />
        </video>
        <div className="splash-overlay" />
        <div className="splash-content">
          <h1>FORESTWATCH AI</h1>
          <p className="splash-tagline">Real-Time Autonomous Wildfire Detection & Explainable AI Early Warning Sentinel</p>
          <div className="splash-loader" role="status" aria-label="Loading application">
            <span />
          </div>
          <p className="splash-loading-text">INITIALIZING NEURAL PIPELINE & SURVEILLANCE TELEMETRY</p>
          <button
            type="button"
            className="splash-skip-btn"
            onClick={dismissSplash}
            aria-label="Skip to main dashboard"
          >
            <span>Skip Intro</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </main>
    );
  }

  return (
    <div className="app-layout">
      {/* Dynamic ambient parallax depth backdrop */}
      <div className="ambient-parallax-container" aria-hidden="true">
        <div className="ambient-orb ambient-orb-1" />
        <div className="ambient-orb ambient-orb-2" />
        <div className="ambient-orb ambient-orb-3" />
      </div>

      <Navbar currentPath={currentPath} onNavigate={navigate} />
      <div className="app-body">
        <main className="main-content">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

export default App;

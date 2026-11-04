import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Navbar } from './components/layout/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { MonitoringPage } from './pages/MonitoringPage';
import { DetectionsPage } from './pages/DetectionsPage';
import { DetectionDetailPage } from './pages/DetectionDetailPage';
import { AlertsPage } from './pages/AlertsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SettingsPage } from './pages/SettingsPage';
import { SystemPage } from './pages/SystemPage';

export const App: React.FC = () => {
  const [currentPath, setCurrentPath] = useState<string>(window.location.pathname || '/');

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
    window.scrollTo(0, 0);
  };

  const renderContent = () => {
    if (currentPath === '/') {
      return <DashboardPage onNavigate={navigate} />;
    }
    if (currentPath === '/monitoring') {
      return <MonitoringPage />;
    }
    if (currentPath === '/detections') {
      return <DetectionsPage onNavigate={navigate} />;
    }
    if (currentPath.startsWith('/detections/')) {
      const id = currentPath.split('/')[2];
      return <DetectionDetailPage detectionId={id} onNavigate={navigate} />;
    }
    if (currentPath === '/alerts') {
      return <AlertsPage onNavigate={navigate} />;
    }
    if (currentPath === '/analytics') {
      return <AnalyticsPage />;
    }
    if (currentPath === '/settings') {
      return <SettingsPage />;
    }
    if (currentPath === '/system') {
      return <SystemPage />;
    }
    return <DashboardPage onNavigate={navigate} />;
  };

  return (
    <div className="app-layout">
      <Sidebar currentPath={currentPath} onNavigate={navigate} />
      <div className="main-content">
        <Navbar />
        {renderContent()}
      </div>
    </div>
  );
};

export default App;

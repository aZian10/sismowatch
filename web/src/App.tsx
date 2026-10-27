import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Reports } from './pages/Reports';
import { LiveEvents } from './pages/LiveEvents';
import { PipelineStatusView } from './pages/PipelineStatus';
import { AdminTools } from './pages/AdminTools';

const MainLayout: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [currentView, setCurrentView] = useState<string>('dashboard');

  if (isLoading) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#090d16',
        color: '#38bdf8',
        fontSize: '16px',
        fontWeight: 500
      }}>
        Initializing SismoWatch...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#090d16', color: '#f8fafc' }}>
      <Navbar currentView={currentView} onNavigate={(view) => setCurrentView(view)} />
      <main>
        {currentView === 'dashboard' && <Dashboard />}
        {currentView === 'reports' && <Reports />}
        {currentView === 'live' && <LiveEvents />}
        {currentView === 'pipeline' && <PipelineStatusView />}
        {currentView === 'admin' && <AdminTools />}
      </main>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainLayout />
    </AuthProvider>
  );
};

export default App;

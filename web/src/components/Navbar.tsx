import React from 'react';
import { useAuth } from '../context/AuthContext';

interface NavbarProps {
  currentView: string;
  onNavigate: (view: string) => void;
  streamConnected?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ currentView, onNavigate, streamConnected = false }) => {
  const { user, logout } = useAuth();
  const isAdmin = user?.role === 'admin';

  return (
    <header style={{
      backgroundColor: '#0c1322',
      borderBottom: '1px solid #1e293b',
      padding: '0 24px',
      height: '64px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 1000
    }}>
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }} onClick={() => onNavigate('dashboard')}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '8px',
          background: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 12px rgba(249, 115, 22, 0.4)'
        }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M2 12h5l3-8 4 16 3-8h5"/>
          </svg>
        </div>
        <div>
          <span style={{ fontSize: '18px', fontWeight: 700, letterSpacing: '-0.02em', color: '#f8fafc' }}>
            Sismo<span style={{ color: '#f97316' }}>Watch</span>
          </span>
          <span style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#64748b', display: 'block' }}>
            Global Seismic Intelligence
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={() => onNavigate('dashboard')}
          style={{
            background: currentView === 'dashboard' ? '#1e293b' : 'transparent',
            color: currentView === 'dashboard' ? '#38bdf8' : '#94a3b8',
            border: 'none',
            padding: '8px 14px',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
        >
          Dashboard
        </button>

        <button
          onClick={() => onNavigate('reports')}
          style={{
            background: currentView === 'reports' ? '#1e293b' : 'transparent',
            color: currentView === 'reports' ? '#38bdf8' : '#94a3b8',
            border: 'none',
            padding: '8px 14px',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
        >
          AI Reports
        </button>

        <button
          onClick={() => onNavigate('live')}
          style={{
            background: currentView === 'live' ? '#1e293b' : 'transparent',
            color: currentView === 'live' ? '#38bdf8' : '#94a3b8',
            border: 'none',
            padding: '8px 14px',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: 500,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            transition: 'all 0.15s ease'
          }}
        >
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: streamConnected ? '#10b981' : '#f59e0b',
            display: 'inline-block'
          }} />
          Live Feed
        </button>

        <button
          onClick={() => onNavigate('pipeline')}
          style={{
            background: currentView === 'pipeline' ? '#1e293b' : 'transparent',
            color: currentView === 'pipeline' ? '#38bdf8' : '#94a3b8',
            border: 'none',
            padding: '8px 14px',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
        >
          Pipeline Status
        </button>

        {/* Administrator Tools - Only rendered for admin role */}
        {isAdmin && (
          <button
            onClick={() => onNavigate('admin')}
            style={{
              background: currentView === 'admin' ? '#7f1d1d' : 'transparent',
              color: currentView === 'admin' ? '#fca5a5' : '#ef4444',
              border: '1px solid #7f1d1d',
              padding: '7px 14px',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            Admin Tools
          </button>
        )}
      </nav>

      {/* User and Logout */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc' }}>
            {user?.full_name || user?.username}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'flex-end' }}>
            <span style={{
              fontSize: '10px',
              textTransform: 'uppercase',
              fontWeight: 700,
              padding: '1px 6px',
              borderRadius: '4px',
              backgroundColor: isAdmin ? '#7f1d1d' : '#1e3a5f',
              color: isAdmin ? '#fecaca' : '#bfdbfe'
            }}>
              {user?.role}
            </span>
          </div>
        </div>

        <button
          onClick={logout}
          title="Sign out"
          style={{
            backgroundColor: '#1e293b',
            color: '#94a3b8',
            border: '1px solid #334155',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '13px',
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = '#f8fafc')}
          onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
        >
          Sign Out
        </button>
      </div>
    </header>
  );
};

import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { EarthquakeEvent } from '../types';

export const LiveEvents: React.FC = () => {
  const [liveEvents, setLiveEvents] = useState<any[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [lastHeartbeat, setLastHeartbeat] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    let eventSource: EventSource | null = null;
    let reconnectTimeout: any = null;

    const connectSSE = () => {
      setConnectionStatus('connecting');
      setErrorMsg(null);
      const url = api.getStreamUrl();

      eventSource = new EventSource(url);

      eventSource.onopen = () => {
        setConnectionStatus('connected');
      };

      eventSource.addEventListener('connect', (e: any) => {
        setConnectionStatus('connected');
        setLastHeartbeat(new Date().toLocaleTimeString());
      });

      eventSource.addEventListener('earthquake_update', (e: any) => {
        try {
          const data = JSON.parse(e.data);
          if (data.events && Array.isArray(data.events)) {
            setLiveEvents(prev => [...data.events, ...prev].slice(0, 50));
          }
          setLastHeartbeat(new Date().toLocaleTimeString());
        } catch (err) {
          console.error('Error parsing SSE event data:', err);
        }
      });

      eventSource.onerror = (e) => {
        setConnectionStatus('error');
        setErrorMsg('Live stream connection interrupted. Automatically attempting to reconnect...');
        eventSource?.close();
        reconnectTimeout = setTimeout(connectSSE, 4000);
      };
    };

    connectSSE();

    return () => {
      if (eventSource) eventSource.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, []);

  return (
    <div style={{ padding: '28px 32px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header & Status Indicator */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.02em', marginBottom: '4px' }}>
            Live Seismic Event Stream (SSE)
          </h1>
          <p style={{ fontSize: '13px', color: '#94a3b8' }}>
            Server-Sent Events connection streaming newly ingested and validated earthquakes directly into your browser
          </p>
        </div>

        {/* Live Status Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          backgroundColor: '#131b2e',
          border: '1px solid #23304c',
          borderRadius: '8px',
          padding: '8px 16px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: connectionStatus === 'connected' ? '#10b981' : (connectionStatus === 'connecting' ? '#f59e0b' : '#ef4444'),
              boxShadow: connectionStatus === 'connected' ? '0 0 10px #10b981' : 'none'
            }} />
            <span style={{
              fontSize: '12px',
              fontWeight: 700,
              textTransform: 'uppercase',
              color: connectionStatus === 'connected' ? '#10b981' : (connectionStatus === 'connecting' ? '#f59e0b' : '#ef4444')
            }}>
              {connectionStatus === 'connected' ? 'Live Connected' : (connectionStatus === 'connecting' ? 'Reconnecting...' : 'Connection Lost')}
            </span>
          </div>

          {lastHeartbeat && (
            <span style={{ fontSize: '11px', color: '#64748b', borderLeft: '1px solid #23304c', paddingLeft: '12px' }}>
              Ping: {lastHeartbeat}
            </span>
          )}
        </div>
      </div>

      {/* Reconnection Error Alert */}
      {errorMsg && (
        <div style={{ backgroundColor: '#451a03', border: '1px solid #b45309', color: '#fed7aa', padding: '12px 16px', borderRadius: '6px', marginBottom: '20px', fontSize: '13px' }}>
          {errorMsg}
        </div>
      )}

      {/* Stream Feed Table / Cards */}
      <div style={{
        backgroundColor: '#131b2e',
        border: '1px solid #23304c',
        borderRadius: '10px',
        overflow: 'hidden'
      }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #23304c', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc' }}>
            Live Stream Feed ({liveEvents.length} updates recorded this session)
          </span>
          <button
            onClick={() => setLiveEvents([])}
            style={{
              background: '#1e293b',
              border: '1px solid #334155',
              color: '#94a3b8',
              padding: '4px 10px',
              borderRadius: '4px',
              fontSize: '11px',
              cursor: 'pointer'
            }}
          >
            Clear Log
          </button>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ backgroundColor: '#0c1322', color: '#64748b', textAlign: 'left', borderBottom: '1px solid #23304c' }}>
                <th style={{ padding: '10px 16px' }}>Magnitude</th>
                <th style={{ padding: '10px 16px' }}>Location</th>
                <th style={{ padding: '10px 16px' }}>Depth</th>
                <th style={{ padding: '10px 16px' }}>Coordinates</th>
                <th style={{ padding: '10px 16px' }}>Event Time</th>
                <th style={{ padding: '10px 16px' }}>Stream Received</th>
              </tr>
            </thead>
            <tbody>
              {liveEvents.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: '48px', textAlign: 'center', color: '#64748b' }}>
                    <div style={{ marginBottom: '8px', fontSize: '15px', color: '#94a3b8' }}>
                      Listening to USGS live pipeline stream...
                    </div>
                    <div style={{ fontSize: '12px' }}>
                      New seismic events ingested every 5 minutes by Airflow will appear here in real time without refreshing.
                    </div>
                  </td>
                </tr>
              ) : (
                liveEvents.map((evt, idx) => (
                  <tr
                    key={evt.event_id || idx}
                    style={{
                      borderBottom: '1px solid #1a243c',
                      animation: 'fadeIn 0.4s ease'
                    }}
                  >
                    <td style={{ padding: '10px 16px', fontWeight: 700 }}>
                      <span style={{
                        color: evt.mag >= 6.0 ? '#ef4444' : (evt.mag >= 4.5 ? '#f97316' : (evt.mag >= 3.0 ? '#eab308' : '#10b981')),
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}>
                        M{Number(evt.mag).toFixed(1)}
                        {evt.tsunami > 0 && <span>🌊</span>}
                      </span>
                    </td>
                    <td style={{ padding: '10px 16px', color: '#f8fafc', fontWeight: 500 }}>
                      {evt.place}
                    </td>
                    <td style={{ padding: '10px 16px', color: '#94a3b8' }}>
                      {evt.depth_km ? `${Number(evt.depth_km).toFixed(1)} km` : '—'}
                    </td>
                    <td style={{ padding: '10px 16px', color: '#64748b', fontSize: '12px' }}>
                      {evt.latitude ? `${Number(evt.latitude).toFixed(2)}°, ${Number(evt.longitude).toFixed(2)}°` : '—'}
                    </td>
                    <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: '12px' }}>
                      {new Date(evt.event_time).toLocaleTimeString()}
                    </td>
                    <td style={{ padding: '10px 16px', color: '#38bdf8', fontSize: '12px', fontWeight: 600 }}>
                      {new Date(evt.last_synced_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

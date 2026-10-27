import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { KPIStats, EarthquakeEvent, TimeseriesStats } from '../types';
import { StatCard } from '../components/StatCard';
import { EventMap } from '../components/EventMap';
import { HourlyChart } from '../components/HourlyChart';
import { MagDistributionChart } from '../components/MagDistributionChart';
import { ActiveRegionsTable } from '../components/ActiveRegionsTable';

export const Dashboard: React.FC = () => {
  const [kpis, setKpis] = useState<KPIStats | null>(null);
  const [events, setEvents] = useState<EarthquakeEvent[]>([]);
  const [totalEvents, setTotalEvents] = useState(0);
  const [stats, setStats] = useState<TimeseriesStats | null>(null);

  // Filters
  const [minMag, setMinMag] = useState<number>(0);
  const [regionFilter, setRegionFilter] = useState<string>('');
  const [tsunamiOnly, setTsunamiOnly] = useState<boolean>(false);
  const [page, setPage] = useState<number>(0);
  const pageSize = 50;

  // Selected event for map focus
  const [selectedEvent, setSelectedEvent] = useState<EarthquakeEvent | null>(null);

  // UI state
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [kpiRes, statsRes, eventsRes] = await Promise.all([
        api.getKPIs(),
        api.getStats(24),
        api.getEvents({
          min_mag: minMag > 0 ? minMag : undefined,
          region: regionFilter.trim() || undefined,
          tsunami_only: tsunamiOnly,
          limit: pageSize,
          offset: page * pageSize
        })
      ]);
      setKpis(kpiRes);
      setStats(statsRes);
      setEvents(eventsRes.items);
      setTotalEvents(eventsRes.total);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve dashboard data from API.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [minMag, regionFilter, tsunamiOnly, page]);

  return (
    <div style={{ padding: '28px 32px', maxWidth: '1600px', margin: '0 auto' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.02em', marginBottom: '4px' }}>
            Operational Seismic Dashboard
          </h1>
          <p style={{ fontSize: '13px', color: '#94a3b8' }}>
            Near real-time USGS event ingestion, Pandera data quality enforcement, and automated analytics
          </p>
        </div>

        <button
          onClick={fetchData}
          disabled={isLoading}
          style={{
            backgroundColor: '#1e293b',
            color: '#38bdf8',
            border: '1px solid #334155',
            padding: '8px 16px',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: 600,
            cursor: isLoading ? 'not-allowed' : 'pointer'
          }}
        >
          {isLoading ? 'Refreshing...' : '↻ Refresh Data'}
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div style={{
          backgroundColor: '#450a0a',
          border: '1px solid #991b1b',
          color: '#fecaca',
          padding: '14px 18px',
          borderRadius: '8px',
          marginBottom: '24px',
          fontSize: '14px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>⚠ {error}</div>
          <button
            onClick={fetchData}
            style={{
              background: '#991b1b',
              border: 'none',
              color: '#fff',
              padding: '4px 10px',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Retry
          </button>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <StatCard
          title="24H TOTAL EVENTS"
          value={kpis ? kpis.total_events_24h : '—'}
          subtitle="Curated global events"
          valueColor="#f8fafc"
        />
        <StatCard
          title="MAX MAGNITUDE (24H)"
          value={kpis ? `M${kpis.max_magnitude_24h.toFixed(1)}` : '—'}
          subtitle="Highest peak intensity"
          valueColor={kpis && kpis.max_magnitude_24h >= 6.0 ? '#ef4444' : '#f97316'}
        />
        <StatCard
          title="MEAN MAGNITUDE (24H)"
          value={kpis ? `M${kpis.avg_magnitude_24h.toFixed(2)}` : '—'}
          subtitle="Tectonic baseline average"
          valueColor="#38bdf8"
        />
        <StatCard
          title="TSUNAMI ALERTS"
          value={kpis ? kpis.tsunami_events_24h : '—'}
          subtitle="Flagged events"
          valueColor={kpis && kpis.tsunami_events_24h > 0 ? '#ef4444' : '#10b981'}
        />
        <StatCard
          title="DATA QUALITY SCORE"
          value={kpis ? `${kpis.data_quality_score}%` : '—'}
          badge={kpis && kpis.data_quality_score >= 90 ? 'PASSED' : 'DEGRADED'}
          badgeColor={kpis && kpis.data_quality_score >= 90 ? '#10b981' : '#f59e0b'}
          subtitle="Validation acceptance rate"
        />
        <StatCard
          title="ACTIVE ANOMALIES"
          value={kpis ? kpis.active_anomalies_24h : '—'}
          subtitle="Z-Score deviations (24h)"
          valueColor={kpis && kpis.active_anomalies_24h > 0 ? '#f59e0b' : '#10b981'}
        />
      </div>

      {/* Map and Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', marginBottom: '24px' }}>
        {/* Interactive Map */}
        <div style={{
          backgroundColor: '#131b2e',
          border: '1px solid #23304c',
          borderRadius: '10px',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 600, color: '#f8fafc' }}>
              Global Seismicity Map
            </h2>
            <span style={{ fontSize: '12px', color: '#64748b' }}>
              Showing {events.length} filtered events
            </span>
          </div>
          <EventMap
            events={events}
            selectedEventId={selectedEvent?.event_id}
            onSelectEvent={(e) => setSelectedEvent(e)}
          />
        </div>

        {/* Magnitude Distribution & Active Regions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Magnitude Distribution */}
          <div style={{
            backgroundColor: '#131b2e',
            border: '1px solid #23304c',
            borderRadius: '10px',
            padding: '20px'
          }}>
            <h2 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc', marginBottom: '16px' }}>
              Magnitude Distribution (24H)
            </h2>
            {stats && <MagDistributionChart distribution={stats.magnitude_distribution} />}
          </div>

          {/* Top 5 Active Regions */}
          <div style={{
            backgroundColor: '#131b2e',
            border: '1px solid #23304c',
            borderRadius: '10px',
            padding: '20px',
            flex: 1
          }}>
            <h2 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc', marginBottom: '12px' }}>
              Most Active Regions
            </h2>
            {stats && (
              <ActiveRegionsTable
                regions={stats.top_regions}
                onSelectRegion={(reg) => {
                  setRegionFilter(reg);
                  setPage(0);
                }}
              />
            )}
          </div>
        </div>
      </div>

      {/* Hourly Trend Chart */}
      <div style={{
        backgroundColor: '#131b2e',
        border: '1px solid #23304c',
        borderRadius: '10px',
        padding: '20px',
        marginBottom: '24px'
      }}>
        <h2 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc', marginBottom: '16px' }}>
          Hourly Event Frequency & Intensity (Last 24 Hours)
        </h2>
        {stats && <HourlyChart data={stats.hourly} />}
      </div>

      {/* Filter Toolbar */}
      <div style={{
        backgroundColor: '#131b2e',
        border: '1px solid #23304c',
        borderRadius: '10px',
        padding: '16px 20px',
        marginBottom: '20px',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '16px',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>
            Min Magnitude:
          </label>
          <select
            value={minMag}
            onChange={(e) => {
              setMinMag(Number(e.target.value));
              setPage(0);
            }}
            style={{
              backgroundColor: '#0c1322',
              border: '1px solid #334155',
              color: '#f8fafc',
              padding: '6px 12px',
              borderRadius: '6px',
              fontSize: '13px',
              outline: 'none'
            }}
          >
            <option value={0}>All (M0.0+)</option>
            <option value={2.5}>M2.5+ (Felt quakes)</option>
            <option value={4.0}>M4.0+ (Moderate)</option>
            <option value={5.0}>M5.0+ (Significant)</option>
            <option value={6.0}>M6.0+ (Major)</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: '220px' }}>
          <label style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>
            Region Search:
          </label>
          <input
            type="text"
            value={regionFilter}
            onChange={(e) => {
              setRegionFilter(e.target.value);
              setPage(0);
            }}
            placeholder="Search place (e.g. California, Alaska, Japan)..."
            style={{
              flex: 1,
              backgroundColor: '#0c1322',
              border: '1px solid #334155',
              color: '#f8fafc',
              padding: '6px 12px',
              borderRadius: '6px',
              fontSize: '13px',
              outline: 'none'
            }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: '#f8fafc', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={tsunamiOnly}
              onChange={(e) => {
                setTsunamiOnly(e.target.checked);
                setPage(0);
              }}
              style={{ cursor: 'pointer' }}
            />
            Tsunami Warning Only
          </label>
        </div>

        {(minMag > 0 || regionFilter || tsunamiOnly) && (
          <button
            onClick={() => {
              setMinMag(0);
              setRegionFilter('');
              setTsunamiOnly(false);
              setPage(0);
            }}
            style={{
              backgroundColor: 'transparent',
              color: '#f87171',
              border: '1px solid #7f1d1d',
              padding: '6px 12px',
              borderRadius: '6px',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* Events Table */}
      <div style={{
        backgroundColor: '#131b2e',
        border: '1px solid #23304c',
        borderRadius: '10px',
        overflow: 'hidden'
      }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #23304c', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc' }}>
            Curated Earthquake Events ({totalEvents} total)
          </h2>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <button
              onClick={() => setPage(Math.max(page - 1, 0))}
              disabled={page === 0}
              style={{
                backgroundColor: '#1e293b',
                color: page === 0 ? '#475569' : '#f8fafc',
                border: '1px solid #334155',
                padding: '4px 10px',
                borderRadius: '4px',
                cursor: page === 0 ? 'not-allowed' : 'pointer',
                fontSize: '12px'
              }}
            >
              &larr; Prev
            </button>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>
              Page {page + 1} of {Math.max(Math.ceil(totalEvents / pageSize), 1)}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={(page + 1) * pageSize >= totalEvents}
              style={{
                backgroundColor: '#1e293b',
                color: (page + 1) * pageSize >= totalEvents ? '#475569' : '#f8fafc',
                border: '1px solid #334155',
                padding: '4px 10px',
                borderRadius: '4px',
                cursor: (page + 1) * pageSize >= totalEvents ? 'not-allowed' : 'pointer',
                fontSize: '12px'
              }}
            >
              Next &rarr;
            </button>
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ backgroundColor: '#0c1322', color: '#64748b', textAlign: 'left', borderBottom: '1px solid #23304c' }}>
                <th style={{ padding: '10px 16px' }}>Magnitude</th>
                <th style={{ padding: '10px 16px' }}>Location</th>
                <th style={{ padding: '10px 16px' }}>Depth</th>
                <th style={{ padding: '10px 16px' }}>Coordinates</th>
                <th style={{ padding: '10px 16px' }}>Event Time (UTC)</th>
                <th style={{ padding: '10px 16px' }}>Status</th>
                <th style={{ padding: '10px 16px' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {events.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: '36px', textAlign: 'center', color: '#64748b' }}>
                    {isLoading ? 'Loading events from curated database...' : 'No earthquake records match the specified filters.'}
                  </td>
                </tr>
              ) : (
                events.map((evt) => (
                  <tr
                    key={evt.event_id}
                    style={{
                      borderBottom: '1px solid #1a243c',
                      backgroundColor: selectedEvent?.event_id === evt.event_id ? '#1e293b' : 'transparent'
                    }}
                  >
                    <td style={{ padding: '10px 16px', fontWeight: 700 }}>
                      <span style={{
                        color: evt.mag >= 6.0 ? '#ef4444' : (evt.mag >= 4.5 ? '#f97316' : (evt.mag >= 3.0 ? '#eab308' : '#10b981')),
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}>
                        M{evt.mag.toFixed(1)}
                        {evt.tsunami > 0 && <span title="Tsunami Warning Flagged">🌊</span>}
                      </span>
                    </td>
                    <td style={{ padding: '10px 16px', color: '#f8fafc', fontWeight: 500 }}>
                      {evt.place}
                    </td>
                    <td style={{ padding: '10px 16px', color: '#94a3b8' }}>
                      {evt.depth_km.toFixed(1)} km
                    </td>
                    <td style={{ padding: '10px 16px', color: '#64748b', fontSize: '12px' }}>
                      {evt.latitude.toFixed(2)}°, {evt.longitude.toFixed(2)}°
                    </td>
                    <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: '12px' }}>
                      {new Date(evt.event_time).toUTCString()}
                    </td>
                    <td style={{ padding: '10px 16px' }}>
                      <span style={{
                        fontSize: '11px',
                        textTransform: 'uppercase',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        backgroundColor: evt.status === 'reviewed' ? '#064e3b' : '#312e81',
                        color: evt.status === 'reviewed' ? '#a7f3d0' : '#c7d2fe'
                      }}>
                        {evt.status}
                      </span>
                    </td>
                    <td style={{ padding: '10px 16px' }}>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                          onClick={() => setSelectedEvent(evt)}
                          style={{
                            background: '#1e293b',
                            border: '1px solid #334155',
                            color: '#38bdf8',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            fontSize: '11px',
                            cursor: 'pointer'
                          }}
                        >
                          Focus Map
                        </button>
                        {evt.url && (
                          <a
                            href={evt.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              color: '#94a3b8',
                              textDecoration: 'none',
                              fontSize: '11px',
                              padding: '3px 8px',
                              border: '1px solid #23304c',
                              borderRadius: '4px'
                            }}
                          >
                            USGS ↗
                          </a>
                        )}
                      </div>
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

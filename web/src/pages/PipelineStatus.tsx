import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { PipelineStatus } from '../types';
import { StatCard } from '../components/StatCard';

export const PipelineStatusView: React.FC = () => {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.getPipelineStatus();
      setStatus(res);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch pipeline status.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <div style={{ padding: '28px 32px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.02em', marginBottom: '4px' }}>
            Pipeline Health & Data Quality Status
          </h1>
          <p style={{ fontSize: '13px', color: '#94a3b8' }}>
            End-to-end Airflow execution telemetry, Pandera schema metrics, freshness, and anomaly detection
          </p>
        </div>

        <button
          onClick={fetchStatus}
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
          {isLoading ? 'Checking...' : '↻ Refresh Status'}
        </button>
      </div>

      {error && (
        <div style={{ backgroundColor: '#450a0a', border: '1px solid #991b1b', color: '#fecaca', padding: '12px 16px', borderRadius: '6px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {/* Headline KPI Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <StatCard
          title="CURATED EVENTS"
          value={status ? status.total_curated_events : '—'}
          subtitle="Validated, query-ready records"
          valueColor="#10b981"
        />
        <StatCard
          title="QUARANTINED EVENTS"
          value={status ? status.total_quarantined_events : '—'}
          subtitle="Isolated quality violations"
          valueColor={status && status.total_quarantined_events > 0 ? '#f59e0b' : '#64748b'}
        />
        <StatCard
          title="LATEST QUALITY SCORE"
          value={status ? `${status.latest_quality_score}%` : '—'}
          badge={status && status.latest_quality_score >= 90 ? 'HEALTHY' : 'WARNING'}
          badgeColor={status && status.latest_quality_score >= 90 ? '#10b981' : '#f59e0b'}
          subtitle="Passed / Evaluated ratio"
        />
        <StatCard
          title="DATA FRESHNESS"
          value={status?.data_freshness_seconds ? `${Math.round(status.data_freshness_seconds / 60)} min` : 'Active'}
          subtitle="Lag from USGS publication"
          valueColor="#38bdf8"
        />
      </div>

      {/* DAGs Architecture Overview Card */}
      <div style={{
        backgroundColor: '#131b2e',
        border: '1px solid #23304c',
        borderRadius: '10px',
        padding: '20px',
        marginBottom: '24px'
      }}>
        <h2 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc', marginBottom: '16px' }}>
          Airflow DAG Orchestration Registry
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          <div style={{ background: '#0c1322', padding: '16px', borderRadius: '8px', border: '1px solid #1e293b' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontWeight: 600, color: '#f8fafc', fontSize: '13px' }}>sismowatch_ingestion_dag</span>
              <span style={{ fontSize: '11px', color: '#10b981', fontWeight: 700 }}>ACTIVE (*/5)</span>
            </div>
            <p style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.4 }}>
              Queries USGS 1-hour GeoJSON, saves raw payload into raw.usgs_feed for complete auditability.
            </p>
          </div>

          <div style={{ background: '#0c1322', padding: '16px', borderRadius: '8px', border: '1px solid #1e293b' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontWeight: 600, color: '#f8fafc', fontSize: '13px' }}>sismowatch_transformation_dag</span>
              <span style={{ fontSize: '11px', color: '#38bdf8', fontWeight: 700 }}>TRIGGERED</span>
            </div>
            <p style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.4 }}>
              Normalizes staging, executes Pandera quality rules, isolates quarantine, upserts curated, and tests anomalies.
            </p>
          </div>

          <div style={{ background: '#0c1322', padding: '16px', borderRadius: '8px', border: '1px solid #1e293b' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontWeight: 600, color: '#f8fafc', fontSize: '13px' }}>sismowatch_daily_report_dag</span>
              <span style={{ fontSize: '11px', color: '#a855f7', fontWeight: 700 }}>DAILY (01:00 UTC)</span>
            </div>
            <p style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.4 }}>
              Calculates SQL stats, invokes structured LLM or deterministic fallback, and generates executive report.
            </p>
          </div>

          <div style={{ background: '#0c1322', padding: '16px', borderRadius: '8px', border: '1px solid #1e293b' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontWeight: 600, color: '#f8fafc', fontSize: '13px' }}>sismowatch_backfill_dag</span>
              <span style={{ fontSize: '11px', color: '#f97316', fontWeight: 700 }}>ADMIN ON-DEMAND</span>
            </div>
            <p style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.4 }}>
              Parameterized 30-day historical query endpoint backfill with idempotent curated upserts.
            </p>
          </div>
        </div>
      </div>

      {/* Recent Quality Execution Batches */}
      <div style={{
        backgroundColor: '#131b2e',
        border: '1px solid #23304c',
        borderRadius: '10px',
        overflow: 'hidden',
        marginBottom: '24px'
      }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #23304c' }}>
          <h2 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc' }}>
            Data Quality Audit History (curated.quality_metrics)
          </h2>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ backgroundColor: '#0c1322', color: '#64748b', textAlign: 'left', borderBottom: '1px solid #23304c' }}>
                <th style={{ padding: '10px 16px' }}>Batch Identifier</th>
                <th style={{ padding: '10px 16px' }}>Evaluated</th>
                <th style={{ padding: '10px 16px' }}>Passed (Curated)</th>
                <th style={{ padding: '10px 16px' }}>Rejected (Quarantine)</th>
                <th style={{ padding: '10px 16px' }}>Quality Score</th>
                <th style={{ padding: '10px 16px' }}>Freshness Lag</th>
                <th style={{ padding: '10px 16px' }}>Executed At</th>
              </tr>
            </thead>
            <tbody>
              {!status?.recent_batches || status.recent_batches.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
                    No quality batches recorded yet.
                  </td>
                </tr>
              ) : (
                status.recent_batches.map((b) => (
                  <tr key={b.batch_id} style={{ borderBottom: '1px solid #1a243c' }}>
                    <td style={{ padding: '10px 16px', fontFamily: 'monospace', color: '#f8fafc' }}>
                      {b.batch_id}
                    </td>
                    <td style={{ padding: '10px 16px', color: '#94a3b8' }}>
                      {b.evaluated_records}
                    </td>
                    <td style={{ padding: '10px 16px', color: '#10b981', fontWeight: 600 }}>
                      {b.passed_records}
                    </td>
                    <td style={{ padding: '10px 16px', color: b.rejected_records > 0 ? '#f59e0b' : '#64748b' }}>
                      {b.rejected_records}
                    </td>
                    <td style={{ padding: '10px 16px', fontWeight: 700, color: b.quality_score >= 90 ? '#10b981' : '#f59e0b' }}>
                      {b.quality_score.toFixed(1)}%
                    </td>
                    <td style={{ padding: '10px 16px', color: '#94a3b8' }}>
                      {b.freshness_seconds ? `${Math.round(b.freshness_seconds / 60)} min` : 'Live'}
                    </td>
                    <td style={{ padding: '10px 16px', color: '#64748b', fontSize: '12px' }}>
                      {new Date(b.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Anomaly Alerts */}
      <div style={{
        backgroundColor: '#131b2e',
        border: '1px solid #23304c',
        borderRadius: '10px',
        overflow: 'hidden'
      }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #23304c' }}>
          <h2 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc' }}>
            Statistical Anomaly Alerts (curated.anomaly_alerts)
          </h2>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ backgroundColor: '#0c1322', color: '#64748b', textAlign: 'left', borderBottom: '1px solid #23304c' }}>
                <th style={{ padding: '10px 16px' }}>Timestamp</th>
                <th style={{ padding: '10px 16px' }}>Metric</th>
                <th style={{ padding: '10px 16px' }}>Observed</th>
                <th style={{ padding: '10px 16px' }}>Z-Score</th>
                <th style={{ padding: '10px 16px' }}>Severity</th>
                <th style={{ padding: '10px 16px' }}>Explanation</th>
              </tr>
            </thead>
            <tbody>
              {!status?.recent_anomalies || status.recent_anomalies.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
                    No statistical deviations detected in the rolling baseline.
                  </td>
                </tr>
              ) : (
                status.recent_anomalies.map((a) => (
                  <tr key={a.id} style={{ borderBottom: '1px solid #1a243c' }}>
                    <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: '12px' }}>
                      {new Date(a.alert_time).toLocaleString()}
                    </td>
                    <td style={{ padding: '10px 16px', color: '#f8fafc', fontWeight: 500 }}>
                      {a.metric_name}
                    </td>
                    <td style={{ padding: '10px 16px', color: '#38bdf8' }}>
                      {a.current_value.toFixed(2)}
                    </td>
                    <td style={{ padding: '10px 16px', color: '#f97316', fontWeight: 600 }}>
                      z={a.z_score.toFixed(2)}
                    </td>
                    <td style={{ padding: '10px 16px' }}>
                      <span style={{
                        fontSize: '11px',
                        textTransform: 'uppercase',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        backgroundColor: a.severity === 'critical' ? '#7f1d1d' : '#451a03',
                        color: a.severity === 'critical' ? '#fca5a5' : '#fed7aa'
                      }}>
                        {a.severity}
                      </span>
                    </td>
                    <td style={{ padding: '10px 16px', color: '#cbd5e1', fontSize: '12px' }}>
                      {a.explanation}
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

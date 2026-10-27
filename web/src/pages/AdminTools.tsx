import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { QuarantineRecord } from '../types';

export const AdminTools: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  // Quarantine State
  const [quarantineRecords, setQuarantineRecords] = useState<QuarantineRecord[]>([]);
  const [totalQuarantine, setTotalQuarantine] = useState(0);
  const [selectedRawRecord, setSelectedRawRecord] = useState<any | null>(null);
  const [isQuarantineLoading, setIsQuarantineLoading] = useState(false);

  // Backfill State
  const [startBackfillDate, setStartBackfillDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 14);
    return d.toISOString().split('T')[0];
  });
  const [endBackfillDate, setEndBackfillDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [minBackfillMag, setMinBackfillMag] = useState<number>(3.0);
  const [isBackfilling, setIsBackfilling] = useState(false);
  const [backfillResult, setBackfillResult] = useState<any | null>(null);

  // Report Regeneration State
  const [reportTargetDate, setReportTargetDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 1);
    return d.toISOString().split('T')[0];
  });
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [regenerateResult, setRegenerateResult] = useState<any | null>(null);

  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchQuarantine = async () => {
    if (!isAdmin) return;
    setIsQuarantineLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.getQuarantine(50, 0);
      setQuarantineRecords(res.items);
      setTotalQuarantine(res.total);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load quarantine records.');
    } finally {
      setIsQuarantineLoading(false);
    }
  };

  useEffect(() => {
    if (isAdmin) {
      fetchQuarantine();
    }
  }, [isAdmin]);

  const handleRunBackfill = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsBackfilling(true);
    setErrorMsg(null);
    setBackfillResult(null);
    try {
      const res = await api.triggerBackfill({
        starttime: startBackfillDate,
        endtime: endBackfillDate,
        minmagnitude: minBackfillMag
      });
      setBackfillResult(res);
      fetchQuarantine();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to execute backfill.');
    } finally {
      setIsBackfilling(false);
    }
  };

  const handleRegenerateReport = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsRegenerating(true);
    setErrorMsg(null);
    setRegenerateResult(null);
    try {
      const res = await api.regenerateReport(reportTargetDate);
      setRegenerateResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Report regeneration failed.');
    } finally {
      setIsRegenerating(false);
    }
  };

  // If user is not admin, deny access immediately
  if (!isAdmin) {
    return (
      <div style={{ padding: '64px', textAlign: 'center', maxWidth: '600px', margin: '0 auto' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🚫</div>
        <h1 style={{ fontSize: '22px', fontWeight: 700, color: '#ef4444', marginBottom: '12px' }}>
          403 — Administrative Access Forbidden
        </h1>
        <p style={{ fontSize: '14px', color: '#94a3b8', lineHeight: 1.6 }}>
          Your current account role (<strong>viewer</strong>) lacks authorization to access quarantine management,
          historical backfill, or report regeneration tools.
        </p>
      </div>
    );
  }

  return (
    <div style={{ padding: '28px 32px', maxWidth: '1600px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            Administrator Quality & Orchestration Controls
          </h1>
          <span style={{
            fontSize: '11px',
            fontWeight: 700,
            padding: '2px 8px',
            borderRadius: '4px',
            backgroundColor: '#7f1d1d',
            color: '#fecaca',
            textTransform: 'uppercase'
          }}>
            Admin Authorized
          </span>
        </div>
        <p style={{ fontSize: '13px', color: '#94a3b8' }}>
          Inspect quarantined validation failures, execute historical USGS backfills, and trigger AI report re-runs
        </p>
      </div>

      {errorMsg && (
        <div style={{ backgroundColor: '#450a0a', border: '1px solid #991b1b', color: '#fecaca', padding: '14px 18px', borderRadius: '8px', marginBottom: '24px', fontSize: '13px' }}>
          ⚠ {errorMsg}
        </div>
      )}

      {/* Grid: Backfill & Report Regeneration Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
        {/* Card 1: Historical Backfill */}
        <div style={{
          backgroundColor: '#131b2e',
          border: '1px solid #23304c',
          borderRadius: '10px',
          padding: '24px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <span style={{ fontSize: '18px' }}>⚡</span>
            <h2 style={{ fontSize: '16px', fontWeight: 600, color: '#f8fafc' }}>
              USGS Historical Catalog Backfill
            </h2>
          </div>
          <p style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '18px', lineHeight: 1.5 }}>
            Fetches past earthquake events from USGS FDSNWS query endpoint, runs them through the Pandera quality validation pipeline, and idempotently upserts to curated.
          </p>

          <form onSubmit={handleRunBackfill} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#cbd5e1', marginBottom: '4px' }}>
                  Start Date
                </label>
                <input
                  type="date"
                  value={startBackfillDate}
                  onChange={(e) => setStartBackfillDate(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    backgroundColor: '#0c1322',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    color: '#f8fafc',
                    fontSize: '13px'
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#cbd5e1', marginBottom: '4px' }}>
                  End Date
                </label>
                <input
                  type="date"
                  value={endBackfillDate}
                  onChange={(e) => setEndBackfillDate(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    backgroundColor: '#0c1322',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    color: '#f8fafc',
                    fontSize: '13px'
                  }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#cbd5e1', marginBottom: '4px' }}>
                Minimum Magnitude Filter: M{minBackfillMag.toFixed(1)}
              </label>
              <input
                type="range"
                min="1.0"
                max="6.0"
                step="0.5"
                value={minBackfillMag}
                onChange={(e) => setMinBackfillMag(parseFloat(e.target.value))}
                style={{ width: '100%' }}
              />
            </div>

            <button
              type="submit"
              disabled={isBackfilling}
              style={{
                backgroundColor: '#f97316',
                color: '#ffffff',
                border: 'none',
                padding: '10px',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: 600,
                cursor: isBackfilling ? 'not-allowed' : 'pointer',
                opacity: isBackfilling ? 0.7 : 1
              }}
            >
              {isBackfilling ? 'Executing Backfill Pipeline...' : 'Run Historical Backfill'}
            </button>
          </form>

          {backfillResult && (
            <div style={{ marginTop: '16px', padding: '12px', borderRadius: '6px', backgroundColor: '#064e3b', color: '#a7f3d0', fontSize: '12px', border: '1px solid #047857' }}>
              <strong>Backfill Complete:</strong> {backfillResult.message}<br />
              Evaluated: {backfillResult.evaluated} | Passed: {backfillResult.passed} | Quarantined: {backfillResult.quarantined} | Quality Score: {backfillResult.quality_score}%
            </div>
          )}
        </div>

        {/* Card 2: AI Report Regeneration */}
        <div style={{
          backgroundColor: '#131b2e',
          border: '1px solid #23304c',
          borderRadius: '10px',
          padding: '24px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <span style={{ fontSize: '18px' }}>🤖</span>
            <h2 style={{ fontSize: '16px', fontWeight: 600, color: '#f8fafc' }}>
              Regenerate Daily AI Seismic Report
            </h2>
          </div>
          <p style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '18px', lineHeight: 1.5 }}>
            Recalculates verified ground-truth figures for any historical date, invokes the LLM with structured output validation (or deterministic engine), and updates curated.daily_reports.
          </p>

          <form onSubmit={handleRegenerateReport} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#cbd5e1', marginBottom: '4px' }}>
                Report Target Date
              </label>
              <input
                type="date"
                value={reportTargetDate}
                onChange={(e) => setReportTargetDate(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  backgroundColor: '#0c1322',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  color: '#f8fafc',
                  fontSize: '13px'
                }}
              />
            </div>

            <button
              type="submit"
              disabled={isRegenerating}
              style={{
                marginTop: '34px',
                backgroundColor: '#38bdf8',
                color: '#0f172a',
                border: 'none',
                padding: '10px',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: 600,
                cursor: isRegenerating ? 'not-allowed' : 'pointer',
                opacity: isRegenerating ? 0.7 : 1
              }}
            >
              {isRegenerating ? 'Generating AI Report...' : 'Regenerate Report for Date'}
            </button>
          </form>

          {regenerateResult && (
            <div style={{ marginTop: '16px', padding: '12px', borderRadius: '6px', backgroundColor: '#064e3b', color: '#a7f3d0', fontSize: '12px', border: '1px solid #047857' }}>
              <strong>Report Generated:</strong> {regenerateResult.title} (Engine: {regenerateResult.provider}, Fallback: {String(regenerateResult.is_fallback)})
            </div>
          )}
        </div>
      </div>

      {/* Quarantine Records Audit Table */}
      <div style={{
        backgroundColor: '#131b2e',
        border: '1px solid #23304c',
        borderRadius: '10px',
        overflow: 'hidden'
      }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #23304c', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc' }}>
              Quarantined Records Quality Log (curated.quarantine)
            </h2>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>
              {totalQuarantine} records blocked from reaching curated due to quality rule violations
            </span>
          </div>

          <button
            onClick={fetchQuarantine}
            disabled={isQuarantineLoading}
            style={{
              background: '#1e293b',
              border: '1px solid #334155',
              color: '#38bdf8',
              padding: '6px 12px',
              borderRadius: '6px',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            {isQuarantineLoading ? 'Refreshing...' : '↻ Refresh Quarantine'}
          </button>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ backgroundColor: '#0c1322', color: '#64748b', textAlign: 'left', borderBottom: '1px solid #23304c' }}>
                <th style={{ padding: '10px 16px' }}>Event ID</th>
                <th style={{ padding: '10px 16px' }}>Batch</th>
                <th style={{ padding: '10px 16px' }}>Failed Rules</th>
                <th style={{ padding: '10px 16px' }}>Rejection Reasons</th>
                <th style={{ padding: '10px 16px' }}>Quarantined At</th>
                <th style={{ padding: '10px 16px' }}>Raw Payload</th>
              </tr>
            </thead>
            <tbody>
              {quarantineRecords.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: '36px', textAlign: 'center', color: '#64748b' }}>
                    {isQuarantineLoading ? 'Loading quarantine data...' : 'Zero quarantined records. Data quality is currently 100% compliant.'}
                  </td>
                </tr>
              ) : (
                quarantineRecords.map((q) => (
                  <tr key={q.id} style={{ borderBottom: '1px solid #1a243c' }}>
                    <td style={{ padding: '10px 16px', fontFamily: 'monospace', color: '#f8fafc', fontWeight: 600 }}>
                      {q.event_id || '<missing_id>'}
                    </td>
                    <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: '12px' }}>
                      {q.batch_id}
                    </td>
                    <td style={{ padding: '10px 16px' }}>
                      <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                        {q.failed_rules.map((rule, idx) => (
                          <span
                            key={idx}
                            style={{
                              fontSize: '10px',
                              backgroundColor: '#450a0a',
                              color: '#fca5a5',
                              padding: '2px 6px',
                              borderRadius: '4px',
                              fontWeight: 700
                            }}
                          >
                            {rule}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td style={{ padding: '10px 16px', color: '#fed7aa', fontSize: '12px' }}>
                      {q.rejection_reasons.join('; ')}
                    </td>
                    <td style={{ padding: '10px 16px', color: '#94a3b8', fontSize: '12px' }}>
                      {new Date(q.quarantined_at).toLocaleString()}
                    </td>
                    <td style={{ padding: '10px 16px' }}>
                      <button
                        onClick={() => setSelectedRawRecord(q.raw_record)}
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
                        Inspect JSON
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Raw Payload Modal */}
      {selectedRawRecord && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000,
          padding: '20px'
        }}>
          <div style={{
            backgroundColor: '#131b2e',
            border: '1px solid #23304c',
            borderRadius: '10px',
            width: '100%',
            maxWidth: '700px',
            maxHeight: '80vh',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
          }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #23304c', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc' }}>
                Raw Rejected Payload Inspection
              </span>
              <button
                onClick={() => setSelectedRawRecord(null)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '18px', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>
            <pre style={{
              padding: '20px',
              overflowY: 'auto',
              flex: 1,
              backgroundColor: '#090d16',
              color: '#38bdf8',
              fontSize: '12px',
              fontFamily: 'monospace'
            }}>
              {JSON.stringify(selectedRawRecord, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

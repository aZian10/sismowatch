import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { DailyReport } from '../types';

export const Reports: React.FC = () => {
  const [reports, setReports] = useState<DailyReport[]>([]);
  const [total, setTotal] = useState(0);
  const [selectedReport, setSelectedReport] = useState<DailyReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const pageSize = 15;

  const fetchReports = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.getReports(pageSize, page * pageSize);
      setReports(res.items);
      setTotal(res.total);
      if (res.items.length > 0 && !selectedReport) {
        setSelectedReport(res.items[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load historical AI reports.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [page]);

  return (
    <div style={{ padding: '28px 32px', maxWidth: '1600px', margin: '0 auto' }}>
      {/* Header & Export Toolbar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.02em', marginBottom: '4px' }}>
            Daily AI Seismic Intelligence Reports
          </h1>
          <p style={{ fontSize: '13px', color: '#94a3b8' }}>
            Automated narrative summaries validated with Pydantic structured schemas and ground-truth figures
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <a
            href={api.getExportUrl('csv')}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              backgroundColor: '#1e293b',
              color: '#38bdf8',
              border: '1px solid #334155',
              padding: '8px 16px',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 600,
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <span>📥 Export CSV</span>
          </a>

          <a
            href={api.getExportUrl('html')}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              backgroundColor: '#1e293b',
              color: '#f8fafc',
              border: '1px solid #334155',
              padding: '8px 16px',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 600,
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <span>🖨 Print / Export HTML</span>
          </a>
        </div>
      </div>

      {error && (
        <div style={{ backgroundColor: '#450a0a', border: '1px solid #991b1b', color: '#fecaca', padding: '12px 16px', borderRadius: '6px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {/* Main 2-column layout: Report List & Report Viewer */}
      <div style={{ display: 'grid', gridTemplateColumns: '400px 1fr', gap: '24px' }}>
        {/* Left: Report list */}
        <div style={{
          backgroundColor: '#131b2e',
          border: '1px solid #23304c',
          borderRadius: '10px',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          maxHeight: '750px'
        }}>
          <div style={{ padding: '16px', borderBottom: '1px solid #23304c', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc' }}>
              Historical Catalog ({total})
            </span>
            <div style={{ display: 'flex', gap: '6px' }}>
              <button
                onClick={() => setPage(Math.max(page - 1, 0))}
                disabled={page === 0}
                style={{
                  background: '#1e293b',
                  color: page === 0 ? '#475569' : '#cbd5e1',
                  border: '1px solid #334155',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  cursor: page === 0 ? 'not-allowed' : 'pointer',
                  fontSize: '11px'
                }}
              >
                &larr;
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={(page + 1) * pageSize >= total}
                style={{
                  background: '#1e293b',
                  color: (page + 1) * pageSize >= total ? '#475569' : '#cbd5e1',
                  border: '1px solid #334155',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  cursor: (page + 1) * pageSize >= total ? 'not-allowed' : 'pointer',
                  fontSize: '11px'
                }}
              >
                &rarr;
              </button>
            </div>
          </div>

          <div style={{ overflowY: 'auto', flex: 1 }}>
            {reports.length === 0 ? (
              <div style={{ padding: '32px', textAlign: 'center', color: '#64748b', fontSize: '13px' }}>
                {isLoading ? 'Loading reports...' : 'No historical reports generated yet.'}
              </div>
            ) : (
              reports.map((rep) => {
                const isSelected = selectedReport?.id === rep.id;
                return (
                  <div
                    key={rep.id}
                    onClick={() => setSelectedReport(rep)}
                    style={{
                      padding: '14px 16px',
                      borderBottom: '1px solid #1a243c',
                      backgroundColor: isSelected ? '#1e293b' : 'transparent',
                      cursor: 'pointer',
                      transition: 'background 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span style={{ fontSize: '13px', fontWeight: 600, color: isSelected ? '#38bdf8' : '#f8fafc' }}>
                        {rep.report_date}
                      </span>
                      <span style={{
                        fontSize: '10px',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        backgroundColor: rep.is_fallback ? '#451a03' : '#064e3b',
                        color: rep.is_fallback ? '#fed7aa' : '#a7f3d0'
                      }}>
                        {rep.is_fallback ? 'DETERMINISTIC' : 'LLM VERIFIED'}
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.4, overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                      {rep.executive_summary}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right: Selected Report Details */}
        <div style={{
          backgroundColor: '#131b2e',
          border: '1px solid #23304c',
          borderRadius: '10px',
          padding: '28px',
          minHeight: '600px'
        }}>
          {selectedReport ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
                <div>
                  <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc', marginBottom: '6px' }}>
                    {selectedReport.title}
                  </h2>
                  <div style={{ fontSize: '13px', color: '#94a3b8' }}>
                    Target Date: <strong style={{ color: '#f8fafc' }}>{selectedReport.report_date}</strong> &bull; Generated: {new Date(selectedReport.created_at).toLocaleString()}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '11px', textTransform: 'uppercase', color: '#64748b', fontWeight: 600 }}>
                    Engine & Model
                  </div>
                  <div style={{ fontSize: '13px', color: '#38bdf8', fontWeight: 600 }}>
                    {selectedReport.provider} / {selectedReport.model}
                  </div>
                  {selectedReport.latency_ms && (
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                      Execution time: {selectedReport.latency_ms} ms
                    </div>
                  )}
                </div>
              </div>

              {/* Executive Summary Card */}
              <div style={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                padding: '18px',
                marginBottom: '24px'
              }}>
                <div style={{ fontSize: '11px', textTransform: 'uppercase', color: '#f97316', fontWeight: 700, letterSpacing: '0.05em', marginBottom: '8px' }}>
                  Executive Synthesis
                </div>
                <p style={{ fontSize: '14px', color: '#f8fafc', lineHeight: 1.6 }}>
                  {selectedReport.executive_summary}
                </p>
              </div>

              {/* Ground Truth Stats Snapshot */}
              {selectedReport.stats_json && (
                <div style={{ marginBottom: '24px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '10px' }}>
                    Verified Input Measurements
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
                    <div style={{ background: '#0c1322', padding: '12px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                      <div style={{ fontSize: '11px', color: '#64748b' }}>Events Count</div>
                      <div style={{ fontSize: '18px', fontWeight: 700, color: '#f8fafc' }}>
                        {selectedReport.stats_json.total_events ?? '—'}
                      </div>
                    </div>
                    <div style={{ background: '#0c1322', padding: '12px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                      <div style={{ fontSize: '11px', color: '#64748b' }}>Peak Magnitude</div>
                      <div style={{ fontSize: '18px', fontWeight: 700, color: '#f97316' }}>
                        M{selectedReport.stats_json.max_magnitude ?? '—'}
                      </div>
                    </div>
                    <div style={{ background: '#0c1322', padding: '12px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                      <div style={{ fontSize: '11px', color: '#64748b' }}>Mean Magnitude</div>
                      <div style={{ fontSize: '18px', fontWeight: 700, color: '#38bdf8' }}>
                        M{selectedReport.stats_json.avg_magnitude ? Number(selectedReport.stats_json.avg_magnitude).toFixed(2) : '—'}
                      </div>
                    </div>
                    <div style={{ background: '#0c1322', padding: '12px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                      <div style={{ fontSize: '11px', color: '#64748b' }}>Tsunami Flags</div>
                      <div style={{ fontSize: '18px', fontWeight: 700, color: selectedReport.stats_json.tsunami_count > 0 ? '#ef4444' : '#10b981' }}>
                        {selectedReport.stats_json.tsunami_count ?? 0}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Detailed Narrative */}
              <div>
                <div style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '10px' }}>
                  Complete Narrative & Technical Analysis
                </div>
                <div style={{
                  fontSize: '14px',
                  color: '#cbd5e1',
                  lineHeight: 1.8,
                  whiteSpace: 'pre-line',
                  backgroundColor: '#0c1322',
                  padding: '20px',
                  borderRadius: '8px',
                  border: '1px solid #1e293b'
                }}>
                  {selectedReport.narrative_report}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b' }}>
              Select a report from the historical catalog to read.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

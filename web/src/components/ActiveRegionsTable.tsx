import React from 'react';
import { RegionCount } from '../types';

interface ActiveRegionsTableProps {
  regions: RegionCount[];
  onSelectRegion?: (region: string) => void;
}

export const ActiveRegionsTable: React.FC<ActiveRegionsTableProps> = ({ regions, onSelectRegion }) => {
  if (!regions || regions.length === 0) {
    return <div style={{ color: '#64748b', fontSize: '13px' }}>No regional activity recorded.</div>;
  }

  return (
    <div style={{ width: '100%', overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid #23304c', color: '#64748b', textAlign: 'left' }}>
            <th style={{ padding: '8px 12px', fontWeight: 600 }}>Region</th>
            <th style={{ padding: '8px 12px', fontWeight: 600, textAlign: 'right' }}>Events</th>
            <th style={{ padding: '8px 12px', fontWeight: 600, textAlign: 'right' }}>Avg Mag</th>
          </tr>
        </thead>
        <tbody>
          {regions.map((reg, idx) => (
            <tr
              key={idx}
              onClick={() => onSelectRegion && onSelectRegion(reg.region)}
              style={{
                borderBottom: '1px solid #1a243c',
                cursor: onSelectRegion ? 'pointer' : 'default',
                transition: 'background 0.15s ease'
              }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#1e293b')}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
            >
              <td style={{ padding: '10px 12px', color: '#f8fafc', fontWeight: 500 }}>
                {reg.region}
              </td>
              <td style={{ padding: '10px 12px', textAlign: 'right', color: '#38bdf8', fontWeight: 600 }}>
                {reg.count}
              </td>
              <td style={{ padding: '10px 12px', textAlign: 'right', color: reg.avg_mag >= 4.5 ? '#f97316' : '#94a3b8' }}>
                M{reg.avg_mag.toFixed(2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

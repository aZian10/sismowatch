import React from 'react';
import { HourlyBucket } from '../types';

interface HourlyChartProps {
  data: HourlyBucket[];
}

export const HourlyChart: React.FC<HourlyChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div style={{
        height: '240px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#64748b',
        fontSize: '13px'
      }}>
        No hourly data points recorded in this window.
      </div>
    );
  }

  const maxCount = Math.max(...data.map(d => d.count), 5);
  const chartHeight = 180;
  const barWidth = 100 / data.length;

  return (
    <div style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '11px', color: '#64748b' }}>
        <span>Peak Volume: {maxCount} events/hr</span>
        <span>Average Magnitude Overlay</span>
      </div>

      <div style={{ height: `${chartHeight}px`, display: 'flex', alignItems: 'flex-end', gap: '3px', position: 'relative', borderBottom: '1px solid #23304c' }}>
        {data.map((item, idx) => {
          const heightPercent = (item.count / maxCount) * 100;
          const label = item.hour.split('T')[1]?.substring(0, 5) || '';

          return (
            <div
              key={idx}
              title={`Hour ${item.hour}: ${item.count} events (avg M${item.avg_mag.toFixed(2)})`}
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                height: '100%',
                justifyContent: 'flex-end',
                cursor: 'pointer'
              }}
            >
              <div
                style={{
                  width: '80%',
                  height: `${Math.max(heightPercent, 3)}%`,
                  backgroundColor: item.avg_mag >= 4.5 ? '#f97316' : '#38bdf8',
                  borderRadius: '3px 3px 0 0',
                  transition: 'height 0.3s ease',
                  opacity: 0.85
                }}
                onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
                onMouseLeave={(e) => (e.currentTarget.style.opacity = '0.85')}
              />
            </div>
          );
        })}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '10px', color: '#64748b' }}>
        <span>{data[0]?.hour.split('T')[1]?.substring(0, 5) || '00:00'}</span>
        <span>{data[Math.floor(data.length / 2)]?.hour.split('T')[1]?.substring(0, 5) || '12:00'}</span>
        <span>{data[data.length - 1]?.hour.split('T')[1]?.substring(0, 5) || '23:00'}</span>
      </div>
    </div>
  );
};

import React from 'react';
import { MagBucket } from '../types';

interface MagDistributionChartProps {
  distribution: MagBucket[];
}

export const MagDistributionChart: React.FC<MagDistributionChartProps> = ({ distribution }) => {
  const total = distribution.reduce((acc, curr) => acc + curr.count, 0);

  const getBucketColor = (bucket: string) => {
    if (bucket.includes('< 2.0')) return '#10b981';
    if (bucket.includes('2.0 - 3.9')) return '#eab308';
    if (bucket.includes('4.0 - 5.9')) return '#f97316';
    return '#ef4444';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {distribution.map((item, idx) => {
        const percentage = total > 0 ? (item.count / total) * 100 : 0;
        const color = getBucketColor(item.bucket);

        return (
          <div key={idx}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
              <span style={{ color: '#cbd5e1', fontWeight: 500 }}>{item.bucket}</span>
              <span style={{ color: '#94a3b8' }}>
                {item.count} ({percentage.toFixed(1)}%)
              </span>
            </div>
            <div style={{
              width: '100%',
              height: '6px',
              backgroundColor: '#1e293b',
              borderRadius: '3px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${percentage}%`,
                height: '100%',
                backgroundColor: color,
                borderRadius: '3px',
                transition: 'width 0.4s ease'
              }} />
            </div>
          </div>
        );
      })}
    </div>
  );
};

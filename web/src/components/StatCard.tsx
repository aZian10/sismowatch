import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  badge?: string;
  badgeColor?: string;
  valueColor?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  badge,
  badgeColor = '#38bdf8',
  valueColor = '#f8fafc'
}) => {
  return (
    <div style={{
      backgroundColor: '#131b2e',
      border: '1px solid #23304c',
      borderRadius: '10px',
      padding: '20px',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.25)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <span style={{ fontSize: '13px', fontWeight: 500, color: '#94a3b8', letterSpacing: '0.02em' }}>
          {title}
        </span>
        {icon && (
          <div style={{ color: '#64748b', display: 'flex', alignItems: 'center' }}>
            {icon}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '8px' }}>
        <span style={{ fontSize: '28px', fontWeight: 700, color: valueColor, letterSpacing: '-0.03em' }}>
          {value}
        </span>
        {badge && (
          <span style={{
            fontSize: '11px',
            fontWeight: 600,
            color: badgeColor,
            backgroundColor: `${badgeColor}15`,
            border: `1px solid ${badgeColor}40`,
            padding: '2px 6px',
            borderRadius: '4px'
          }}>
            {badge}
          </span>
        )}
      </div>

      {subtitle && (
        <span style={{ fontSize: '12px', color: '#64748b' }}>
          {subtitle}
        </span>
      )}
    </div>
  );
};

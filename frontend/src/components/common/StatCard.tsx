import React, { ReactNode } from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtext?: string;
  icon: ReactNode;
  accentColor?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtext,
  icon,
  accentColor = 'var(--color-flame)'
}) => {
  return (
    <div className="glass-card stat-card">
      <div className="stat-header">
        <span className="stat-title">{title}</span>
        <div className="stat-icon" style={{ color: accentColor }}>
          {icon}
        </div>
      </div>
      <div className="stat-value">{value}</div>
      {subtext && <div className="stat-sub">{subtext}</div>}
    </div>
  );
};

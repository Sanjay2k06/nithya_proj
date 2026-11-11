import React from 'react';
import { Flame, Cloud, CheckCircle, AlertTriangle, ShieldCheck, Clock } from 'lucide-react';
import { ClassLabel } from '../../types';

interface BadgeProps {
  type: ClassLabel | 'uncertain' | 'ACTIVE' | 'ACKNOWLEDGED' | 'CLOSED' | 'CRITICAL' | 'WARNING' | 'INFO';
  label?: string;
}

export const Badge: React.FC<BadgeProps> = ({ type, label }) => {
  const t = type.toLowerCase();

  if (t === 'fire' || t === 'critical') {
    return (
      <span className="badge badge-fire">
        <Flame size={12} />
        {label || type}
      </span>
    );
  }

  if (t === 'smoke' || t === 'warning') {
    return (
      <span className="badge badge-smoke">
        <Cloud size={12} />
        {label || type}
      </span>
    );
  }

  if (t === 'normal' || t === 'info') {
    return (
      <span className="badge badge-normal">
        <CheckCircle size={12} />
        {label || type}
      </span>
    );
  }

  if (t === 'uncertain') {
    return (
      <span className="badge">
        <AlertTriangle size={12} />
        {label || 'UNCERTAIN'}
      </span>
    );
  }

  if (type === 'ACTIVE') {
    return (
      <span className="badge badge-active">
        <AlertTriangle size={12} />
        Active
      </span>
    );
  }

  if (type === 'ACKNOWLEDGED') {
    return (
      <span className="badge badge-acknowledged">
        <Clock size={12} />
        Acknowledged
      </span>
    );
  }

  if (type === 'CLOSED') {
    return (
      <span className="badge badge-closed">
        <ShieldCheck size={12} />
        Resolved
      </span>
    );
  }

  return <span className="badge">{label || type}</span>;
};

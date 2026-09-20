import React from 'react';
import { ShieldCheck, AlertTriangle, AlertOctagon } from 'lucide-react';

const ConfidenceBadge = ({ score, tier }) => {
  const numericScore = typeof score === 'number' ? score : parseFloat(score) || 0;
  
  let badgeClass = 'badge-emerald';
  let Icon = ShieldCheck;
  let label = 'VERIFIED HIGH';

  if (numericScore >= 80 || tier === 'HIGH') {
    badgeClass = 'badge-emerald';
    Icon = ShieldCheck;
    label = `HIGH (${numericScore.toFixed(1)}%)`;
  } else if (numericScore >= 50 || tier === 'MEDIUM') {
    badgeClass = 'badge-amber';
    Icon = AlertTriangle;
    label = `MEDIUM (${numericScore.toFixed(1)}%)`;
  } else {
    badgeClass = 'badge-crimson';
    Icon = AlertOctagon;
    label = `LOW (${numericScore.toFixed(1)}%)`;
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold uppercase tracking-wider ${badgeClass}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600 }}>
      <Icon size={14} />
      <span>{label}</span>
    </span>
  );
};

export default ConfidenceBadge;

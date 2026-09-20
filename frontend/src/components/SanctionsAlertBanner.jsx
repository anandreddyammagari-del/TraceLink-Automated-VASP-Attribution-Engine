import React from 'react';
import { AlertTriangle, ShieldAlert, ExternalLink } from 'lucide-react';

const SanctionsAlertBanner = ({ match }) => {
  if (!match) return null;

  return (
    <div style={{
      background: '#FEF2F2',
      border: '1px solid #F87171',
      borderLeft: '4px solid #DC2626',
      borderRadius: '6px',
      padding: '0.85rem 1.25rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '1rem',
      marginBottom: '1rem'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <ShieldAlert size={22} color="#DC2626" />
        <div>
          <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#991B1B' }}>
            CRITICAL INTELLIGENCE ALERT: Sanctions Registry Match Detected
          </div>
          <div style={{ fontSize: '0.75rem', color: '#7F1D1D', marginTop: '0.15rem' }}>
            Entity: <strong>{match.entity_name}</strong> | List: <span className="badge-crimson" style={{ padding: '0.1rem 0.35rem', fontSize: '0.65rem' }}>{match.list_source}</span> | Program: {match.program}
          </div>
          {match.remarks && (
            <div style={{ fontSize: '0.72rem', color: '#B91C1C', marginTop: '0.15rem', fontStyle: 'italic' }}>
              Intelligence Notes: {match.remarks}
            </div>
          )}
        </div>
      </div>

      <span style={{
        fontSize: '0.7rem',
        fontWeight: 700,
        background: '#DC2626',
        color: '#FFFFFF',
        padding: '0.2rem 0.5rem',
        borderRadius: '4px',
        textTransform: 'uppercase',
        letterSpacing: '0.04em'
      }}>
        MANDATORY SEIZURE / FREEZE
      </span>
    </div>
  );
};

export default SanctionsAlertBanner;

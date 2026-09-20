import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FolderGit2, AlertCircle, Users, ArrowRight, Shield } from 'lucide-react';

const CaseCard = ({ caseItem }) => {
  const navigate = useNavigate();

  const getPriorityBadgeClass = (priority) => {
    switch (priority) {
      case 'CRITICAL':
        return 'badge-crimson';
      case 'HIGH':
        return 'badge-amber';
      default:
        return 'badge-navy';
    }
  };

  return (
    <div className="police-card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
          <span className="font-mono" style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--police-navy)' }}>
            {caseItem.fir_number}
          </span>
          <span className={getPriorityBadgeClass(caseItem.priority)} style={{ fontSize: '0.7rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: '4px' }}>
            {caseItem.priority}
          </span>
        </div>

        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--police-navy-dark)', marginBottom: '0.5rem', lineHeight: 1.3 }}>
          {caseItem.title}
        </h3>

        <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '0.75rem', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {caseItem.description}
        </p>

        <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', background: '#F8FAFC', padding: '0.4rem 0.6rem', borderRadius: '4px', marginBottom: '0.75rem' }}>
          <strong>Sections:</strong> {caseItem.crime_sections}
        </div>
      </div>

      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8125rem', borderTop: '1px solid var(--border-light)', paddingTop: '0.75rem', marginBottom: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--text-muted)' }}>
            <Users size={15} />
            <span>{caseItem.suspects_count || caseItem.suspects?.length || 0} Suspects</span>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>Disputed: </span>
            <strong style={{ color: '#0F2C59' }}>₹ {(caseItem.total_disputed_inr || 0).toLocaleString('en-IN')}</strong>
          </div>
        </div>

        <button
          onClick={() => navigate(`/cases/${caseItem.id}`)}
          className="btn-police-secondary"
          style={{ width: '100%', justifyContent: 'center', fontSize: '0.8125rem' }}
        >
          <span>Open Case Investigation</span>
          <ArrowRight size={14} />
        </button>
      </div>
    </div>
  );
};

export default CaseCard;

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Layers, TrendingUp, AlertCircle, FilePlus, Upload, ExternalLink, Network, CheckCircle2 } from 'lucide-react';
import GlobalTransactionLedger from '../components/GlobalTransactionLedger';
import { transactionsApi } from '../services/api';

const DashboardPage = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_transactions_tracked: 6,
    total_disputed_volume_inr: 48500000.0,
    active_cases: 2,
    tracked_suspects: 3,
    identified_vasp_deposits: 2
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await transactionsApi.getStats();
        setStats(res.data);
      } catch (err) {
        console.error("Failed to load tactical stats:", err);
      }
    };
    fetchStats();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner with Quick Actions */}
      <div style={{
        background: '#FFFFFF',
        border: '1px solid var(--border-medium)',
        borderRadius: '6px',
        padding: '1.25rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--police-navy-dark)' }}>
            Tactical Operations Command Dashboard
          </h2>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
            Continuous monitoring of cross-case suspect fund flows, peel chains, and automated VASP identification.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            onClick={() => navigate('/cases')}
            className="btn-police-secondary"
            style={{ fontSize: '0.8125rem' }}
          >
            <Layers size={15} />
            <span>View All FIRs</span>
          </button>
          <button
            onClick={() => navigate('/graph?person_id=SUSP-IND-9021')}
            className="btn-police-primary"
            style={{ fontSize: '0.8125rem' }}
          >
            <Network size={15} />
            <span>Launch Primary Graph</span>
          </button>
        </div>
      </div>

      {/* Stats Cards Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        {/* Disputed Volume */}
        <div className="police-card" style={{ padding: '1rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-subtle)', textTransform: 'uppercase' }}>
            Total Disputed Value
          </span>
          <div style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--police-navy-dark)', marginTop: '0.25rem' }}>
            ₹ {stats.total_disputed_volume_inr?.toLocaleString('en-IN') || '0'}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#166534', marginTop: '0.25rem', fontWeight: 600 }}>
            Active across 2 state FIRs
          </div>
        </div>

        {/* Transactions Tracked */}
        <div className="police-card" style={{ padding: '1rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-subtle)', textTransform: 'uppercase' }}>
            Transactions Tracked
          </span>
          <div style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--police-navy-dark)', marginTop: '0.25rem' }}>
            {stats.total_transactions_tracked || 0}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', marginTop: '0.25rem' }}>
            Aggregated cross-entity
          </div>
        </div>

        {/* Tracked Suspect Entities */}
        <div className="police-card" style={{ padding: '1rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-subtle)', textTransform: 'uppercase' }}>
            Tracked Suspects
          </span>
          <div style={{ fontSize: '1.35rem', fontWeight: 700, color: '#DC2626', marginTop: '0.25rem' }}>
            {stats.tracked_suspects || 0}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#DC2626', marginTop: '0.25rem', fontWeight: 600 }}>
            Severe / High Risk
          </div>
        </div>

        {/* Identified VASP Deposits */}
        <div className="police-card" style={{ padding: '1rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-subtle)', textTransform: 'uppercase' }}>
            Identified VASP Deposits
          </span>
          <div style={{ fontSize: '1.35rem', fontWeight: 700, color: '#166534', marginTop: '0.25rem' }}>
            {stats.identified_vasp_deposits || 0}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#166534', marginTop: '0.25rem', fontWeight: 600 }}>
            WazirX & Binance Nodal
          </div>
        </div>

        {/* Active Cases */}
        <div className="police-card" style={{ padding: '1rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-subtle)', textTransform: 'uppercase' }}>
            Active Cases
          </span>
          <div style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--police-navy-dark)', marginTop: '0.25rem' }}>
            {stats.active_cases || 0}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', marginTop: '0.25rem' }}>
            Under active investigation
          </div>
        </div>
      </div>

      {/* Central Master Multi-Entity Transaction Ledger (Directive #1) */}
      <GlobalTransactionLedger />
    </div>
  );
};

export default DashboardPage;

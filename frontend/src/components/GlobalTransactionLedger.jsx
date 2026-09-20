import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, ArrowRight, ExternalLink, Network, AlertTriangle, ShieldCheck, RefreshCw, Upload } from 'lucide-react';
import { transactionsApi } from '../services/api';
import DatasetUploadModal from './DatasetUploadModal';

const GlobalTransactionLedger = () => {
  const navigate = useNavigate();
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedRisk, setSelectedRisk] = useState('');
  const [totalCount, setTotalCount] = useState(0);
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const params = {
        limit: 100,
        search: search || undefined,
        risk_flag: selectedRisk || undefined
      };
      const res = await transactionsApi.getTransactions(params);
      setTransactions(res.data.transactions || []);
      setTotalCount(res.data.total || 0);
    } catch (err) {
      console.error("Failed to fetch transaction stream:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchTransactions();
    }, 300);
    return () => clearTimeout(timer);
  }, [search, selectedRisk]);

  const handleTraceInGraph = (entityId, entityType = 'person') => {
    if (entityType === 'person') {
      navigate(`/graph?person_id=${encodeURIComponent(entityId)}`);
    } else if (entityType === 'wallet') {
      navigate(`/graph?wallet=${encodeURIComponent(entityId)}`);
    } else if (entityType === 'tx') {
      navigate(`/graph?tx=${encodeURIComponent(entityId)}`);
    }
  };

  const getRiskBadgeClass = (flag) => {
    switch (flag) {
      case 'VASP_DEPOSIT':
        return 'badge-emerald';
      case 'FRAUD_COLLECTION':
      case 'CRITICAL':
        return 'badge-crimson';
      case 'PEEL_CHAIN':
      case 'STRUCTURING':
      case 'LAYERING_HOP_1':
        return 'badge-amber';
      default:
        return 'badge-navy';
    }
  };

  return (
    <div className="police-card" style={{ padding: '1.25rem' }}>
      {/* Header & Controls */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--police-navy-dark)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>Master Multi-Entity Transaction Stream</span>
            <span style={{
              background: '#E2E8F0',
              color: '#334155',
              fontSize: '0.75rem',
              fontWeight: 700,
              padding: '0.15rem 0.5rem',
              borderRadius: '12px'
            }}>
              {totalCount} Entries
            </span>
          </h2>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
            Real-time multi-suspect evidentiary flow across all active FIR cases. Click <strong>[Trace in Graph]</strong> or any <strong>Person ID</strong> to pivot to topological analysis.
          </p>
        </div>

        {/* Search & Refresh */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ position: 'relative' }}>
            <Search size={16} color="#64748B" style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Search Person ID, Wallet, Tx Hash..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                padding: '0.45rem 0.75rem 0.45rem 2rem',
                fontSize: '0.8125rem',
                border: '1px solid var(--border-medium)',
                borderRadius: '4px',
                width: '280px',
                outline: 'none'
              }}
            />
          </div>

          <select
            value={selectedRisk}
            onChange={(e) => setSelectedRisk(e.target.value)}
            style={{
              padding: '0.45rem 0.75rem',
              fontSize: '0.8125rem',
              border: '1px solid var(--border-medium)',
              borderRadius: '4px',
              background: '#FFFFFF'
            }}
          >
            <option value="">All Risk Patterns</option>
            <option value="VASP_DEPOSIT">VASP Deposit Only</option>
            <option value="FRAUD_COLLECTION">Primary Fraud Inflow</option>
            <option value="PEEL_CHAIN">Peel Chain Obfuscation</option>
            <option value="STRUCTURING">Smurfing / Structuring</option>
          </select>

          <button
            onClick={() => setIsUploadOpen(true)}
            className="btn-police-primary"
            style={{ padding: '0.45rem 0.75rem', fontSize: '0.8125rem' }}
            title="Upload custom CSV/JSON transaction dataset"
          >
            <Upload size={14} />
            <span>Upload Dataset</span>
          </button>

          <button
            onClick={fetchTransactions}
            className="btn-police-secondary"
            style={{ padding: '0.45rem 0.75rem' }}
            title="Reload ledger"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      <DatasetUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={() => {
          fetchTransactions();
        }}
      />

      {/* Ledger Table */}
      <div style={{ overflowX: 'auto', border: '1px solid var(--border-medium)', borderRadius: '4px' }}>
        <table className="police-table">
          <thead>
            <tr>
              <th>Timestamp (UTC)</th>
              <th>Suspect / Person ID</th>
              <th>Source Address (From)</th>
              <th>Destination Address (To)</th>
              <th>Amount & Valuation</th>
              <th>Risk Classification</th>
              <th>Attributed Entity / VASP</th>
              <th style={{ textAlign: 'center' }}>Forensic Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                  Loading evidentiary transaction ledger...
                </td>
              </tr>
            ) : transactions.length === 0 ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                  No transactions matching current query filters.
                </td>
              </tr>
            ) : (
              transactions.map((tx) => (
                <tr key={tx.id}>
                  {/* Timestamp */}
                  <td className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {tx.timestamp ? tx.timestamp.replace('T', ' ').substring(0, 19) : 'N/A'}
                  </td>

                  {/* Person ID Pill - Clickable to pivot */}
                  <td>
                    <button
                      onClick={() => handleTraceInGraph(tx.person_id, 'person')}
                      title={`Pivot to topological trace for ${tx.person_id}`}
                      style={{
                        background: '#EFF6FF',
                        border: '1px solid #BFDBFE',
                        color: '#1D4ED8',
                        padding: '0.15rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.25rem'
                      }}
                    >
                      <span>{tx.person_id}</span>
                      <ExternalLink size={10} />
                    </button>
                  </td>

                  {/* From Address */}
                  <td className="font-mono" style={{ fontSize: '0.75rem' }}>
                    <span
                      onClick={() => handleTraceInGraph(tx.from_address, 'wallet')}
                      style={{ cursor: 'pointer', color: 'var(--police-navy)' }}
                      title={tx.from_address}
                    >
                      {tx.from_address.substring(0, 8)}...{tx.from_address.substring(tx.from_address.length - 6)}
                    </span>
                  </td>

                  {/* To Address */}
                  <td className="font-mono" style={{ fontSize: '0.75rem' }}>
                    <span
                      onClick={() => handleTraceInGraph(tx.to_address, 'wallet')}
                      style={{ cursor: 'pointer', color: 'var(--police-navy)' }}
                      title={tx.to_address}
                    >
                      {tx.to_address.substring(0, 8)}...{tx.to_address.substring(tx.to_address.length - 6)}
                    </span>
                  </td>

                  {/* Amount & INR */}
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                      {tx.value.toLocaleString()} {tx.token_symbol}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
                      ₹ {tx.value_inr ? tx.value_inr.toLocaleString('en-IN') : '0.00'}
                    </div>
                  </td>

                  {/* Risk Flag */}
                  <td>
                    <span className={getRiskBadgeClass(tx.risk_flag)} style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      padding: '0.15rem 0.5rem',
                      borderRadius: '4px',
                      fontSize: '0.7rem',
                      fontWeight: 700
                    }}>
                      {tx.risk_flag.replace(/_/g, ' ')}
                    </span>
                  </td>

                  {/* Attributed Entity */}
                  <td style={{ fontWeight: 500, color: tx.risk_flag === 'VASP_DEPOSIT' ? '#166534' : 'var(--text-main)' }}>
                    {tx.attributed_entity}
                  </td>

                  {/* Pivot Action */}
                  <td style={{ textAlign: 'center' }}>
                    <button
                      onClick={() => handleTraceInGraph(tx.person_id !== 'UNASSIGNED' ? tx.person_id : tx.from_address, tx.person_id !== 'UNASSIGNED' ? 'person' : 'wallet')}
                      className="btn-police-action"
                      title="Pivot to force-directed graph to trace fund flow to VASP"
                    >
                      <Network size={13} />
                      <span>Trace in Graph</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default GlobalTransactionLedger;

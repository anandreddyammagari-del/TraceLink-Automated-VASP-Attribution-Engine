import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FolderGit2, ArrowLeft, Network, FileText, User, Shield, Users, ArrowRight } from 'lucide-react';
import LawfulRequestModal from '../components/LawfulRequestModal';
import { casesApi, transactionsApi } from '../services/api';

const CaseDetailsPage = () => {
  const { caseId } = useParams();
  const navigate = useNavigate();

  const [caseData, setCaseData] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isNoticeModalOpen, setIsNoticeModalOpen] = useState(false);

  useEffect(() => {
    const loadDetails = async () => {
      try {
        const res = await casesApi.getCaseDetail(caseId);
        setCaseData(res.data);

        // Fetch transactions for this case
        const txRes = await transactionsApi.getTransactions({ case_id: caseId, limit: 50 });
        setTransactions(txRes.data.transactions || []);
      } catch (err) {
        console.error("Failed to load case details:", err);
      } finally {
        setLoading(false);
      }
    };
    loadDetails();
  }, [caseId]);

  if (loading) {
    return (
      <div className="police-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        Loading case dossier...
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="police-card" style={{ padding: '3rem', textAlign: 'center', color: '#991B1B' }}>
        Case record not found.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Case Header */}
      <div className="police-card" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button
              onClick={() => navigate('/cases')}
              className="btn-police-secondary"
              style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
            >
              <ArrowLeft size={14} />
              <span>Back</span>
            </button>
            <span className="font-mono" style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--police-navy)' }}>
              {caseData.fir_number}
            </span>
            <span className="badge-crimson" style={{ fontSize: '0.7rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: '4px' }}>
              {caseData.priority} PRIORITY
            </span>
            <span className="badge-emerald" style={{ fontSize: '0.7rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: '4px' }}>
              {caseData.status}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button
              onClick={() => window.open(`/api/reports/case/${caseData.id}/pdf`, '_blank')}
              className="btn-police-secondary"
              style={{ fontSize: '0.8125rem' }}
              title="Download Section 63 BSA / 65B IEA Compliant PDF Dossier"
            >
              <FileText size={15} color="#166534" />
              <span>Court Dossier (PDF)</span>
            </button>
            <button
              onClick={() => setIsNoticeModalOpen(true)}
              className="btn-police-secondary"
              style={{ fontSize: '0.8125rem' }}
            >
              <FileText size={15} />
              <span>Draft Sec 94 Notice</span>
            </button>
            <button
              onClick={() => navigate(`/graph?case_id=${caseData.id}`)}
              className="btn-police-primary"
              style={{ fontSize: '0.8125rem' }}
            >
              <Network size={15} />
              <span>Open Case Graph</span>
            </button>
          </div>
        </div>

        <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--police-navy-dark)', marginBottom: '0.5rem' }}>
          {caseData.title}
        </h1>

        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          {caseData.description}
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', background: '#F8FAFC', padding: '1rem', borderRadius: '6px', border: '1px solid var(--border-light)', fontSize: '0.8125rem' }}>
          <div>
            <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: '0.75rem' }}>Police Station / Jurisdiction</span>
            <strong>{caseData.police_station}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: '0.75rem' }}>Statutory Sections</span>
            <strong>{caseData.crime_sections}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: '0.75rem' }}>Investigating Officer</span>
            <strong>{caseData.investigating_officer?.name} ({caseData.investigating_officer?.badge})</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-subtle)', display: 'block', fontSize: '0.75rem' }}>Total Disputed Financial Value</span>
            <strong style={{ color: '#0F2C59' }}>₹ {(caseData.total_disputed_inr || 0).toLocaleString('en-IN')}</strong>
          </div>
        </div>
      </div>

      {/* Suspect Entities Section */}
      <div className="police-card" style={{ padding: '1.25rem' }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--police-navy-dark)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Users size={16} />
          <span>Accused Persons & Suspect Entities Under Tracking</span>
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
          {caseData.suspects?.map((s) => (
            <div key={s.id} style={{ background: '#FFFFFF', border: '1px solid var(--border-medium)', borderRadius: '6px', padding: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span className="font-mono" style={{ fontSize: '0.75rem', fontWeight: 700, background: '#EFF6FF', color: '#1D4ED8', padding: '0.15rem 0.5rem', borderRadius: '4px' }}>
                  {s.person_id}
                </span>
                <span className={s.risk_category === 'SEVERE' ? 'badge-crimson' : 'badge-amber'} style={{ fontSize: '0.65rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: '3px' }}>
                  {s.risk_category}
                </span>
              </div>

              <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--police-navy-dark)' }}>
                {s.full_name}
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', marginBottom: '0.5rem' }}>
                Aliases: {s.aliases || 'None reported'} | ID: {s.national_id || 'Under verification'}
              </p>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                {s.notes}
              </p>

              <button
                onClick={() => navigate(`/graph?person_id=${s.person_id}`)}
                className="btn-police-action"
                style={{ width: '100%', justifyContent: 'center' }}
              >
                <Network size={13} />
                <span>Trace Back in Graph</span>
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Case Transactions Ledger */}
      <div className="police-card" style={{ padding: '1.25rem' }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--police-navy-dark)', marginBottom: '1rem' }}>
          Transaction Ledger for FIR {caseData.fir_number}
        </h2>
        <table className="police-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Person ID</th>
              <th>From Address</th>
              <th>To Address</th>
              <th>Amount</th>
              <th>Risk Flag</th>
              <th>Attributed Entity</th>
              <th style={{ textAlign: 'center' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {transactions.length === 0 ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  No transactions recorded specifically for this case yet.
                </td>
              </tr>
            ) : (
              transactions.map((tx) => (
                <tr key={tx.id}>
                  <td className="font-mono" style={{ fontSize: '0.75rem' }}>
                    {tx.timestamp ? tx.timestamp.replace('T', ' ').substring(0, 19) : 'N/A'}
                  </td>
                  <td>
                    <span className="badge-navy" style={{ fontSize: '0.75rem', padding: '0.15rem 0.45rem', borderRadius: '4px' }}>
                      {tx.person_id}
                    </span>
                  </td>
                  <td className="font-mono" style={{ fontSize: '0.75rem' }}>
                    {tx.from_address.substring(0, 8)}...
                  </td>
                  <td className="font-mono" style={{ fontSize: '0.75rem' }}>
                    {tx.to_address.substring(0, 8)}...
                  </td>
                  <td style={{ fontWeight: 600 }}>
                    {tx.value} {tx.token_symbol}
                  </td>
                  <td>
                    <span className="badge-amber" style={{ fontSize: '0.7rem', padding: '0.1rem 0.4rem', borderRadius: '3px' }}>
                      {tx.risk_flag}
                    </span>
                  </td>
                  <td>{tx.attributed_entity}</td>
                  <td style={{ textAlign: 'center' }}>
                    <button
                      onClick={() => navigate(`/graph?person_id=${tx.person_id}`)}
                      className="btn-police-action"
                    >
                      Trace
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Lawful Request Modal */}
      {caseData && (
        <LawfulRequestModal
          isOpen={isNoticeModalOpen}
          onClose={() => setIsNoticeModalOpen(false)}
          attribution={{
            id: `case-attrib-${caseData.id}`,
            target_vasp_name: 'WazirX (Zanmai Labs Pvt Ltd)',
            vasp_deposit_address: '0x503828976d22510aad0201ac7ec88293211d23dc',
            confidence_score: 91.2,
            confidence_tier: 'HIGH',
            total_volume: transactions.reduce((acc, tx) => acc + (tx.value || 0), 0) || 8.2,
            token_symbol: 'ETH',
            hop_distance: 3
          }}
          caseId={caseData.id}
          firNumber={caseData.fir_number}
        />
      )}
    </div>
  );
};

export default CaseDetailsPage;

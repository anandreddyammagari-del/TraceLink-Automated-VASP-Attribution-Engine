import React, { useState, useEffect } from 'react';
import { History, ShieldCheck, AlertOctagon, RefreshCw, Lock } from 'lucide-react';
import { auditApi } from '../services/api';

const AuditLogsPage = () => {
  const [logs, setLogs] = useState([]);
  const [verificationResult, setVerificationResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);

  const fetchLogs = async () => {
    try {
      const res = await auditApi.getAuditLogs({ limit: 100 });
      setLogs(res.data);
    } catch (err) {
      console.error("Failed to load audit trail:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyChain = async () => {
    setVerifying(true);
    try {
      const res = await auditApi.verifyChain();
      setVerificationResult(res.data);
    } catch (err) {
      console.error("Failed to verify audit chain:", err);
      setVerificationResult({ verified: false, error: "Verification endpoint error." });
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    handleVerifyChain();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header with Verification Status */}
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
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--police-navy-dark)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>Tamper-Evident Cryptographic Audit Trail</span>
            <span className="badge-navy" style={{ fontSize: '0.75rem', padding: '0.15rem 0.5rem', borderRadius: '4px' }}>
              SHA-256 Hash Chain
            </span>
          </h2>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
            Append-only, immutable forensic log of all investigator queries, node expansions, and officer sign-offs.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {verificationResult && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.4rem 0.8rem',
              borderRadius: '4px',
              background: verificationResult.verified ? '#DCFCE7' : '#FEE2E2',
              color: verificationResult.verified ? '#166534' : '#991B1B',
              border: `1px solid ${verificationResult.verified ? '#86EFAC' : '#FCA5A5'}`,
              fontSize: '0.75rem',
              fontWeight: 700
            }}>
              {verificationResult.verified ? <ShieldCheck size={16} /> : <AlertOctagon size={16} />}
              <span>
                {verificationResult.verified
                  ? `CHAIN VERIFIED AUTHENTIC (${verificationResult.entries_checked} Blocks)`
                  : `SECURITY ALERT: ${verificationResult.error || 'Chain Broken!'}`}
              </span>
            </div>
          )}

          <button
            onClick={handleVerifyChain}
            disabled={verifying}
            className="btn-police-primary"
            style={{ fontSize: '0.8125rem' }}
          >
            <RefreshCw size={14} className={verifying ? 'animate-spin' : ''} />
            <span>{verifying ? 'Verifying Hashes...' : 'Re-Verify SHA-256 Chain'}</span>
          </button>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="police-card" style={{ padding: '1.25rem' }}>
        <div style={{ overflowX: 'auto' }}>
          <table className="police-table">
            <thead>
              <tr>
                <th>Timestamp (UTC)</th>
                <th>Event Type</th>
                <th>Officer Badge</th>
                <th>Case FIR</th>
                <th>Forensic Action Details</th>
                <th>Previous Block Hash</th>
                <th>Current Block SHA-256</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    Reading cryptographic chain...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No audit records logged yet.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id}>
                    <td className="font-mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      {log.timestamp ? log.timestamp.replace('T', ' ').substring(0, 19) : 'N/A'}
                    </td>
                    <td>
                      <span className="badge-navy" style={{ fontSize: '0.7rem', padding: '0.15rem 0.45rem', borderRadius: '3px', fontWeight: 600 }}>
                        {log.event_type}
                      </span>
                    </td>
                    <td className="font-mono" style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--police-navy)' }}>
                      {log.officer_id}
                    </td>
                    <td>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-main)' }}>
                        {log.case_id || 'GLOBAL'}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.8125rem', color: 'var(--text-main)' }}>
                      {log.details}
                    </td>
                    <td className="font-mono" style={{ fontSize: '0.68rem', color: '#64748B' }} title={log.prev_hash}>
                      {log.prev_hash.substring(0, 10)}...
                    </td>
                    <td className="font-mono" style={{ fontSize: '0.68rem', color: '#166534', fontWeight: 600 }} title={log.current_hash}>
                      {log.current_hash.substring(0, 12)}...
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AuditLogsPage;

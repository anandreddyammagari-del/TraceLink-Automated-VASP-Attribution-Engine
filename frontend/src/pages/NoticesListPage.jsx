import React, { useState, useEffect } from 'react';
import { FileText, CheckCircle2, Clock, Printer, Shield, Eye } from 'lucide-react';
import { requestsApi } from '../services/api';
import { useAuth } from '../hooks/useAuth';

const NoticesListPage = () => {
  const { clearanceLevel } = useAuth();
  const [notices, setNotices] = useState([]);
  const [selectedNotice, setSelectedNotice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [signing, setSigning] = useState(false);
  const [signSuccess, setSignSuccess] = useState('');

  const fetchNotices = async () => {
    try {
      const res = await requestsApi.getNotices();
      setNotices(res.data);
      if (res.data.length > 0 && !selectedNotice) {
        const detail = await requestsApi.getNoticeDetail(res.data[0].id);
        setSelectedNotice(detail.data);
      }
    } catch (err) {
      console.error("Failed to load notices:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotices();
  }, []);

  const handleSelectNotice = async (id) => {
    try {
      const res = await requestsApi.getNoticeDetail(id);
      setSelectedNotice(res.data);
      setSignSuccess('');
    } catch (err) {
      console.error("Failed to fetch notice detail:", err);
    }
  };

  const handleSignOff = async () => {
    if (!selectedNotice) return;
    setSigning(true);
    try {
      await requestsApi.signNotice(selectedNotice.id, {
        confirm_local_review_only: true,
        officer_notes: "Approved after forensic verification of blockchain attribution path."
      });
      setSignSuccess('Statutory notice successfully signed and sealed for official submission.');
      fetchNotices();
      const updated = await requestsApi.getNoticeDetail(selectedNotice.id);
      setSelectedNotice(updated.data);
    } catch (err) {
      console.error("Failed to sign notice:", err);
      alert(err.response?.data?.detail || "Sign-off failed. Clearance L2/L3 required.");
    } finally {
      setSigning(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: '1.5rem' }}>
      {/* Notice List Sidebar */}
      <div className="police-card" style={{ padding: '1.25rem' }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--police-navy-dark)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FileText size={18} />
          <span>Statutory Notice Drafts (Sec 94 BNSS)</span>
        </h2>

        {loading ? (
          <div style={{ padding: '2rem 0', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading notice repository...
          </div>
        ) : notices.length === 0 ? (
          <div style={{ padding: '2rem 0', textAlign: 'center', color: 'var(--text-muted)' }}>
            No notices drafted yet. Open any case or trace graph to draft a notice.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {notices.map((n) => (
              <div
                key={n.id}
                onClick={() => handleSelectNotice(n.id)}
                style={{
                  background: selectedNotice?.id === n.id ? '#EFF6FF' : '#FFFFFF',
                  border: selectedNotice?.id === n.id ? '2px solid var(--police-navy)' : '1px solid var(--border-medium)',
                  borderRadius: '6px',
                  padding: '0.85rem',
                  cursor: 'pointer',
                  transition: 'all 0.1s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <span className="font-mono" style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--police-navy)' }}>
                    {n.notice_reference_number}
                  </span>
                  <span className={n.status === 'APPROVED_PRINT_READY' ? 'badge-emerald' : 'badge-amber'} style={{ fontSize: '0.65rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: '3px' }}>
                    {n.status}
                  </span>
                </div>

                <div style={{ fontWeight: 600, fontSize: '0.8125rem', color: 'var(--police-navy-dark)' }}>
                  To: {n.target_vasp_name}
                </div>
                <div className="font-mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                  Addr: {n.target_deposit_wallet.substring(0, 10)}...
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Notice Viewer & Sign-Off Panel */}
      <div className="police-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        {selectedNotice ? (
          <div>
            {/* Header with Print & Actions */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '2px solid var(--border-medium)', paddingBottom: '1rem', marginBottom: '1.25rem' }}>
              <div>
                <span className="font-mono" style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--police-navy)' }}>
                  {selectedNotice.notice_reference_number}
                </span>
                <h2 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--police-navy-dark)' }}>
                  Statutory Production Notice — {selectedNotice.target_vasp_name}
                </h2>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <button
                  onClick={handlePrint}
                  className="btn-police-secondary"
                  style={{ fontSize: '0.8125rem' }}
                >
                  <Printer size={15} />
                  <span>Print Court Copy</span>
                </button>

                {selectedNotice.status !== 'APPROVED_PRINT_READY' && (
                  <button
                    onClick={handleSignOff}
                    disabled={signing}
                    className="btn-police-primary"
                    style={{ fontSize: '0.8125rem' }}
                  >
                    <CheckCircle2 size={15} />
                    <span>{signing ? 'Sealing...' : 'Senior Officer Sign-Off'}</span>
                  </button>
                )}
              </div>
            </div>

            {signSuccess && (
              <div style={{ background: '#DCFCE7', border: '1px solid #86EFAC', color: '#166534', padding: '0.75rem', borderRadius: '4px', fontSize: '0.8125rem', marginBottom: '1rem' }}>
                {signSuccess}
              </div>
            )}

            {/* Document Body */}
            <div style={{
              background: '#F8FAFC',
              border: '1px solid var(--border-medium)',
              borderRadius: '4px',
              padding: '1.5rem',
              whiteSpace: 'pre-wrap',
              fontFamily: 'JetBrains Mono',
              fontSize: '0.8125rem',
              lineHeight: 1.6,
              color: '#0F172A',
              maxHeight: '520px',
              overflowY: 'auto'
            }}>
              {selectedNotice.notice_body}
            </div>

            {/* Legal Advisory Footer */}
            <div style={{ marginTop: '1rem', fontSize: '0.75rem', color: '#64748B', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Shield size={14} color="#166534" />
              <span>
                Statutory clause: <strong>{selectedNotice.statutory_clause}</strong>. This document is stored in the local evidence database. Direct transmission to SAHYOG or external portals is deactivated.
              </span>
            </div>
          </div>
        ) : (
          <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            Select a drafted notice to review and print.
          </div>
        )}
      </div>
    </div>
  );
};

export default NoticesListPage;

import React, { useState, useEffect } from 'react';
import { FileText, X, CheckCircle2, AlertOctagon, Printer, Shield, Eye, Lock } from 'lucide-react';
import { requestsApi } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import ConfidenceBadge from './ConfidenceBadge';

const LawfulRequestModal = ({ isOpen, onClose, attribution, caseId, firNumber }) => {
  const { officer, clearanceLevel } = useAuth();
  const [customRemarks, setCustomRemarks] = useState('');
  const [drafting, setDrafting] = useState(false);
  const [signing, setSigning] = useState(false);
  const [createdDraft, setCreatedDraft] = useState(null);
  const [error, setError] = useState('');
  const [signSuccess, setSignSuccess] = useState('');

  if (!isOpen || !attribution) return null;

  const handleGenerateDraft = async () => {
    setDrafting(true);
    setError('');
    try {
      const res = await requestsApi.createDraft({
        attribution_id: attribution.id,
        case_id: caseId || 'FIR-2026-DEL-CY-0042',
        target_vasp_name: attribution.target_vasp_name,
        target_deposit_wallet: attribution.vasp_deposit_address,
        custom_remarks: customRemarks || undefined
      });
      setCreatedDraft(res.data);
    } catch (err) {
      console.error("Drafting error:", err);
      setError(err.response?.data?.detail || 'Failed to generate statutory notice.');
    } finally {
      setDrafting(false);
    }
  };

  const handleSignOff = async () => {
    if (!createdDraft) return;
    setSigning(true);
    setError('');
    try {
      const res = await requestsApi.signNotice(createdDraft.id, {
        confirm_local_review_only: true,
        officer_notes: `Statutory sign-off performed by ${officer?.rank} ${officer?.badge_number}`
      });
      setSignSuccess(`Statutory notice ${createdDraft.notice_reference_number} officially signed and approved for local printing.`);
      setCreatedDraft({ ...createdDraft, status: 'APPROVED_PRINT_READY' });
    } catch (err) {
      console.error("Sign-off error:", err);
      setError(err.response?.data?.detail || 'Sign-off requires L2 Senior Officer clearance.');
    } finally {
      setSigning(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleClose = () => {
    setCreatedDraft(null);
    setCustomRemarks('');
    setError('');
    setSignSuccess('');
    onClose();
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(15, 23, 42, 0.7)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '1.5rem'
    }}>
      <div style={{
        background: '#FFFFFF',
        borderRadius: '8px',
        width: '100%',
        maxWidth: '750px',
        maxHeight: '90vh',
        display: 'flex',
        flexDirection: 'column',
        border: '1px solid var(--border-medium)',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        overflow: 'hidden'
      }}>
        {/* Modal Header */}
        <div style={{
          background: 'var(--police-navy-dark)',
          color: '#FFFFFF',
          padding: '1rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '3px solid #FCD34D'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <FileText size={20} color="#FCD34D" />
            <div>
              <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>
                Section 94 BNSS (2023) Lawful Request Generator
              </h3>
              <p style={{ fontSize: '0.72rem', color: '#93C5FD' }}>
                Order to Produce KYC / Transaction Logs r/w Sec 79(3)(b) IT Act, 2000
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            style={{ background: 'transparent', border: 'none', color: '#FFFFFF', cursor: 'pointer' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '1.25rem', overflowY: 'auto', flex: 1 }}>
          {error && (
            <div style={{
              background: '#FEE2E2',
              border: '1px solid #FCA5A5',
              color: '#991B1B',
              padding: '0.75rem',
              borderRadius: '4px',
              fontSize: '0.8125rem',
              marginBottom: '1rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <AlertOctagon size={16} />
              <span>{error}</span>
            </div>
          )}

          {signSuccess && (
            <div style={{
              background: '#DCFCE7',
              border: '1px solid #86EFAC',
              color: '#166534',
              padding: '0.75rem',
              borderRadius: '4px',
              fontSize: '0.8125rem',
              marginBottom: '1rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <CheckCircle2 size={16} />
              <span>{signSuccess}</span>
            </div>
          )}

          {!createdDraft ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {/* Attribution Particulars Card */}
              <div style={{ background: '#F8FAFC', border: '1px solid var(--border-medium)', borderRadius: '6px', padding: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--police-navy)' }}>
                    FORENSIC ATTRIBUTION TARGET
                  </span>
                  <ConfidenceBadge score={attribution.confidence_score} tier={attribution.confidence_tier} />
                </div>

                <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--police-navy-dark)', marginBottom: '0.35rem' }}>
                  {attribution.target_vasp_name}
                </div>

                <div className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', background: '#E2E8F0', padding: '0.35rem 0.5rem', borderRadius: '4px', wordBreak: 'break-all', marginBottom: '0.5rem' }}>
                  Deposit Gateway: {attribution.vasp_deposit_address}
                </div>

                <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.8125rem' }}>
                  <div>
                    <span style={{ color: 'var(--text-subtle)' }}>Tracked Inflow: </span>
                    <strong>{attribution.total_volume} {attribution.token_symbol || 'ETH'}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-subtle)' }}>Hop Distance: </span>
                    <strong>{attribution.hop_distance} hop(s)</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-subtle)' }}>FIR Ref: </span>
                    <strong className="font-mono">{firNumber || 'FIR-2026-DEL-CY-0042'}</strong>
                  </div>
                </div>
              </div>

              {/* Custom Instructions Field */}
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
                  Specific Investigative Directives to Exchange (Optional)
                </label>
                <textarea
                  rows={3}
                  value={customRemarks}
                  onChange={(e) => setCustomRemarks(e.target.value)}
                  placeholder="e.g. Preserve IP connection logs for port 443; freeze all fiat withdrawal destinations linked to this PAN."
                  style={{
                    width: '100%',
                    padding: '0.55rem',
                    border: '1px solid var(--border-medium)',
                    borderRadius: '4px',
                    fontSize: '0.8125rem',
                    fontFamily: 'Inter',
                    outline: 'none'
                  }}
                />
              </div>

              {/* Statutory Notice Callout */}
              <div className="statutory-banner">
                <strong>Mandatory Safety Notice:</strong> This draft notice is stored locally in the tamper-evident evidence locker for officer review and court presentation. Electronic transmission to external portals (SAHYOG) is deactivated.
              </div>
            </div>
          ) : (
            <div>
              {/* Draft Viewer & Print Controls */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                <span className="font-mono" style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--police-navy)' }}>
                  Ref: {createdDraft.notice_reference_number}
                </span>
                <span className={createdDraft.status === 'APPROVED_PRINT_READY' ? 'badge-emerald' : 'badge-amber'} style={{ fontSize: '0.7rem', fontWeight: 700, padding: '0.15rem 0.45rem', borderRadius: '4px' }}>
                  {createdDraft.status}
                </span>
              </div>

              <div style={{
                background: '#F8FAFC',
                border: '1px solid var(--border-medium)',
                borderRadius: '4px',
                padding: '1.25rem',
                fontFamily: 'JetBrains Mono',
                fontSize: '0.78rem',
                lineHeight: 1.55,
                whiteSpace: 'pre-wrap',
                maxHeight: '400px',
                overflowY: 'auto'
              }}>
                {createdDraft.notice_body}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer Actions */}
        <div style={{
          background: '#F1F5F9',
          borderTop: '1px solid var(--border-medium)',
          padding: '0.85rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <button
            onClick={handleClose}
            className="btn-police-secondary"
            style={{ fontSize: '0.8125rem' }}
          >
            {createdDraft ? 'Close' : 'Cancel'}
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {!createdDraft ? (
              <button
                onClick={handleGenerateDraft}
                disabled={drafting}
                className="btn-police-primary"
                style={{ fontSize: '0.8125rem' }}
              >
                <FileText size={15} />
                <span>{drafting ? 'Generating...' : 'Generate Section 94 Notice Draft'}</span>
              </button>
            ) : (
              <>
                <button
                  onClick={handlePrint}
                  className="btn-police-secondary"
                  style={{ fontSize: '0.8125rem' }}
                >
                  <Printer size={15} />
                  <span>Print Court Copy</span>
                </button>

                {createdDraft.status !== 'APPROVED_PRINT_READY' && (
                  <button
                    onClick={handleSignOff}
                    disabled={signing}
                    className="btn-police-primary"
                    style={{ fontSize: '0.8125rem' }}
                  >
                    <CheckCircle2 size={15} />
                    <span>{signing ? 'Signing...' : 'Officer Digital Sign-Off'}</span>
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LawfulRequestModal;

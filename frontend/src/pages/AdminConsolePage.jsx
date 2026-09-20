import React, { useState, useEffect } from 'react';
import { Shield, Users, Database, RefreshCw, Key, Lock, CheckCircle2, AlertOctagon, UserPlus, HardDrive } from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

const AdminConsolePage = () => {
  const { clearanceLevel } = useAuth();
  const [officers, setOfficers] = useState([]);
  const [dataPacks, setDataPacks] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reloadingPacks, setReloadingPacks] = useState(false);
  const [packSuccess, setPackSuccess] = useState('');
  const [snapshotResult, setSnapshotResult] = useState(null);
  const [creatingSnapshot, setCreatingSnapshot] = useState(false);

  // New officer form modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [newBadge, setNewBadge] = useState('');
  const [newFullName, setNewFullName] = useState('');
  const [newRank, setNewRank] = useState('Inspector (Cyber Crime)');
  const [newStation, setNewStation] = useState('Special Cyber Operations');
  const [newClearance, setNewClearance] = useState('L1_INVESTIGATOR');
  const [newPassword, setNewPassword] = useState('Police@Secure2026');
  const [provisionError, setProvisionError] = useState('');
  const [provisionSuccess, setProvisionSuccess] = useState('');

  const fetchData = async () => {
    try {
      const [offRes, dpRes] = await Promise.all([
        api.get('/admin/officers'),
        api.get('/admin/datapacks')
      ]);
      setOfficers(offRes.data);
      setDataPacks(dpRes.data);
    } catch (err) {
      console.error("Failed to load admin data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleReloadDataPacks = async () => {
    setReloadingPacks(true);
    setPackSuccess('');
    try {
      const res = await api.post('/admin/datapacks/reload');
      setPackSuccess(`Data packs reloaded: ${res.data.indexed_vasp_count} VASPs and ${res.data.indexed_sanctions_count} Sanctioned entities active.`);
      fetchData();
    } catch (err) {
      console.error("Reload error:", err);
    } finally {
      setReloadingPacks(false);
    }
  };

  const handleCreateSnapshot = async () => {
    setCreatingSnapshot(true);
    try {
      const res = await api.post('/admin/backup/create');
      setSnapshotResult(res.data);
    } catch (err) {
      console.error("Snapshot error:", err);
    } finally {
      setCreatingSnapshot(false);
    }
  };

  const handleToggleStatus = async (userId, currentStatus) => {
    try {
      await api.patch(`/admin/officers/${userId}/status`, { is_active: !currentStatus });
      fetchData();
    } catch (err) {
      console.error("Status toggle error:", err);
    }
  };

  const handleProvisionOfficer = async (e) => {
    e.preventDefault();
    setProvisionError('');
    setProvisionSuccess('');
    try {
      await api.post('/admin/officers', {
        badge_number: newBadge,
        full_name: newFullName,
        rank: newRank,
        police_station: newStation,
        clearance_level: newClearance,
        password: newPassword
      });
      setProvisionSuccess(`Officer ${newBadge} successfully provisioned.`);
      setNewBadge('');
      setNewFullName('');
      setShowAddModal(false);
      fetchData();
    } catch (err) {
      setProvisionError(err.response?.data?.detail || 'Provisioning failed.');
    }
  };

  if (clearanceLevel !== 'L3_ADMIN_DIRECTOR') {
    return (
      <div className="police-card" style={{ padding: '3rem', textAlign: 'center', color: '#991B1B' }}>
        <AlertOctagon size={40} style={{ margin: '0 auto 1rem' }} />
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Access Restricted: L3 Clearance Required</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
          This terminal is restricted to Directorate Administrators and Cyber Crime Station In-Charges.
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner */}
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
            <Key size={20} color="#FCD34D" />
            <span>L3 Institutional Administration & Governance Console</span>
          </h2>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
            Supervisory control over officer clearance credentials, offline intelligence fixtures, and forensic backups.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-police-primary"
            style={{ fontSize: '0.8125rem' }}
          >
            <UserPlus size={15} />
            <span>Provision Officer</span>
          </button>
          <button
            onClick={handleCreateSnapshot}
            disabled={creatingSnapshot}
            className="btn-police-secondary"
            style={{ fontSize: '0.8125rem' }}
          >
            <HardDrive size={15} />
            <span>{creatingSnapshot ? 'Sealing...' : 'Cryptographic Snapshot'}</span>
          </button>
        </div>
      </div>

      {snapshotResult && (
        <div style={{ background: '#DCFCE7', border: '1px solid #86EFAC', color: '#166534', padding: '0.85rem 1.25rem', borderRadius: '6px', fontSize: '0.8125rem' }}>
          <strong>Forensic Database Snapshot Sealed:</strong> Filename <code>{snapshotResult.snapshot_filename}</code> | SHA-256: <code>{snapshotResult.sha256_integrity_seal?.substring(0, 16)}...</code>
        </div>
      )}

      {/* Intelligence Data Packs Card */}
      <div className="police-card" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--police-navy-dark)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Database size={16} />
              <span>Offline Forensic Intelligence Data Packs</span>
            </h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Release Version: <strong>{dataPacks?.datapack_version || '2026.09-AIRGAPPED'}</strong>
            </p>
          </div>
          <button
            onClick={handleReloadDataPacks}
            disabled={reloadingPacks}
            className="btn-police-secondary"
            style={{ fontSize: '0.75rem' }}
          >
            <RefreshCw size={13} className={reloadingPacks ? 'animate-spin' : ''} />
            <span>{reloadingPacks ? 'Reloading...' : 'Hot-Reload Intelligence'}</span>
          </button>
        </div>

        {packSuccess && (
          <div style={{ background: '#EFF6FF', border: '1px solid #BFDBFE', color: '#1E40AF', padding: '0.6rem 1rem', borderRadius: '4px', fontSize: '0.75rem', marginBottom: '0.75rem' }}>
            {packSuccess}
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem' }}>
          {dataPacks && Object.entries(dataPacks.packages || {}).map(([k, p]) => (
            <div key={k} style={{ background: '#F8FAFC', border: '1px solid var(--border-light)', borderRadius: '4px', padding: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <strong style={{ fontSize: '0.75rem', color: 'var(--police-navy)' }}>{p.filename}</strong>
                <span className="badge-emerald" style={{ fontSize: '0.65rem' }}>{p.status}</span>
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-subtle)', marginTop: '0.25rem' }}>
                Size: {(p.file_size_bytes / 1024).toFixed(1)} KB
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Officers Registry Table */}
      <div className="police-card" style={{ padding: '1.25rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--police-navy-dark)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Users size={16} />
          <span>Registered Police Investigators & Clearance Levels</span>
        </h3>

        <table className="police-table">
          <thead>
            <tr>
              <th>Badge ID</th>
              <th>Officer Name</th>
              <th>Rank</th>
              <th>Police Station Assignment</th>
              <th>Clearance Level</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {officers.map((o) => (
              <tr key={o.id}>
                <td className="font-mono" style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--police-navy)' }}>
                  {o.badge_number}
                </td>
                <td style={{ fontWeight: 600 }}>{o.full_name}</td>
                <td>{o.rank}</td>
                <td>{o.police_station}</td>
                <td>
                  <span className={o.clearance_level === 'L3_ADMIN_DIRECTOR' ? 'badge-gold' : (o.clearance_level === 'L2_SENIOR_OFFICER' ? 'badge-navy' : 'badge-emerald')} style={{ fontSize: '0.7rem' }}>
                    {o.clearance_level.replace('_', ' ')}
                  </span>
                </td>
                <td>
                  <span className={o.is_active ? 'badge-emerald' : 'badge-crimson'} style={{ fontSize: '0.7rem' }}>
                    {o.is_active ? 'ACTIVE' : 'SUSPENDED'}
                  </span>
                </td>
                <td>
                  <button
                    onClick={() => handleToggleStatus(o.id, o.is_active)}
                    className="btn-police-secondary"
                    style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem' }}
                  >
                    {o.is_active ? 'Suspend' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Provision Officer Modal */}
      {showAddModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(15, 23, 42, 0.7)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '1rem'
        }}>
          <div style={{ background: '#FFFFFF', borderRadius: '8px', maxWidth: '480px', width: '100%', padding: '1.5rem', border: '1px solid var(--border-medium)' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--police-navy-dark)', marginBottom: '1rem' }}>
              Provision New Cyber Officer
            </h3>

            {provisionError && (
              <div style={{ background: '#FEE2E2', border: '1px solid #FCA5A5', color: '#991B1B', padding: '0.5rem', borderRadius: '4px', fontSize: '0.75rem', marginBottom: '1rem' }}>
                {provisionError}
              </div>
            )}

            <form onSubmit={handleProvisionOfficer} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, marginBottom: '0.25rem' }}>Badge Number</label>
                <input
                  type="text" required value={newBadge} onChange={e => setNewBadge(e.target.value)}
                  placeholder="e.g. IND-CYBER-5521"
                  style={{ width: '100%', padding: '0.45rem', border: '1px solid var(--border-medium)', borderRadius: '4px', fontSize: '0.8125rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, marginBottom: '0.25rem' }}>Full Name</label>
                <input
                  type="text" required value={newFullName} onChange={e => setNewFullName(e.target.value)}
                  placeholder="e.g. Insp. Rajesh Sharma"
                  style={{ width: '100%', padding: '0.45rem', border: '1px solid var(--border-medium)', borderRadius: '4px', fontSize: '0.8125rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, marginBottom: '0.25rem' }}>Clearance Level</label>
                <select
                  value={newClearance} onChange={e => setNewClearance(e.target.value)}
                  style={{ width: '100%', padding: '0.45rem', border: '1px solid var(--border-medium)', borderRadius: '4px', fontSize: '0.8125rem' }}
                >
                  <option value="L1_INVESTIGATOR">L1_INVESTIGATOR (Case Investigator)</option>
                  <option value="L2_SENIOR_OFFICER">L2_SENIOR_OFFICER (Sign-Off Authority)</option>
                  <option value="L3_ADMIN_DIRECTOR">L3_ADMIN_DIRECTOR (Station Commander)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, marginBottom: '0.25rem' }}>Initial Password</label>
                <input
                  type="password" required value={newPassword} onChange={e => setNewPassword(e.target.value)}
                  style={{ width: '100%', padding: '0.45rem', border: '1px solid var(--border-medium)', borderRadius: '4px', fontSize: '0.8125rem' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button type="button" onClick={() => setShowAddModal(false)} className="btn-police-secondary" style={{ fontSize: '0.8125rem' }}>
                  Cancel
                </button>
                <button type="submit" className="btn-police-primary" style={{ fontSize: '0.8125rem' }}>
                  Create Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminConsolePage;

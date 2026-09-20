import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Shield, Lock, User, Building, AlertOctagon, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { authApi } from '../services/api';

const LoginPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login, isAuthenticated } = useAuth();

  const [badgeNumber, setBadgeNumber] = useState('IND-CYBER-8841');
  const [password, setPassword] = useState('Police@Secure2026');
  const [station, setStation] = useState('Special Cyber Operations, State Crime Branch');
  const [stations, setStations] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    const fetchStations = async () => {
      try {
        const res = await authApi.getStations();
        setStations(res.data);
      } catch (err) {
        console.error("Failed to load police stations:", err);
      }
    };
    fetchStations();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(badgeNumber, password, station);
      navigate('/');
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(180deg, #0A1E3F 0%, #0F2C59 50%, #1E3A8A 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1.5rem'
    }}>
      <div style={{
        background: '#FFFFFF',
        borderRadius: '8px',
        width: '100%',
        maxWidth: '480px',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
        overflow: 'hidden'
      }}>
        {/* Police Insignia Header */}
        <div style={{
          background: '#0F2C59',
          color: '#FFFFFF',
          padding: '1.75rem',
          textAlign: 'center',
          borderBottom: '3px solid #FCD34D'
        }}>
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            background: '#1E3A8A',
            border: '2px solid #FCD34D',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem auto',
            color: '#FCD34D'
          }}>
            <Shield size={32} />
          </div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '0.03em' }}>
            TraceLink Forensics
          </h1>
          <p style={{ fontSize: '0.8125rem', color: '#93C5FD', marginTop: '0.25rem' }}>
            Automated VASP Attribution & Blockchain Intelligence Terminal
          </p>
        </div>

        {/* Form Container */}
        <div style={{ padding: '2rem' }}>
          {searchParams.get('session_expired') && (
            <div className="statutory-banner" style={{ marginBottom: '1.25rem' }}>
              Your officer session has expired. Please re-authenticate to continue.
            </div>
          )}

          {error && (
            <div style={{
              background: '#FEE2E2',
              border: '1px solid #FCA5A5',
              color: '#991B1B',
              padding: '0.75rem',
              borderRadius: '4px',
              fontSize: '0.8125rem',
              marginBottom: '1.25rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <AlertOctagon size={16} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
                Service / Badge Number
              </label>
              <div style={{ position: 'relative' }}>
                <User size={16} color="#64748B" style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }} />
                <input
                  type="text"
                  required
                  value={badgeNumber}
                  onChange={(e) => setBadgeNumber(e.target.value)}
                  placeholder="e.g. IND-CYBER-8841"
                  style={{
                    width: '100%',
                    padding: '0.55rem 0.75rem 0.55rem 2.2rem',
                    border: '1px solid var(--border-medium)',
                    borderRadius: '4px',
                    fontSize: '0.875rem'
                  }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
                Official Police Password
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={16} color="#64748B" style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }} />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  style={{
                    width: '100%',
                    padding: '0.55rem 0.75rem 0.55rem 2.2rem',
                    border: '1px solid var(--border-medium)',
                    borderRadius: '4px',
                    fontSize: '0.875rem'
                  }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
                Assigned Cyber Unit / Station
              </label>
              <div style={{ position: 'relative' }}>
                <Building size={16} color="#64748B" style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }} />
                <select
                  value={station}
                  onChange={(e) => setStation(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.55rem 0.75rem 0.55rem 2.2rem',
                    border: '1px solid var(--border-medium)',
                    borderRadius: '4px',
                    fontSize: '0.875rem',
                    background: '#FFFFFF'
                  }}
                >
                  {stations.map((st, i) => (
                    <option key={i} value={st}>{st}</option>
                  ))}
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-police-primary"
              style={{
                width: '100%',
                justifyContent: 'center',
                padding: '0.75rem',
                fontSize: '0.9375rem',
                marginTop: '0.5rem'
              }}
            >
              {loading ? 'Authenticating with Directorate...' : 'Verify Credentials & Enter Workstation'}
            </button>
          </form>

          {/* Quick Demo Fill Helper */}
          <div style={{ marginTop: '1.25rem', padding: '0.75rem', background: '#F8FAFC', border: '1px dashed var(--border-medium)', borderRadius: '4px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            <strong>Default Officer Credentials (Air-Gapped Lab):</strong><br />
            Badge: <code className="font-mono" style={{ color: '#0F2C59' }}>IND-CYBER-8841</code> | Password: <code className="font-mono" style={{ color: '#0F2C59' }}>Police@Secure2026</code>
          </div>

          {/* Statutory Caveat Warning */}
          <div style={{
            marginTop: '1.5rem',
            borderTop: '1px solid var(--border-light)',
            paddingTop: '1rem',
            fontSize: '0.6875rem',
            color: '#64748B',
            textAlign: 'center',
            lineHeight: 1.4
          }}>
            <strong>RESTRICTED LAW ENFORCEMENT ACCESS</strong><br />
            Unauthorized access is strictly prohibited and punishable under Section 66 and Section 70 of the Information Technology Act, 2000. All activities are recorded with IP, workstation ID, and cryptographic timestamp.
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;

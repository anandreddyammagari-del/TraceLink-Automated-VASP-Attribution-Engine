import React, { useState, useEffect } from 'react';
import { Shield, Maximize, Minimize, LogOut, User, Building, Lock } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

const Navbar = () => {
  const { officer, logout, clearanceLevel } = useAuth();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [timeStr, setTimeStr] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString('en-IN', { hour12: false }) + ' IST');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().then(() => setIsFullscreen(true)).catch(err => {
        console.error("Fullscreen request failed:", err);
      });
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen().then(() => setIsFullscreen(false));
      }
    }
  };

  const getClearanceBadgeClass = (lvl) => {
    switch (lvl) {
      case 'L3_ADMIN_DIRECTOR':
        return 'badge-gold';
      case 'L2_SENIOR_OFFICER':
        return 'badge-navy';
      default:
        return 'badge-emerald';
    }
  };

  return (
    <header style={{
      background: 'var(--police-navy-dark)',
      color: '#FFFFFF',
      borderBottom: '2px solid #0A1E3F',
      padding: '0.6rem 1.5rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between'
    }}>
      {/* Brand & Police Unit */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '50%',
          background: '#1E3A8A',
          border: '2px solid #FCD34D',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#FCD34D'
        }}>
          <Shield size={22} />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <h1 style={{ fontSize: '1.125rem', fontWeight: 700, letterSpacing: '0.02em' }}>TraceLink</h1>
            <span style={{
              fontSize: '0.65rem',
              fontWeight: 700,
              background: '#DC2626',
              color: '#FFFFFF',
              padding: '0.1rem 0.4rem',
              borderRadius: '3px',
              textTransform: 'uppercase'
            }}>
              Forensics
            </span>
          </div>
          <p style={{ fontSize: '0.75rem', color: '#93C5FD' }}>
            State Cyber Police & Financial Crime Intelligence Terminal
          </p>
        </div>
      </div>

      {/* Center Station & Time */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', fontSize: '0.8rem', color: '#E2E8F0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <Building size={14} color="#93C5FD" />
          <span>{officer?.police_station || 'State Cyber Cell'}</span>
        </div>
        <div style={{
          background: 'rgba(255, 255, 255, 0.1)',
          padding: '0.2rem 0.6rem',
          borderRadius: '4px',
          fontFamily: 'JetBrains Mono',
          fontSize: '0.75rem'
        }}>
          {timeStr}
        </div>
      </div>

      {/* Officer Credentials, Fullscreen & Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {officer && (
          <div style={{ textAlign: 'right', marginRight: '0.5rem' }}>
            <div style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
              {officer.rank} {officer.badge_number}
            </div>
            <div style={{ marginTop: '0.15rem' }}>
              <span className={getClearanceBadgeClass(clearanceLevel)} style={{
                fontSize: '0.65rem',
                fontWeight: 700,
                padding: '0.1rem 0.4rem',
                borderRadius: '3px',
                textTransform: 'uppercase'
              }}>
                {clearanceLevel.replace('_', ' ')}
              </span>
            </div>
          </div>
        )}

        {/* Fullscreen Workstation Toggle */}
        <button
          onClick={toggleFullscreen}
          title={isFullscreen ? "Exit Fullscreen Kiosk" : "Expand Fullscreen Workstation (F11)"}
          className="btn-police-secondary"
          style={{ padding: '0.4rem 0.6rem', fontSize: '0.75rem', color: 'var(--police-navy-dark)' }}
        >
          {isFullscreen ? <Minimize size={16} /> : <Maximize size={16} />}
          <span>{isFullscreen ? "Exit Kiosk" : "Fullscreen Kiosk"}</span>
        </button>

        {/* Logout */}
        <button
          onClick={logout}
          title="Secure Logout from Terminal"
          className="btn-police-secondary"
          style={{ padding: '0.4rem 0.6rem', fontSize: '0.75rem', color: '#991B1B', borderColor: '#FCA5A5' }}
        >
          <LogOut size={16} />
          <span>Sign Out</span>
        </button>
      </div>
    </header>
  );
};

export default Navbar;

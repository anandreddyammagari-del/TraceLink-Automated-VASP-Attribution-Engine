import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Network, FolderGit2, FileText, History, ShieldAlert, ShieldCheck, Key } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import Navbar from './Navbar';

const Layout = ({ children }) => {
  const { clearanceLevel } = useAuth();
  const navItems = [
    { to: '/', label: 'Master Transaction Ledger', icon: LayoutDashboard },
    { to: '/cases', label: 'Registered Cases (FIRs)', icon: FolderGit2 },
    { to: '/graph', label: 'Forensic Graph Visualizer', icon: Network },
    { to: '/notices', label: 'BNSS Section 94 Notices', icon: FileText },
    { to: '/audit', label: 'Tamper-Evident Audit Trail', icon: History },
  ];

  if (clearanceLevel === 'L3_ADMIN_DIRECTOR') {
    navItems.push({ to: '/admin', label: 'L3 Admin Console', icon: Key });
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', background: 'var(--bg-secondary)' }}>
      <Navbar />

      {/* Sub-header Navigation Bar */}
      <nav style={{
        background: '#FFFFFF',
        borderBottom: '1px solid var(--border-medium)',
        padding: '0 1.5rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 1px 2px rgba(0,0,0,0.03)'
      }}>
        <div style={{ display: 'flex', gap: '0.25rem' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                style={({ isActive }) => ({
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.75rem 1rem',
                  fontSize: '0.8125rem',
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? 'var(--police-navy-dark)' : 'var(--text-muted)',
                  borderBottom: isActive ? '3px solid var(--police-navy)' : '3px solid transparent',
                  textDecoration: 'none',
                  transition: 'all 0.1s ease',
                  background: isActive ? '#F1F5F9' : 'transparent'
                })}
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </div>

        {/* Operational Status Pill */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: '#166534', fontWeight: 600 }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: '#16A34A',
            display: 'inline-block'
          }}></span>
          <span>AIR-GAPPED LAB MODE ACTIVE</span>
        </div>
      </nav>

      {/* Statutory Advisory Notice */}
      <div style={{
        background: '#FEF3C7',
        borderBottom: '1px solid #FCD34D',
        padding: '0.35rem 1.5rem',
        fontSize: '0.75rem',
        color: '#92400E',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ShieldAlert size={14} color="#D97706" />
          <span>
            <strong>CONFIDENTIAL FORENSIC SYSTEM:</strong> Access restricted to authorized Investigating Officers. All actions cryptographically logged under Section 63 of Bharatiya Sakshya Adhiniyam (BSA), 2023.
          </span>
        </div>
        <span style={{ fontStyle: 'italic', fontSize: '0.7rem' }}>
          External SAHYOG/Portal submission disabled. Local archival only.
        </span>
      </div>

      {/* Main Content Viewport */}
      <main style={{ flex: 1, padding: '1.5rem', maxWidth: '1600px', width: '100%', margin: '0 auto' }}>
        {children}
      </main>
    </div>
  );
};

export default Layout;

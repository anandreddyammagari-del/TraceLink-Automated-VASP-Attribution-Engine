import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FolderGit2, Plus, Search, Filter } from 'lucide-react';
import CaseCard from '../components/CaseCard';
import { casesApi } from '../services/api';

const CasesListPage = () => {
  const navigate = useNavigate();
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    const fetchCases = async () => {
      try {
        const res = await casesApi.getCases();
        setCases(res.data);
      } catch (err) {
        console.error("Failed to load cases:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchCases();
  }, []);

  const filteredCases = cases.filter(c =>
    c.fir_number.toLowerCase().includes(search.toLowerCase()) ||
    c.title.toLowerCase().includes(search.toLowerCase()) ||
    c.police_station.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
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
            Registered Cyber Crime Cases (FIR Directory)
          </h2>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
            Official FIR repository with linked cryptocurrency suspect networks and court evidentiary records.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ position: 'relative' }}>
            <Search size={16} color="#64748B" style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Search FIR number, station..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                padding: '0.45rem 0.75rem 0.45rem 2rem',
                fontSize: '0.8125rem',
                border: '1px solid var(--border-medium)',
                borderRadius: '4px',
                width: '260px'
              }}
            />
          </div>
        </div>
      </div>

      {/* Grid of Cases */}
      {loading ? (
        <div className="police-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading registered FIR cases...
        </div>
      ) : filteredCases.length === 0 ? (
        <div className="police-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          No cases found matching search criteria.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.25rem' }}>
          {filteredCases.map(c => (
            <CaseCard key={c.id} caseItem={c} />
          ))}
        </div>
      )}
    </div>
  );
};

export default CasesListPage;

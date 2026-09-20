import React, { useState, useRef } from 'react';
import { Upload, X, FileText, CheckCircle2, AlertOctagon, RefreshCw, FileCheck } from 'lucide-react';
import api from '../services/api';

const DatasetUploadModal = ({ isOpen, onClose, onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  };

  const handleFileSelected = (selected) => {
    const ext = selected.name.toLowerCase();
    if (!ext.endsWith('.csv') && !ext.endsWith('.json')) {
      setError('Unsupported file type. Please upload a .CSV or .JSON transaction dataset.');
      setFile(null);
      return;
    }
    setFile(selected);
    setError('');
    setResult(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post('/transactions/upload-dataset', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(res.data);
      if (onUploadSuccess) onUploadSuccess(res.data);
    } catch (err) {
      console.error("Upload error:", err);
      setError(err.response?.data?.detail || 'Failed to parse and ingest dataset.');
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setResult(null);
    setError('');
    onClose();
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(15, 23, 42, 0.65)',
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
        maxWidth: '560px',
        border: '1px solid var(--border-medium)',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)',
        overflow: 'hidden'
      }}>
        {/* Modal Header */}
        <div style={{
          background: 'var(--police-navy-dark)',
          color: '#FFFFFF',
          padding: '1rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Upload size={18} color="#93C5FD" />
            <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>
              Ingest Officer-Provided Transaction Dataset
            </h3>
          </div>
          <button
            onClick={handleClose}
            style={{ background: 'transparent', border: 'none', color: '#FFFFFF', cursor: 'pointer' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '1.5rem' }}>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
            Upload raw transaction logs or suspect case files in <strong>CSV</strong> or <strong>JSON</strong> format. The engine automatically normalizes columns, validates addresses, eliminates duplicates, and integrates records directly into the master ledger and graph topology.
          </p>

          {/* Drag & Drop Area */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: dragActive ? '2px dashed #2563EB' : '2px dashed var(--border-medium)',
              background: dragActive ? '#EFF6FF' : '#F8FAFC',
              borderRadius: '6px',
              padding: '2rem 1.5rem',
              textAlign: 'center',
              cursor: 'pointer',
              marginBottom: '1rem',
              transition: 'all 0.15s ease'
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.json"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{
                width: '42px',
                height: '42px',
                borderRadius: '50%',
                background: '#E2E8F0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--police-navy)'
              }}>
                <FileText size={22} />
              </div>
              <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-main)' }}>
                {file ? file.name : "Click to select or drag & drop file"}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
                {file ? `${(file.size / 1024).toFixed(1)} KB` : "Supports standard CSV (tx_hash, from, to, amount) or JSON arrays"}
              </div>
            </div>
          </div>

          {/* Error Banner */}
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

          {/* Success Ingestion Result */}
          {result && (
            <div style={{
              background: '#DCFCE7',
              border: '1px solid #86EFAC',
              color: '#166534',
              padding: '1rem',
              borderRadius: '4px',
              fontSize: '0.8125rem',
              marginBottom: '1rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                <CheckCircle2 size={16} />
                <span>Dataset Ingestion Complete</span>
              </div>
              <ul style={{ paddingLeft: '1.25rem', fontSize: '0.78rem', lineHeight: 1.5 }}>
                <li>Total rows evaluated: <strong>{result.summary?.total_rows_received || 0}</strong></li>
                <li>New transactions committed: <strong>{result.summary?.inserted || 0}</strong></li>
                <li>Existing duplicates skipped: <strong>{result.summary?.skipped_duplicates || 0}</strong></li>
                {result.summary?.errors?.length > 0 && (
                  <li style={{ color: '#991B1B' }}>Rows with errors: <strong>{result.summary.errors.length}</strong></li>
                )}
              </ul>
            </div>
          )}

          {/* Action Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.25rem' }}>
            <button
              onClick={handleClose}
              className="btn-police-secondary"
              style={{ fontSize: '0.8125rem' }}
            >
              {result ? 'Done' : 'Cancel'}
            </button>
            {!result && (
              <button
                onClick={handleUpload}
                disabled={!file || uploading}
                className="btn-police-primary"
                style={{ fontSize: '0.8125rem' }}
              >
                {uploading ? (
                  <>
                    <RefreshCw size={14} className="animate-spin" />
                    <span>Parsing & Committing...</span>
                  </>
                ) : (
                  <>
                    <FileCheck size={14} />
                    <span>Commit to Master Ledger</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DatasetUploadModal;

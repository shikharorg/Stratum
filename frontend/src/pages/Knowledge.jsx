import { useState, useEffect, useRef } from 'react';
import { colors, typography } from '../theme';
import SectionHeader from '../components/SectionHeader';
import apiClient from '../api/client';

const COL = { name: '1fr', type: '90px', status: '110px', chunks: '70px', size: '80px', uploaded: '80px' };

function formatSize(bytes) {
  if (bytes == null) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

function relativeTime(isoString) {
  const secs = Math.floor((Date.now() - new Date(isoString).getTime()) / 1000);
  if (secs < 60) return 'just now';
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
  return `${Math.floor(secs / 86400)}d ago`;
}

function detectSourceType(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  if (ext === 'md') return 'markdown';
  if (ext === 'pdf') return 'pdf';
  if (ext === 'json') return 'json';
  if (ext === 'txt') return 'text';
  return 'text';
}

function PulsingDot() {
  const [scale, setScale] = useState(1);
  useEffect(() => {
    const interval = setInterval(() => setScale(s => s === 1 ? 1.6 : 1), 900);
    return () => clearInterval(interval);
  }, []);
  return (
    <div style={{
      width: '6px',
      height: '6px',
      borderRadius: '50%',
      backgroundColor: colors.running,
      flexShrink: 0,
      transform: `scale(${scale})`,
      transition: 'transform 0.4s ease',
    }} />
  );
}

function DocStatus({ status }) {
  if (status === 'completed') {
    return (
      <span style={{ fontFamily: typography.fontUI, fontSize: typography.sizes.sm, color: colors.textMuted }}>
        Indexed
      </span>
    );
  }
  if (status === 'processing' || status === 'pending') {
    return (
      <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
        <PulsingDot />
        <span style={{ fontFamily: typography.fontUI, fontSize: typography.sizes.sm, color: colors.text }}>
          Processing
        </span>
      </div>
    );
  }
  if (status === 'failed') {
    return (
      <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
        <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: colors.error, flexShrink: 0 }} />
        <span style={{ fontFamily: typography.fontUI, fontSize: typography.sizes.sm, color: colors.error }}>
          Failed
        </span>
      </div>
    );
  }
  return null;
}

function DocRow({ doc, isLast }) {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'grid',
        gridTemplateColumns: `${COL.name} ${COL.type} ${COL.status} ${COL.chunks} ${COL.size} ${COL.uploaded}`,
        alignItems: 'center',
        padding: '10px 12px',
        backgroundColor: hovered ? colors.surfaceHover : 'transparent',
        borderBottom: isLast ? 'none' : `1px solid ${colors.borderSubtle}`,
        transition: 'background-color 0.15s ease',
      }}
    >
      <span style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.base,
        color: colors.text,
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        paddingRight: '12px',
      }}>
        {doc.name}
      </span>
      <span style={{ fontFamily: typography.fontUI, fontSize: typography.sizes.sm, color: colors.textMuted }}>
        {doc.source_type}
      </span>
      <span>
        <DocStatus status={doc.status} />
      </span>
      <span style={{ fontFamily: typography.fontMono, fontSize: typography.sizes.sm, color: colors.textSecondary }}>
        {doc.chunk_count ?? '—'}
      </span>
      <span style={{ fontFamily: typography.fontMono, fontSize: typography.sizes.sm, color: colors.textSecondary }}>
        {formatSize(doc.file_size)}
      </span>
      <span style={{ fontFamily: typography.fontUI, fontSize: typography.sizes.sm, color: colors.textMuted }}>
        {relativeTime(doc.created_at)}
      </span>
    </div>
  );
}

function UploadArea({ onFile, uploading, uploadError, dragOver, onDragOver, onDragLeave, onDrop }) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      onClick={onFile}
      style={{
        border: `1px dashed ${dragOver || hovered ? colors.textMuted : colors.border}`,
        borderRadius: '6px',
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '6px',
        height: '80px',
        cursor: 'pointer',
        transition: 'border-color 0.15s ease',
        marginBottom: '32px',
      }}
    >
      {uploading ? (
        <span style={{ fontFamily: typography.fontUI, fontSize: typography.sizes.base, color: colors.textMuted }}>
          Uploading...
        </span>
      ) : uploadError ? (
        <span style={{ fontFamily: typography.fontUI, fontSize: typography.sizes.sm, color: colors.error }}>
          {uploadError}
        </span>
      ) : (
        <>
          <span style={{ fontFamily: typography.fontUI, fontSize: typography.sizes.base, color: colors.textSecondary }}>
            Drop files here or click to upload
          </span>
          <span style={{ fontFamily: typography.fontUI, fontSize: typography.sizes.xs, color: colors.textMuted }}>
            Markdown, PDF, JSON, plain text
          </span>
        </>
      )}
    </div>
  );
}

export default function Knowledge() {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploadHovered, setUploadHovered] = useState(false);
  const fileInputRef = useRef(null);
  const pollRef = useRef(null);

  async function fetchDocuments() {
    try {
      const { data } = await apiClient.get('/api/v1/ingestion/documents');
      setDocuments(data.items ?? []);
      setError(null);
      return data.items ?? [];
    } catch {
      setError('Failed to load documents.');
      return [];
    }
  }

  function startPolling() {
    if (pollRef.current) return;
    pollRef.current = setInterval(async () => {
      const items = await fetchDocuments();
      const hasActive = items.some(d => d.status === 'pending' || d.status === 'processing');
      if (!hasActive) stopPolling();
    }, 5000);
  }

  function stopPolling() {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }

  useEffect(() => {
    fetchDocuments().then(items => {
      setIsLoading(false);
      const hasActive = items.some(d => d.status === 'pending' || d.status === 'processing');
      if (hasActive) startPolling();
    });
    return () => stopPolling();
  }, []);

  async function uploadFile(file) {
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_type', detectSourceType(file.name));
    try {
      await apiClient.post('/api/v1/ingestion/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const items = await fetchDocuments();
      const hasActive = items.some(d => d.status === 'pending' || d.status === 'processing');
      if (hasActive) startPolling();
    } catch {
      setUploadError('Upload failed. Please try again.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }

  function handleFileInputChange(e) {
    uploadFile(e.target.files?.[0]);
  }

  function handleUploadAreaClick() {
    fileInputRef.current?.click();
  }

  function handleDragOver(e) {
    e.preventDefault();
    setDragOver(true);
  }

  function handleDragLeave() {
    setDragOver(false);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    uploadFile(e.dataTransfer.files?.[0]);
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div style={{
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.xl,
          fontWeight: typography.weights.semibold,
          color: colors.text,
        }}>
          Knowledge
        </div>
        <button
          onMouseEnter={() => setUploadHovered(true)}
          onMouseLeave={() => setUploadHovered(false)}
          onClick={handleUploadAreaClick}
          style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.base,
            fontWeight: typography.weights.regular,
            color: uploadHovered ? colors.text : colors.textSecondary,
            backgroundColor: uploadHovered ? colors.surfaceHover : colors.surface,
            border: `1px solid ${colors.border}`,
            borderRadius: '5px',
            padding: '6px 14px',
            cursor: 'pointer',
            transition: 'color 0.15s ease, background-color 0.15s ease',
          }}
        >
          Upload
        </button>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".md,.pdf,.json,.txt"
        onChange={handleFileInputChange}
        style={{ display: 'none' }}
      />

      <UploadArea
        onFile={handleUploadAreaClick}
        uploading={uploading}
        uploadError={uploadError}
        dragOver={dragOver}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      />

      <div>
        <SectionHeader>Documents</SectionHeader>
        <div style={{
          border: `1px solid ${colors.border}`,
          borderRadius: '6px',
          overflow: 'hidden',
        }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: `${COL.name} ${COL.type} ${COL.status} ${COL.chunks} ${COL.size} ${COL.uploaded}`,
            padding: '8px 12px',
            borderBottom: `1px solid ${colors.border}`,
          }}>
            {['Name', 'Type', 'Status', 'Chunks', 'Size', 'Uploaded'].map(h => (
              <span key={h} style={{
                fontFamily: typography.fontMono,
                fontSize: typography.sizes.xs,
                color: colors.textMuted,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
              }}>
                {h}
              </span>
            ))}
          </div>

          {isLoading ? (
            <div style={{
              padding: '24px',
              textAlign: 'center',
              fontFamily: typography.fontUI,
              fontSize: typography.sizes.base,
              color: colors.textMuted,
            }}>
              Loading documents...
            </div>
          ) : error ? (
            <div style={{
              padding: '24px',
              textAlign: 'center',
              fontFamily: typography.fontUI,
              fontSize: typography.sizes.sm,
              color: colors.error,
            }}>
              {error}
            </div>
          ) : (
            documents.map((doc, i) => (
              <DocRow key={doc.id} doc={doc} isLast={i === documents.length - 1} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}

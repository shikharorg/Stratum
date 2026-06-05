import { useState, useEffect } from 'react';
import { colors, typography } from '../theme';
import SectionHeader from '../components/SectionHeader';
import { mockDocuments } from '../mock/data';

const documents = mockDocuments;

const COL = { name: '1fr', type: '90px', status: '110px', chunks: '70px', size: '80px', uploaded: '80px' };

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
  if (status === 'processing') {
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
        {doc.sourceType}
      </span>
      <span>
        <DocStatus status={doc.status} />
      </span>
      <span style={{ fontFamily: typography.fontMono, fontSize: typography.sizes.sm, color: colors.textSecondary }}>
        {doc.chunkCount ?? '—'}
      </span>
      <span style={{ fontFamily: typography.fontMono, fontSize: typography.sizes.sm, color: colors.textSecondary }}>
        {doc.fileSize}
      </span>
      <span style={{ fontFamily: typography.fontUI, fontSize: typography.sizes.sm, color: colors.textMuted }}>
        {doc.uploadedAt}
      </span>
    </div>
  );
}

function UploadArea() {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        border: `1px dashed ${hovered ? colors.textMuted : colors.border}`,
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
      <span style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.base,
        color: colors.textSecondary,
      }}>
        Drop files here or click to upload
      </span>
      <span style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.xs,
        color: colors.textMuted,
      }}>
        Markdown, PDF, JSON, plain text
      </span>
    </div>
  );
}

export default function Knowledge() {
  const [uploadHovered, setUploadHovered] = useState(false);

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

      <UploadArea />

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
          {documents.map((doc, i) => (
            <DocRow key={doc.id} doc={doc} isLast={i === documents.length - 1} />
          ))}
        </div>
      </div>
    </div>
  );
}

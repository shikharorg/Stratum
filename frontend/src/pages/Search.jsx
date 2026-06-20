import { useState } from 'react';
import { MarkdownHooks } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { colors, typography } from '../theme';
import apiClient from '../api/client';

function SectionLabel({ left, right }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: '12px',
    }}>
      <span style={{
        fontFamily: typography.fontMono,
        fontSize: typography.sizes.xs,
        color: colors.textMuted,
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
      }}>
        {left}
      </span>
      <span style={{
        fontFamily: typography.fontMono,
        fontSize: typography.sizes.xs,
        color: colors.textMuted,
      }}>
        {right}
      </span>
    </div>
  );
}

function SourceRow({ docId, name, sourceType, chunkCount, isFirst, isLast }) {
  return (
    <div style={{
      paddingTop: isFirst ? '0' : '12px',
      paddingBottom: '12px',
      borderBottom: isLast ? 'none' : `1px solid ${colors.borderSubtle}`,
    }}>
      <span style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.base,
        fontWeight: typography.weights.medium,
        color: colors.text,
      }}>
        {name}
      </span>
      <span style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.sm,
        color: colors.textMuted,
        margin: '0 6px',
      }}>
        ·
      </span>
      <span style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.sm,
        color: colors.textMuted,
      }}>
        {sourceType}
      </span>
      <span style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.sm,
        color: colors.textMuted,
        margin: '0 6px',
      }}>
        ·
      </span>
      <span style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.sm,
        color: colors.textMuted,
      }}>
        {chunkCount} {chunkCount === 1 ? 'chunk' : 'chunks'}
      </span>
    </div>
  );
}

export default function Search() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [docNames, setDocNames] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchHovered, setSearchHovered] = useState(false);
  const [inputFocused, setInputFocused] = useState(false);

  const hasResult = result !== null;
  const chunks = result?.result?.chunks ?? [];
  const rawAnswer = result?.result?.answer ?? '';
  const answer = rawAnswer.replace(/^```[\w]*\r?\n?/, '').replace(/\r?\n?```$/, '');
  const grounding = result?.result?.grounding_passed;
  const latency = result?.result?.latency_ms != null ? `${result.result.latency_ms}ms` : '';

  async function handleSearch() {
    if (!query.trim()) return;
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await apiClient.post('/api/v1/retrieval/retrieve', {
        query: query.trim(),
        top_k: 5,
        include_generation: true,
      });
      setResult(response.data);
      const chunks = response.data?.result?.chunks ?? [];
      const uniqueIds = [...new Set(chunks.map(c => c.document_id).filter(Boolean))];
      const entries = await Promise.all(
        uniqueIds.map(id =>
          apiClient.get(`/api/v1/ingestion/documents/${id}`)
            .then(r => [id, r.data.name])
            .catch(() => [id, `doc ${id.slice(0, 8)}`])
        )
      );
      setDocNames(Object.fromEntries(entries));
    } catch (err) {
      console.error(err);
      console.error(err.response?.data);
      setError(
        err.response?.data?.detail ||
        err.message ||
        'Search failed'
      );
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') handleSearch();
  }

  return (
    <div>
      <div style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.xl,
        fontWeight: typography.weights.semibold,
        color: colors.text,
        marginBottom: '24px',
      }}>
        Search
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setInputFocused(true)}
          onBlur={() => setInputFocused(false)}
          placeholder="Ask anything about your knowledge base..."
          style={{
            flex: 1,
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.base,
            color: colors.text,
            backgroundColor: colors.surface,
            border: `1px solid ${inputFocused ? colors.textMuted : colors.border}`,
            borderRadius: '6px',
            padding: '10px 16px',
            outline: 'none',
            transition: 'border-color 0.15s ease',
          }}
        />
        <button
          onClick={handleSearch}
          onMouseEnter={() => setSearchHovered(true)}
          onMouseLeave={() => setSearchHovered(false)}
          style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.base,
            fontWeight: typography.weights.regular,
            color: searchHovered ? colors.text : colors.textSecondary,
            backgroundColor: searchHovered ? colors.surfaceHover : colors.surface,
            border: `1px solid ${colors.border}`,
            borderRadius: '6px',
            padding: '10px 18px',
            cursor: 'pointer',
            whiteSpace: 'nowrap',
            transition: 'color 0.15s ease, background-color 0.15s ease',
          }}
        >
          Search
        </button>
      </div>

      {error && (
        <div style={{
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.sm,
          color: colors.error,
          marginTop: '8px',
        }}>
          {error}
        </div>
      )}

      {!hasResult && !isLoading && !error && (
        <div style={{
          textAlign: 'center',
          marginTop: '40px',
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.base,
          color: colors.textMuted,
        }}>
          Ask a question to search your knowledge base
        </div>
      )}

      {(hasResult || isLoading) && (
        <>
          <div className="scroll-dark" style={{
            backgroundColor: colors.surface,
            border: `1px solid ${colors.border}`,
            borderRadius: '6px',
            padding: '20px',
            marginTop: '20px',
            height: '55vh',
            overflowY: 'auto',
          }}>
            <SectionLabel left="Answer" right={latency} />
            {isLoading ? (
              <div style={{
                fontFamily: typography.fontUI,
                fontSize: typography.sizes.base,
                color: colors.textMuted,
                textAlign: 'center',
                marginTop: '40px',
              }}>
                Searching...
              </div>
            ) : (
              <>
                {grounding === false && (
                  <div style={{
                    fontFamily: typography.fontUI,
                    fontSize: typography.sizes.sm,
                    color: colors.warning,
                    marginBottom: '12px',
                  }}>
                    Response could not be fully grounded in retrieved sources.
                  </div>
                )}
                <div style={{ maxWidth: '680px', fontFamily: typography.fontUI }}>
                  <MarkdownHooks
                    remarkPlugins={[remarkGfm]}
                    components={{
                      h1: ({ children }) => <h1 style={{ fontFamily: typography.fontUI, fontSize: '14px', fontWeight: 500, color: '#1a1a1a', marginBottom: '8px', marginTop: '12px' }}>{children}</h1>,
                      h2: ({ children }) => <h2 style={{ fontFamily: typography.fontUI, fontSize: '14px', fontWeight: 500, color: '#1a1a1a', marginBottom: '8px', marginTop: '12px' }}>{children}</h2>,
                      h3: ({ children }) => <h3 style={{ fontFamily: typography.fontUI, fontSize: '14px', fontWeight: 500, color: '#1a1a1a', marginBottom: '6px', marginTop: '8px' }}>{children}</h3>,
                      p: ({ children }) => <p style={{ fontFamily: typography.fontUI, fontSize: '13px', lineHeight: '1.6', color: '#3a3a3a', marginBottom: '6px', marginTop: 0 }}>{children}</p>,
                      ul: ({ children }) => <ul style={{ paddingLeft: '18px', marginBottom: '6px', marginTop: 0 }}>{children}</ul>,
                      ol: ({ children }) => <ol style={{ paddingLeft: '18px', marginBottom: '6px', marginTop: 0 }}>{children}</ol>,
                      li: ({ children }) => <li style={{ fontFamily: typography.fontUI, fontSize: '13px', lineHeight: '1.8', color: '#3a3a3a', marginBottom: '2px' }}>{children}</li>,
                      strong: ({ children }) => <strong style={{ fontWeight: 500, color: '#1a1a1a' }}>{children}</strong>,
                      code: ({ children }) => <code style={{ fontFamily: typography.fontMono, fontSize: '12px', backgroundColor: colors.surfaceHover, padding: '1px 5px', borderRadius: '3px', color: colors.text }}>{children}</code>,
                      table: ({ children }) => <table style={{ borderCollapse: 'collapse', width: '100%', marginBottom: '8px', fontSize: '13px' }}>{children}</table>,
                      th: ({ children }) => <th style={{ fontFamily: typography.fontUI, border: `1px solid ${colors.border}`, padding: '6px 8px', textAlign: 'left', fontWeight: 500, fontSize: '13px', color: '#1a1a1a' }}>{children}</th>,
                      td: ({ children }) => <td style={{ fontFamily: typography.fontUI, border: `1px solid ${colors.border}`, padding: '6px 8px', fontSize: '13px', color: '#3a3a3a' }}>{children}</td>,
                    }}
                  >
                    {answer}
                  </MarkdownHooks>
                </div>
              </>
            )}
          </div>

          {!isLoading && hasResult && (
            <div className="scroll-dark" style={{
              backgroundColor: colors.surface,
              border: `1px solid ${colors.border}`,
              borderRadius: '6px',
              padding: '20px',
              marginTop: '12px',
              height: '28vh',
              overflowY: 'auto',
            }}>
              {(() => {
                const grouped = [];
                const seen = {};
                for (const chunk of chunks) {
                  const id = chunk.document_id;
                  if (!seen[id]) {
                    seen[id] = true;
                    grouped.push({ docId: id, sourceType: chunk.source_type, count: 1 });
                  } else {
                    grouped.find(g => g.docId === id).count++;
                  }
                }
                return (
                  <>
                    <SectionLabel left="Sources" right={`${grouped.length} documents`} />
                    {grouped.map((g, i) => (
                      <SourceRow
                        key={g.docId}
                        docId={g.docId}
                        name={docNames[g.docId] || `doc ${g.docId?.slice(0, 8) ?? ''}`}
                        sourceType={g.sourceType}
                        chunkCount={g.count}
                        isFirst={i === 0}
                        isLast={i === grouped.length - 1}
                      />
                    ))}
                  </>
                );
              })()}
            </div>
          )}
        </>
      )}
    </div>
  );
}

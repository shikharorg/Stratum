import { useState } from 'react';
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

function SourceRow({ chunk, isFirst, isLast }) {
  const source = chunk.source_url || `doc ${chunk.document_id?.slice(0, 8) ?? ''}`;
  const preview = chunk.text.replace(/^#+\s+[^\n]+\n+/, '').slice(0, 120);

  return (
    <div style={{
      paddingTop: isFirst ? '0' : '12px',
      paddingBottom: '12px',
      borderBottom: isLast ? 'none' : `1px solid ${colors.borderSubtle}`,
    }}>
      <div style={{ marginBottom: '2px' }}>
        <span style={{
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.base,
          fontWeight: typography.weights.medium,
          color: colors.text,
        }}>
          {source}
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
          {chunk.source_type}
        </span>
      </div>
      <div style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.sm,
        color: colors.textSecondary,
        lineHeight: 1.5,
      }}>
        {preview}
      </div>
    </div>
  );
}

export default function Search() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchHovered, setSearchHovered] = useState(false);
  const [inputFocused, setInputFocused] = useState(false);

  const hasResult = result !== null;
  const chunks = result?.result?.chunks ?? [];
  const answer = result?.result?.answer ?? '';
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
                <div style={{
                  fontFamily: typography.fontUI,
                  fontSize: typography.sizes.lg,
                  color: colors.text,
                  lineHeight: 1.8,
                  maxWidth: '680px',
                }}>
                  {answer}
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
              <SectionLabel left="Sources" right={`${chunks.length} results`} />
              {chunks.map((chunk, i) => (
                <SourceRow
                  key={chunk.chunk_id ?? i}
                  chunk={chunk}
                  isFirst={i === 0}
                  isLast={i === chunks.length - 1}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

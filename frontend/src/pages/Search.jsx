import { useState } from 'react';
import { colors, typography } from '../theme';
import { mockSearchResult } from '../mock/data';

const MOCK_RESULT = mockSearchResult;

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

function SourceRow({ chunk, isLast }) {
  const preview = chunk.text.replace(/^#+\s+[^\n]+\n+/, '').slice(0, 120);

  return (
    <div style={{
      paddingTop: '12px',
      paddingBottom: '12px',
      borderBottom: isLast ? 'none' : `1px solid ${colors.borderSubtle}`,
    }}>
      <div style={{ marginBottom: '4px' }}>
        <span style={{
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.base,
          fontWeight: typography.weights.medium,
          color: colors.text,
        }}>
          {chunk.source}
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
          {chunk.sourceType}
        </span>
      </div>
      <div style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.sm,
        color: colors.textSecondary,
        lineHeight: 1.6,
      }}>
        {preview}
      </div>
    </div>
  );
}

export default function Search() {
  const [inputValue, setInputValue] = useState(MOCK_RESULT.query);
  const [result, setResult] = useState(MOCK_RESULT);
  const [searchHovered, setSearchHovered] = useState(false);
  const [inputFocused, setInputFocused] = useState(false);

  const hasResult = result !== null;

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
          value={inputValue}
          onChange={e => setInputValue(e.target.value)}
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

      {!hasResult && (
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

      {hasResult && (
        <>
          <div style={{ marginTop: '24px' }}>
            <SectionLabel left="Answer" right={result.latency} />
            <div style={{ maxHeight: '460px', overflowY: 'auto', paddingRight: '8px' }}>
              <div style={{
                fontFamily: typography.fontUI,
                fontSize: typography.sizes.lg,
                color: colors.text,
                lineHeight: 1.8,
                maxWidth: '680px',
              }}>
                {result.answer}
              </div>
            </div>
          </div>

          <div style={{ borderTop: `1px solid ${colors.borderSubtle}`, marginTop: '24px' }} />

          <div style={{ marginTop: '16px' }}>
            <SectionLabel
              left="Sources"
              right={`${result.chunks.length} results`}
            />
            <div style={{ maxHeight: '280px', overflowY: 'auto' }}>
              {result.chunks.map((chunk, i) => (
                <SourceRow key={i} chunk={chunk} isLast={i === result.chunks.length - 1} />
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

import { useState } from 'react';
import { ChevronRight } from 'lucide-react';
import { colors, typography } from '../theme';

const events = [
  { dotColor: colors.success, text: 'test_doc.md indexed', secondary: null, time: '2m ago', textColor: colors.text },
  { dotColor: colors.textMuted, text: 'Search completed', secondary: '"What is Stratum?"', time: '5m ago', textColor: colors.text },
  { dotColor: colors.textMuted, text: 'RAG Workflow completed', secondary: null, time: '12m ago', textColor: colors.text },
  { dotColor: colors.textMuted, text: 'Slack synchronized', secondary: null, time: '1h ago', textColor: colors.text },
  { dotColor: colors.error, text: 'RAG Workflow failed', secondary: null, time: '3h ago', textColor: colors.error },
];

function EventRow({ event, isLast }) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 0',
        borderBottom: isLast ? 'none' : `1px solid ${colors.borderSubtle}`,
        cursor: 'pointer',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
        <div style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: event.dotColor,
          flexShrink: 0,
        }} />
        <span style={{
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.base,
          color: event.textColor,
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}>
          {event.text}
        </span>
        {event.secondary && (
          <span style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.base,
            color: colors.textMuted,
            fontStyle: 'italic',
            whiteSpace: 'nowrap',
          }}>
            {event.secondary}
          </span>
        )}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0, marginLeft: '16px' }}>
        <span style={{
          fontFamily: typography.fontMono,
          fontSize: typography.sizes.sm,
          color: colors.textMuted,
        }}>
          {event.time}
        </span>
        <ChevronRight size={13} color={hovered ? colors.textSecondary : colors.textMuted} />
      </div>
    </div>
  );
}

export default function EventList() {
  const [viewAllHovered, setViewAllHovered] = useState(false);

  return (
    <div>
      {events.map((event, i) => (
        <EventRow key={i} event={event} isLast={i === events.length - 1} />
      ))}
      <div style={{ marginTop: '16px' }}>
        <span
          onMouseEnter={() => setViewAllHovered(true)}
          onMouseLeave={() => setViewAllHovered(false)}
          style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.base,
            color: viewAllHovered ? colors.textSecondary : colors.textMuted,
            cursor: 'pointer',
            transition: 'color 0.15s ease',
          }}
        >
          View all activity →
        </span>
      </div>
    </div>
  );
}

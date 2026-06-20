import { useState } from 'react';
import { ChevronRight } from 'lucide-react';
import { colors, typography } from '../theme';

function textColorFor(status) {
  return status === 'error' ? colors.error : colors.text;
}

function EventRow({ event, isLast }) {
  const [hovered, setHovered] = useState(false);
  const textColor = textColorFor(event.status);

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
        <span style={{
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.base,
          color: textColor,
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}>
          {event.primary}
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

export default function EventList({ events }) {
  const [viewAllHovered, setViewAllHovered] = useState(false);

  return (
    <div>
      {events.map((event, i) => (
        <EventRow key={event.id} event={event} isLast={i === events.length - 1} />
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

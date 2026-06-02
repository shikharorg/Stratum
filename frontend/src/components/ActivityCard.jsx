import { useState, useEffect } from 'react';
import { ChevronRight } from 'lucide-react';
import { colors, typography } from '../theme';

function PulsingDot() {
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const interval = setInterval(() => {
      setScale(s => s === 1 ? 1.6 : 1);
    }, 900);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{
      width: '8px',
      height: '8px',
      borderRadius: '50%',
      backgroundColor: colors.running,
      flexShrink: 0,
      transform: `scale(${scale})`,
      transition: 'transform 0.4s ease',
    }} />
  );
}

export default function ActivityCard({ name, startedAgo }) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        backgroundColor: hovered ? colors.surfaceHover : colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: '6px',
        cursor: 'pointer',
        transition: 'background-color 0.15s ease',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <PulsingDot />
        <div>
          <div style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.base,
            fontWeight: typography.weights.medium,
            color: colors.text,
          }}>
            {name}
          </div>
          <div style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.sm,
            color: colors.textMuted,
            marginTop: '2px',
          }}>
            started {startedAgo} ago
          </div>
        </div>
      </div>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.sm,
        fontWeight: typography.weights.medium,
        color: colors.textSecondary,
      }}>
        View
        <ChevronRight size={14} color={colors.textMuted} />
      </div>
    </div>
  );
}

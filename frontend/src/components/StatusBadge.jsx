import { useState, useEffect } from 'react';
import { colors, typography } from '../theme';

const DOT_COLOR = {
  completed: colors.success,
  failed: colors.error,
  running: colors.running,
  pending: colors.textMuted,
};

const LABEL = {
  completed: 'Completed',
  failed: 'Failed',
  running: 'Running',
  pending: 'Pending',
};

function PulsingDot({ color }) {
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const interval = setInterval(() => {
      setScale(s => s === 1 ? 1.6 : 1);
    }, 900);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{
      width: '6px',
      height: '6px',
      borderRadius: '50%',
      backgroundColor: color,
      flexShrink: 0,
      transform: `scale(${scale})`,
      transition: 'transform 0.4s ease',
    }} />
  );
}

export default function StatusBadge({ status }) {
  const dotColor = DOT_COLOR[status] ?? colors.textMuted;
  const label = LABEL[status] ?? status;
  const textColor = status === 'failed' ? colors.error : colors.textSecondary;

  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '6px',
    }}>
      {status === 'running' ? (
        <PulsingDot color={dotColor} />
      ) : (
        <div style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: dotColor,
          flexShrink: 0,
        }} />
      )}
      <span style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.sm,
        color: textColor,
      }}>
        {label}
      </span>
    </div>
  );
}

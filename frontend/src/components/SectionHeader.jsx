import { colors, typography } from '../theme';

export default function SectionHeader({ children }) {
  return (
    <div style={{
      fontFamily: typography.fontMono,
      fontSize: '10px',
      fontWeight: typography.weights.regular,
      color: colors.textMuted,
      textTransform: 'uppercase',
      letterSpacing: '0.12em',
      marginBottom: '12px',
    }}>
      {children}
    </div>
  );
}

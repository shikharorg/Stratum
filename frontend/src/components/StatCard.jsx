import { colors, typography } from '../theme';

export default function StatCard({ value, label, delta, deltaColor }) {
  return (
    <div style={{
      flex: 1,
      backgroundColor: colors.surface,
      border: `1px solid ${colors.border}`,
      borderRadius: '6px',
      padding: '20px 24px',
    }}>
      <div style={{
        fontFamily: typography.fontMono,
        fontSize: typography.sizes.xxl,
        fontWeight: typography.weights.medium,
        color: colors.text,
        lineHeight: 1,
        marginBottom: '6px',
      }}>
        {value}
      </div>
      <div style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.base,
        fontWeight: typography.weights.regular,
        color: colors.textSecondary,
        marginBottom: '8px',
      }}>
        {label}
      </div>
      <div style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.sm,
        fontWeight: typography.weights.medium,
        color: deltaColor || colors.textMuted,
      }}>
        {delta}
      </div>
    </div>
  );
}

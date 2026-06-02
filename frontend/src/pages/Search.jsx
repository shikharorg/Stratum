import { colors, typography } from '../theme';

export default function Search() {
  return (
    <div style={{
      fontFamily: typography.fontUI,
      fontSize: typography.sizes.xl,
      fontWeight: typography.weights.semibold,
      color: colors.text,
    }}>
      Search
    </div>
  );
}

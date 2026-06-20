import { typography } from '../theme';

const PILL = {
  completed: { bg: '#eef4e8', color: '#3b6d11', label: 'Completed' },
  failed:    { bg: '#fceaea', color: '#a32d2d', label: 'Failed' },
  running:   { bg: '#e8f0fb', color: '#185FA5', label: 'Running' },
  pending:   { bg: '#f3f2f0', color: '#5f5e5a', label: 'Pending' },
};

export default function StatusBadge({ status }) {
  const pill = PILL[status] ?? PILL.pending;
  return (
    <span style={{
      display: 'inline-block',
      backgroundColor: pill.bg,
      color: pill.color,
      fontFamily: typography.fontUI,
      fontSize: '12px',
      fontWeight: 500,
      padding: '2px 8px',
      borderRadius: '999px',
      whiteSpace: 'nowrap',
    }}>
      {pill.label}
    </span>
  );
}

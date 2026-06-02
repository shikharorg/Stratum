import { ChevronRight } from 'lucide-react';
import { useState } from 'react';
import { colors, typography } from '../theme';
import SectionHeader from '../components/SectionHeader';
import StatCard from '../components/StatCard';
import ActivityCard from '../components/ActivityCard';
import EventList from '../components/EventList';

const attentionItems = [
  '2 documents stuck in processing',
  'Jira hasn\'t synced in 6 hours',
];

function AttentionCard({ text }) {
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
        borderLeft: `4px solid ${colors.warning}`,
        backgroundColor: hovered ? colors.surfaceHover : colors.surface,
        border: `1px solid ${colors.border}`,
        borderLeftWidth: '4px',
        borderLeftColor: colors.warning,
        borderRadius: '6px',
        cursor: 'pointer',
        transition: 'background-color 0.15s ease',
      }}
    >
      <span style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.base,
        color: colors.text,
      }}>
        {text}
      </span>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.sm,
        fontWeight: typography.weights.medium,
        color: colors.textSecondary,
        flexShrink: 0,
        marginLeft: '16px',
      }}>
        View
        <ChevronRight size={14} color={colors.textMuted} />
      </div>
    </div>
  );
}

export default function Dashboard() {
  return (
    <div>
      <div style={{ marginBottom: '28px' }}>
        <SectionHeader>Overview</SectionHeader>
        <div style={{ display: 'flex', gap: '12px' }}>
          <StatCard value="12,481" label="Documents" delta="+124 today" deltaColor={colors.success} />
          <StatCard value="3" label="Connectors" delta="all active" deltaColor={colors.textMuted} />
          <StatCard value="2" label="Running" delta="now" deltaColor={colors.running} />
        </div>
      </div>

      <div style={{ marginBottom: '24px' }}>
        <SectionHeader>Needs attention</SectionHeader>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {attentionItems.map((text, i) => (
            <AttentionCard key={i} text={text} />
          ))}
        </div>
      </div>

      <div style={{ marginBottom: '24px' }}>
        <SectionHeader>Active now</SectionHeader>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <ActivityCard name="RAG Workflow running" startedAgo="2m" />
          <ActivityCard name="Slack synchronizing" startedAgo="8m" />
        </div>
      </div>

      <div>
        <SectionHeader>Recent</SectionHeader>
        <EventList />
      </div>
    </div>
  );
}

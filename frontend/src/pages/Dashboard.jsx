import { ChevronRight } from 'lucide-react';
import { useState } from 'react';
import { colors, typography } from '../theme';
import SectionHeader from '../components/SectionHeader';
import StatCard from '../components/StatCard';
import ActivityCard from '../components/ActivityCard';
import EventList from '../components/EventList';
import { mockStats, mockActiveNow, mockNeedsAttention, mockRecentEvents } from '../mock/data';

function AttentionCard({ item }) {
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
        {item.message}
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
          <StatCard value={mockStats.documents.count} label="Documents" delta={mockStats.documents.delta} deltaColor={colors.success} />
          <StatCard value={mockStats.connectors.count} label="Connectors" delta={mockStats.connectors.status} deltaColor={colors.textMuted} />
          <StatCard value={mockStats.running.count} label="Running" delta={mockStats.running.status} deltaColor={colors.running} />
        </div>
      </div>

      <div style={{ marginBottom: '24px' }}>
        <SectionHeader>Needs attention</SectionHeader>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {mockNeedsAttention.map(item => (
            <AttentionCard key={item.id} item={item} />
          ))}
        </div>
      </div>

      <div style={{ marginBottom: '24px' }}>
        <SectionHeader>Active now</SectionHeader>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {mockActiveNow.map(item => (
            <ActivityCard key={item.id} name={item.name} startedAgo={item.startedAgo} />
          ))}
        </div>
      </div>

      <div>
        <SectionHeader>Recent</SectionHeader>
        <EventList events={mockRecentEvents} />
      </div>
    </div>
  );
}

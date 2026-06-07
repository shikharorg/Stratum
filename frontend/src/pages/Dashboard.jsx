import { ChevronRight } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import { colors, typography } from '../theme';
import SectionHeader from '../components/SectionHeader';
import StatCard from '../components/StatCard';
import ActivityCard from '../components/ActivityCard';
import EventList from '../components/EventList';
import { mockActiveNow, mockNeedsAttention } from '../mock/data';
import apiClient from '../api/client';

function relativeTime(isoString) {
  const secs = Math.floor((Date.now() - new Date(isoString).getTime()) / 1000);
  if (secs < 60) return 'just now';
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
  return `${Math.floor(secs / 86400)}d ago`;
}

function isToday(isoString) {
  const d = new Date(isoString);
  const now = new Date();
  return d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate();
}

function mapAuditLog(item) {
  const et = item.event_type ?? '';
  const payload = item.payload ?? {};
  let primary = et;
  let secondary = null;

  if (et === 'retrieval.completed') {
    primary = 'Search completed';
    secondary = payload.query || null;
  } else if (et === 'document.ingested') {
    primary = (payload.name || item.resource_id?.slice(0, 8) || 'Document') + ' indexed';
  } else if (et === 'workflow.run.completed') {
    primary = (payload.workflow_name || 'Workflow') + ' completed';
  } else if (et === 'workflow.run.failed') {
    primary = (payload.workflow_name || 'Workflow') + ' failed';
  } else if (et === 'connector.synced') {
    primary = (payload.connector_name || 'Connector') + ' synchronized';
  }

  return {
    id: item.id,
    primary,
    secondary,
    time: relativeTime(item.created_at),
    status: et.includes('failed') ? 'error' : 'success',
  };
}

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
  const [documentCount, setDocumentCount] = useState(null);
  const [documentsToday, setDocumentsToday] = useState(0);
  const [recentEvents, setRecentEvents] = useState([]);
  const pollRef = useRef(null);

  async function fetchDocuments() {
    try {
      const { data } = await apiClient.get('/api/v1/ingestion/documents?page=1&page_size=100');
      setDocumentCount(data.total);
      setDocumentsToday((data.items ?? []).filter(d => isToday(d.created_at)).length);
    } catch {
      // keep existing value
    }
  }

  async function fetchAuditLogs() {
    try {
      const { data } = await apiClient.get('/api/v1/observer/audit-logs?page_size=10');
      setRecentEvents((data.items ?? []).map(mapAuditLog));
    } catch {
      // silently keep existing events
    }
  }

  useEffect(() => {
    fetchDocuments();
    fetchAuditLogs();
    pollRef.current = setInterval(fetchAuditLogs, 15000);
    return () => clearInterval(pollRef.current);
  }, []);

  const docCount = documentCount === null ? '—' : documentCount.toLocaleString('en-US');
  const docDelta = documentsToday > 0 ? `+${documentsToday} today` : undefined;

  return (
    <div>
      <div style={{ marginBottom: '28px' }}>
        <SectionHeader>Overview</SectionHeader>
        <div style={{ display: 'flex', gap: '12px' }}>
          <StatCard
            value={docCount}
            label="Documents"
            delta={docDelta}
            deltaColor={colors.success}
          />
          <StatCard value="3" label="Connectors" delta="all active" deltaColor={colors.textMuted} />
          <StatCard value="2" label="Running" delta="now" deltaColor={colors.running} />
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
        <EventList events={recentEvents} />
      </div>
    </div>
  );
}

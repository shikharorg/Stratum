import { useState, useEffect, useRef } from 'react';
import { colors, typography } from '../theme';
import SectionHeader from '../components/SectionHeader';
import StatCard from '../components/StatCard';
import EventList from '../components/EventList';
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

export default function Dashboard() {
  const [documentCount, setDocumentCount] = useState(null);
  const [documentsToday, setDocumentsToday] = useState(0);
  const [connectorCount, setConnectorCount] = useState(null);
  const [runningCount, setRunningCount] = useState(null);
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

  async function fetchConnectors() {
    try {
      const { data } = await apiClient.get('/api/v1/connectors');
      setConnectorCount(data.total ?? 0);
    } catch {
      // keep existing value
    }
  }

  async function fetchActiveRuns() {
    try {
      const { data: wfData } = await apiClient.get('/api/v1/workflow/workflows');
      const workflows = wfData.items ?? [];

      const runResults = await Promise.all(
        workflows.map(wf =>
          apiClient
            .get(`/api/v1/workflow/workflows/${wf.id}/runs`)
            .then(r => ({ name: wf.name, runs: r.data.items ?? [] }))
            .catch(() => ({ name: wf.name, runs: [] }))
        )
      );

      const oneHourAgo = Date.now() - 3600000;
      const active = [];
      runResults.forEach(({ name, runs }) => {
        runs
          .filter(r =>
            (r.status === 'running' || r.status === 'pending') &&
            new Date(r.created_at).getTime() > oneHourAgo
          )
          .forEach(r => active.push({ id: r.id, name: `${name} ${r.status}`, startedAgo: relativeTime(r.created_at) }));
      });

      setRunningCount(active.length);
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
    fetchConnectors();
    fetchActiveRuns();
    fetchAuditLogs();
    pollRef.current = setInterval(() => {
      fetchAuditLogs();
      fetchActiveRuns();
    }, 15000);
    return () => clearInterval(pollRef.current);
  }, []);

  const docCount = documentCount === null ? '—' : documentCount.toLocaleString('en-US');
  const docDelta = documentsToday > 0 ? `+${documentsToday} today` : undefined;
  const connCount = connectorCount === null ? '—' : String(connectorCount);
  const runCount = runningCount === null ? '—' : String(runningCount);

  return (
    <div>
      <div style={{ marginBottom: '28px' }}>
        <SectionHeader>Overview</SectionHeader>
        <div style={{ display: 'flex', gap: '12px' }}>
          <StatCard value={docCount} label="Documents" delta={docDelta} deltaColor={colors.success} />
          <StatCard value={connCount} label="Connectors" delta={connectorCount === 0 ? 'none' : connectorCount === 1 ? '1 configured' : `${connCount} configured`} deltaColor={colors.textMuted} />
          <StatCard value={runCount} label="Running" delta={runningCount === 0 ? 'none active' : 'now'} deltaColor={colors.running} />
        </div>
      </div>

      <div>
        <SectionHeader>Recent</SectionHeader>
        <EventList events={recentEvents} />
      </div>
    </div>
  );
}

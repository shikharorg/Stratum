import { useState, useEffect, useRef } from 'react';
import { colors, typography } from '../theme';
import SectionHeader from '../components/SectionHeader';
import { mockAvailableIntegrations } from '../mock/data';
import apiClient from '../api/client';

function relativeTime(isoString) {
  if (!isoString) return 'never';
  const secs = Math.floor((Date.now() - new Date(isoString).getTime()) / 1000);
  if (secs < 60) return 'just now';
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
  return `${Math.floor(secs / 86400)}d ago`;
}

function deriveConnectorView(connector, runs) {
  const sorted = [...(runs || [])].sort(
    (a, b) => new Date(b.created_at) - new Date(a.created_at)
  );
  const latestRun = sorted[0] ?? null;
  const latestCompleted = sorted.find(r => r.completed_at) ?? null;

  const isError = latestRun?.status === 'failed' && !connector.is_active === false;
  const status = !connector.is_active
    ? 'inactive'
    : latestRun?.status === 'failed'
    ? 'error'
    : 'active';

  const lastSync = latestCompleted
    ? relativeTime(latestCompleted.completed_at)
    : 'never';

  const documentsIngested = (runs || []).reduce(
    (sum, r) => sum + (r.items_processed ?? 0),
    0
  );

  const errorMessage = status === 'error' ? (latestRun?.error_message ?? null) : null;

  return {
    id: String(connector.id),
    name: connector.name,
    type: connector.connector_type,
    status,
    lastSync,
    documentsIngested,
    errorMessage,
  };
}

function formatCount(n) {
  return n.toLocaleString('en-US');
}

function ConnectorCard({ connector, onSync, onDeactivate, syncing, deactivating }) {
  const [hovered, setHovered] = useState(false);
  const [syncHovered, setSyncHovered] = useState(false);
  const [deactivateHovered, setDeactivateHovered] = useState(false);
  const isError = connector.status === 'error';

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        backgroundColor: isError
          ? hovered ? 'rgba(239, 68, 68, 0.07)' : 'rgba(239, 68, 68, 0.04)'
          : hovered ? colors.surfaceHover : colors.surface,
        border: `1px solid ${colors.border}`,
        borderLeftWidth: isError ? '4px' : '1px',
        borderLeftColor: isError ? colors.error : colors.border,
        borderRadius: '6px',
        padding: '12px 16px',
        transition: 'background-color 0.15s ease',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '8px' }}>
        <div>
          <div style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.base,
            fontWeight: typography.weights.medium,
            color: colors.text,
            marginBottom: '2px',
          }}>
            {connector.name}
          </div>
          <div style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.sm,
            color: colors.textMuted,
            marginBottom: isError ? '2px' : '0',
          }}>
            {connector.type}
          </div>
          {isError && connector.errorMessage && (
            <div style={{
              fontFamily: typography.fontUI,
              fontSize: typography.sizes.sm,
              color: colors.error,
            }}>
              {connector.errorMessage}
            </div>
          )}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px', flexShrink: 0, marginLeft: '16px' }}>
          {connector.status === 'active' && (
            <button
              disabled={syncing}
              onClick={() => onSync(connector.id)}
              onMouseEnter={() => setSyncHovered(true)}
              onMouseLeave={() => setSyncHovered(false)}
              style={{
                fontFamily: typography.fontUI,
                fontSize: typography.sizes.sm,
                fontWeight: typography.weights.regular,
                color: syncing ? colors.textMuted : syncHovered ? colors.text : colors.textSecondary,
                backgroundColor: syncHovered && !syncing ? colors.surfaceHover : colors.surface,
                border: `1px solid ${colors.border}`,
                borderRadius: '4px',
                padding: '4px 10px',
                cursor: syncing ? 'default' : 'pointer',
                transition: 'color 0.15s ease, background-color 0.15s ease',
              }}
            >
              {syncing ? '...' : 'Sync now'}
            </button>
          )}
          {connector.status === 'inactive' && (
            <span style={{
              fontFamily: typography.fontUI,
              fontSize: typography.sizes.sm,
              color: colors.textMuted,
            }}>
              Inactive
            </span>
          )}
          {isError && (
            <span style={{
              fontFamily: typography.fontUI,
              fontSize: typography.sizes.sm,
              color: colors.error,
            }}>
              Error
            </span>
          )}
          <span style={{
            fontFamily: typography.fontMono,
            fontSize: typography.sizes.xs,
            color: colors.textMuted,
          }}>
            {isError ? `Since ${connector.lastSync}` : `Last sync ${connector.lastSync}`}
          </span>
          <button
            disabled={deactivating}
            onClick={() => onDeactivate(connector.id)}
            onMouseEnter={() => setDeactivateHovered(true)}
            onMouseLeave={() => setDeactivateHovered(false)}
            style={{
              fontFamily: typography.fontUI,
              fontSize: typography.sizes.xs,
              fontWeight: typography.weights.regular,
              color: deactivating ? colors.textMuted : deactivateHovered ? colors.error : colors.textMuted,
              background: 'none',
              border: 'none',
              padding: '0',
              cursor: deactivating ? 'default' : 'pointer',
              transition: 'color 0.15s ease',
            }}
          >
            {deactivating ? '...' : 'Disconnect'}
          </button>
        </div>
      </div>
      <div style={{
        fontFamily: typography.fontMono,
        fontSize: typography.sizes.sm,
        color: colors.textMuted,
      }}>
        {formatCount(connector.documentsIngested)} documents ingested
      </div>
    </div>
  );
}

function AvailableCard({ integration }) {
  const [connectHovered, setConnectHovered] = useState(false);

  return (
    <div style={{
      flex: 1,
      backgroundColor: colors.surface,
      border: `1px solid ${colors.border}`,
      borderRadius: '6px',
      padding: '16px',
      display: 'flex',
      flexDirection: 'column',
      gap: '4px',
    }}>
      <div style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.base,
        fontWeight: typography.weights.medium,
        color: colors.text,
      }}>
        {integration.name}
      </div>
      <div style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.sm,
        color: colors.textMuted,
        marginBottom: '12px',
      }}>
        {integration.description}
      </div>
      <button
        onMouseEnter={() => setConnectHovered(true)}
        onMouseLeave={() => setConnectHovered(false)}
        style={{
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.sm,
          fontWeight: typography.weights.regular,
          color: connectHovered ? colors.text : colors.textSecondary,
          backgroundColor: connectHovered ? colors.surfaceHover : colors.surface,
          border: `1px solid ${colors.border}`,
          borderRadius: '4px',
          padding: '5px 12px',
          cursor: 'pointer',
          alignSelf: 'flex-start',
          transition: 'color 0.15s ease, background-color 0.15s ease',
        }}
      >
        + Connect
      </button>
    </div>
  );
}

export default function Integrations() {
  const [addHovered, setAddHovered] = useState(false);
  const [rawConnectors, setRawConnectors] = useState([]);
  const [runsByConnector, setRunsByConnector] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [syncingIds, setSyncingIds] = useState(new Set());
  const [deactivatingIds, setDeactivatingIds] = useState(new Set());
  const pollRef = useRef(null);

  async function fetchConnectors() {
    const { data } = await apiClient.get('/api/v1/connectors');
    return data.items ?? [];
  }

  async function fetchRuns(connectorList) {
    const results = await Promise.all(
      connectorList.map(c =>
        apiClient
          .get(`/api/v1/connectors/${c.id}/runs`)
          .then(r => ({ id: String(c.id), runs: r.data.items ?? [] }))
          .catch(() => ({ id: String(c.id), runs: [] }))
      )
    );
    const map = {};
    results.forEach(({ id, runs }) => { map[id] = runs; });
    return map;
  }

  async function loadAll() {
    const list = await fetchConnectors();
    setRawConnectors(list);
    const runs = await fetchRuns(list);
    setRunsByConnector(runs);
    return list;
  }

  async function pollRefresh(currentList) {
    try {
      const runs = await fetchRuns(currentList);
      setRunsByConnector(runs);
    } catch {
      // silently ignore
    }
  }

  useEffect(() => {
    let mounted = true;
    let connectorList = [];

    loadAll()
      .then(list => {
        if (mounted) {
          connectorList = list;
          setIsLoading(false);
        }
      })
      .catch(() => {
        if (mounted) {
          setError('Failed to load connectors.');
          setIsLoading(false);
        }
      });

    pollRef.current = setInterval(() => {
      if (connectorList.length > 0) pollRefresh(connectorList);
    }, 15000);

    return () => {
      mounted = false;
      clearInterval(pollRef.current);
    };
  }, []);

  async function handleSync(connectorId) {
    setSyncingIds(prev => new Set(prev).add(connectorId));
    try {
      await apiClient.post(`/api/v1/connectors/${connectorId}/sync`);
      const list = await fetchConnectors();
      setRawConnectors(list);
      const runs = await fetchRuns(list);
      setRunsByConnector(runs);
    } catch {
      // silently ignore
    } finally {
      setSyncingIds(prev => { const s = new Set(prev); s.delete(connectorId); return s; });
    }
  }

  async function handleDeactivate(connectorId) {
    setDeactivatingIds(prev => new Set(prev).add(connectorId));
    try {
      await apiClient.delete(`/api/v1/connectors/${connectorId}`);
      const list = await fetchConnectors();
      setRawConnectors(list);
      const runs = await fetchRuns(list);
      setRunsByConnector(runs);
    } catch {
      // silently ignore
    } finally {
      setDeactivatingIds(prev => { const s = new Set(prev); s.delete(connectorId); return s; });
    }
  }

  const connectors = rawConnectors.map(c =>
    deriveConnectorView(c, runsByConnector[String(c.id)])
  );

  const activeCount = connectors.filter(c => c.status === 'active').length;
  const errorCount = connectors.filter(c => c.status === 'error').length;
  const inactiveCount = connectors.filter(c => c.status === 'inactive').length;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px' }}>
        <div style={{
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.xl,
          fontWeight: typography.weights.semibold,
          color: colors.text,
        }}>
          Integrations
        </div>
        <button
          onMouseEnter={() => setAddHovered(true)}
          onMouseLeave={() => setAddHovered(false)}
          style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.base,
            fontWeight: typography.weights.regular,
            color: addHovered ? colors.text : colors.textSecondary,
            backgroundColor: addHovered ? colors.surfaceHover : colors.surface,
            border: `1px solid ${colors.border}`,
            borderRadius: '5px',
            padding: '6px 14px',
            cursor: 'pointer',
            transition: 'color 0.15s ease, background-color 0.15s ease',
          }}
        >
          + Add Integration
        </button>
      </div>

      {error ? (
        <div style={{
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.sm,
          color: colors.error,
          marginBottom: '24px',
        }}>
          {error}
        </div>
      ) : (
        <div style={{
          fontFamily: typography.fontMono,
          fontSize: typography.sizes.xs,
          color: colors.textMuted,
          marginBottom: '24px',
        }}>
          {isLoading
            ? 'Loading...'
            : `${connectors.length} connectors · ${activeCount} active · ${errorCount} error · ${inactiveCount} inactive`
          }
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '36px' }}>
        {isLoading ? null : connectors.length === 0 ? (
          <div style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.base,
            color: colors.textMuted,
            padding: '8px 0',
          }}>
            No connectors configured.
          </div>
        ) : (
          connectors.map(connector => (
            <ConnectorCard
              key={connector.id}
              connector={connector}
              onSync={handleSync}
              onDeactivate={handleDeactivate}
              syncing={syncingIds.has(connector.id)}
              deactivating={deactivatingIds.has(connector.id)}
            />
          ))
        )}
      </div>

      <div>
        <SectionHeader>Available</SectionHeader>
        <div style={{ display: 'flex', gap: '12px' }}>
          {mockAvailableIntegrations.map(integration => (
            <AvailableCard key={integration.type} integration={integration} />
          ))}
        </div>
      </div>
    </div>
  );
}

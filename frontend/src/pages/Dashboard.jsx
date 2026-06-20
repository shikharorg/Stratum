import { useState, useEffect } from 'react';
import { colors, typography } from '../theme';
import apiClient from '../api/client';

const CARD_BORDER = '1px solid #e2e1de';
const ROW_DIVIDER = '1px solid #f0efed';

// ── Pill badge ──────────────────────────────────────────────────────────────
function Pill({ label, bg, color, border }) {
  return (
    <span style={{
      display: 'inline-block',
      backgroundColor: bg,
      color,
      border: border || 'none',
      fontFamily: typography.fontUI,
      fontSize: '11px',
      fontWeight: 500,
      padding: '2px 8px',
      borderRadius: '999px',
      whiteSpace: 'nowrap',
    }}>
      {label}
    </span>
  );
}

// ── Skeleton ─────────────────────────────────────────────────────────────────
function Skeleton({ width = '100%', height = '16px', style = {} }) {
  return (
    <div style={{
      width,
      height,
      backgroundColor: colors.surfaceHover,
      borderRadius: '4px',
      ...style,
    }} />
  );
}

// ── Stat card ─────────────────────────────────────────────────────────────────
function StatCard({ value, label, pill, loading }) {
  return (
    <div style={{
      flex: 1,
      backgroundColor: '#ffffff',
      border: CARD_BORDER,
      borderRadius: '10px',
      padding: '18px 20px',
      minWidth: 0,
    }}>
      {loading ? (
        <>
          <Skeleton height="32px" width="56px" />
          <Skeleton height="13px" width="80px" style={{ marginTop: '8px' }} />
          <Skeleton height="20px" width="96px" style={{ marginTop: '10px' }} />
        </>
      ) : (
        <>
          <div style={{
            fontFamily: typography.fontMono,
            fontSize: '28px',
            fontWeight: 500,
            color: colors.text,
            lineHeight: 1,
            marginBottom: '6px',
          }}>
            {value}
          </div>
          <div style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.base,
            color: colors.textSecondary,
            marginBottom: '10px',
          }}>
            {label}
          </div>
          {pill && <Pill {...pill} />}
        </>
      )}
    </div>
  );
}

// ── Card wrapper ──────────────────────────────────────────────────────────────
function Card({ title, subtitle, subtitleColor, children }) {
  return (
    <div style={{
      flex: 1,
      backgroundColor: '#ffffff',
      border: CARD_BORDER,
      borderRadius: '10px',
      padding: '22px 20px',
      minWidth: 0,
    }}>
      <div style={{ marginBottom: '16px' }}>
        <div style={{
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.base,
          fontWeight: typography.weights.medium,
          color: colors.text,
          marginBottom: '2px',
        }}>
          {title}
        </div>
        {subtitle && (
          <div style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.sm,
            color: subtitleColor || colors.textMuted,
          }}>
            {subtitle}
          </div>
        )}
      </div>
      {children}
    </div>
  );
}

// ── Quality metric row ────────────────────────────────────────────────────────
function QualityMetricRow({ label, value, isLast }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingTop: '12px',
      paddingBottom: '12px',
      borderBottom: isLast ? 'none' : ROW_DIVIDER,
    }}>
      <div style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.base,
        color: colors.text,
      }}>
        {label}
      </div>
      <div style={{
        fontFamily: typography.fontMono,
        fontSize: '20px',
        fontWeight: 500,
        color: '#1a1a1a',
        display: 'flex',
        alignItems: 'baseline',
        gap: '3px',
      }}>
        <span style={{ fontSize: '12px', color: '#639922', fontFamily: typography.fontUI }}>↑</span>
        {value}%
      </div>
    </div>
  );
}

// ── Usage tile (2×2 grid cell) ────────────────────────────────────────────────
function UsageTile({ value, label, sub }) {
  return (
    <div style={{
      backgroundColor: '#ffffff',
      border: CARD_BORDER,
      borderRadius: '8px',
      padding: '14px',
    }}>
      <div style={{
        fontFamily: typography.fontMono,
        fontSize: '22px',
        fontWeight: 500,
        color: colors.text,
        lineHeight: 1,
        marginBottom: '4px',
      }}>
        {value}
      </div>
      <div style={{
        fontFamily: typography.fontUI,
        fontSize: '11px',
        color: '#6b6b6b',
        marginBottom: '2px',
      }}>
        {label}
      </div>
      <div style={{
        fontFamily: typography.fontUI,
        fontSize: '11px',
        color: '#999',
      }}>
        {sub}
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [docData, setDocData] = useState(null);
  const [connectorData, setConnectorData] = useState(null);
  const [runData, setRunData] = useState(null);
  const [searchData, setSearchData] = useState(null);
  const [userData, setUserData] = useState(null);
  // null = loading, false = error, object = loaded
  const [qualityData, setQualityData] = useState(null);

  useEffect(() => {
    // Documents
    apiClient
      .get('/api/v1/ingestion/documents?page=1&page_size=100')
      .then(({ data }) => {
        const items = data.items ?? [];
        setDocData({
          total: data.total ?? 0,
          pending: items.filter(d => d.status !== 'completed').length,
          chunks: items.filter(d => d.status === 'completed').reduce((s, d) => s + (d.chunk_count || 0), 0),
        });
      })
      .catch(() => setDocData({ total: 0, pending: 0, chunks: 0 }));

    // Connectors — fetch supported types, not configured instances
    apiClient
      .get('/api/v1/connectors/types')
      .then(({ data }) => {
        const types = data.types ?? [];
        setConnectorData({
          total: types.length,
          names: types.map(t => t.label),
        });
      })
      .catch(() => setConnectorData({ total: 0, names: [] }));

    // Workflow runs — fetch all workflows then aggregate their runs
    apiClient
      .get('/api/v1/workflow/workflows?page_size=100')
      .then(async ({ data }) => {
        const workflows = data.items ?? [];
        const pages = await Promise.all(
          workflows.map(wf =>
            apiClient
              .get(`/api/v1/workflow/workflows/${wf.id}/runs?page_size=100`)
              .then(r => ({ items: r.data.items ?? [], total: r.data.total ?? 0 }))
              .catch(() => ({ items: [], total: 0 }))
          )
        );
        const totalRuns = pages.reduce((s, p) => s + p.total, 0);
        const allItems = pages.flatMap(p => p.items);
        const completed = allItems.filter(r => r.status === 'completed').length;
        const failed = allItems.filter(r => r.status === 'failed').length;
        const denom = completed + failed;
        const successRate = denom > 0 ? Math.round((completed / denom) * 1000) / 10 : 0;
        setRunData({ total: totalRuns, successRate });
      })
      .catch(() => setRunData({ total: 0, successRate: 0 }));

    // Searches — GET /api/v1/retrieval/stats → { total, this_week }
    apiClient
      .get('/api/v1/retrieval/stats')
      .then(({ data }) => setSearchData({ total: data.total ?? 0, week: data.this_week ?? 0 }))
      .catch(() => setSearchData({ total: 0, week: 0 }));

    // Active users
    apiClient
      .get('/api/v1/identity/users?page_size=1')
      .then(({ data }) => setUserData({ total: data.total ?? 0 }))
      .catch(() => setUserData({ total: null }));

    // Search quality — GET /api/v1/evaluation/quality
    apiClient
      .get('/api/v1/evaluation/quality')
      .then(({ data }) => setQualityData(data))
      .catch(() => setQualityData(false));
  }, []);

  // Loading states
  const statsLoading = docData === null || connectorData === null || runData === null || searchData === null;
  const qualityLoading = qualityData === null;

  // Derived values
  const documents = docData?.total ?? 0;
  const pendingDocs = docData?.pending ?? 0;
  const chunks = docData?.chunks ?? 0;
  const allIndexed = pendingDocs === 0 && documents > 0;
  const docPill = allIndexed
    ? { label: 'All indexed', bg: '#eef4e8', color: '#3b6d11' }
    : pendingDocs > 0
    ? { label: `${pendingDocs} indexing`, bg: '#f3f2f0', color: '#5f5e5a' }
    : { label: 'No documents', bg: '#f3f2f0', color: '#5f5e5a' };

  const totalRuns = runData?.total ?? 0;
  const successRate = runData?.successRate ?? 0;
  const wfPill = { label: `${successRate}% success`, bg: '#eef4e8', color: '#3b6d11' };

  const connectorNames = connectorData?.names ?? [];
  const connectorTotal = connectorData?.total ?? 0;
  const connectorPill = {
    label: connectorNames.length > 0 ? connectorNames.join(' · ') : 'Available',
    bg: '#f3f2f0',
    color: '#6b6b6b',
    border: CARD_BORDER,
  };

  const searches = searchData?.total ?? 0;
  const searchesWeek = searchData?.week ?? 0;
  const searchPill = { label: `This week: ${searchesWeek}`, bg: '#e8f0fb', color: '#185FA5' };

  const activeUsers = userData?.total;

  const qualityMetrics = [
    { label: 'Faithfulness',      value: qualityData ? qualityData.faithfulness      : 0 },
    { label: 'Answer Relevancy',  value: qualityData ? qualityData.answer_relevancy  : 0 },
    { label: 'Context Precision', value: qualityData ? qualityData.context_precision : 0 },
  ];

  return (
    <div>
      <div style={{
        fontFamily: typography.fontUI,
        fontSize: '15px',
        fontWeight: 500,
        color: '#1a1a1a',
        marginBottom: '20px',
      }}>
        Dashboard
      </div>

      {/* 4-card stat row */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
        <StatCard loading={statsLoading} value={documents.toLocaleString('en-US')} label="Documents" pill={docPill} />
        <StatCard loading={statsLoading} value={totalRuns.toLocaleString('en-US')} label="Workflow runs" pill={wfPill} />
        <StatCard loading={statsLoading} value={String(connectorTotal)} label="Connectors" pill={connectorPill} />
        <StatCard loading={statsLoading} value={searches.toLocaleString('en-US')} label="Searches run" pill={searchPill} />
      </div>

      {/* Two side-by-side cards */}
      <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>

        {/* Search Quality */}
        <Card
          title="Search quality"
          subtitle={
            qualityLoading ? '' :
            qualityData === false ? 'Could not load quality data' :
            `Based on ${qualityData.total_evaluations} RAGAS evaluations`
          }
          subtitleColor={qualityData === false ? colors.error : colors.textMuted}
        >
          {qualityLoading ? (
            [0, 1, 2].map(i => (
              <div key={i} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                paddingTop: '12px',
                paddingBottom: '12px',
                borderBottom: i < 2 ? ROW_DIVIDER : 'none',
              }}>
                <Skeleton width="120px" height="13px" />
                <Skeleton width="48px" height="22px" />
              </div>
            ))
          ) : qualityData === false ? (
            <div style={{ fontFamily: typography.fontUI, fontSize: typography.sizes.sm, color: colors.textMuted }}>
              Restart the evaluation service to enable quality tracking.
            </div>
          ) : (
            <>
              {qualityMetrics.map((m, i) => (
                <QualityMetricRow key={m.label} label={m.label} value={m.value} isLast={i === qualityMetrics.length - 1} />
              ))}
              <div style={{
                paddingTop: '12px',
                borderTop: ROW_DIVIDER,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <span style={{ fontFamily: typography.fontUI, fontSize: typography.sizes.sm, color: colors.textMuted }}>
                  Total evaluations
                </span>
                <span style={{ fontFamily: typography.fontMono, fontSize: typography.sizes.base, color: colors.text }}>
                  {qualityData.total_evaluations.toLocaleString('en-US')}
                </span>
              </div>
            </>
          )}
        </Card>

        {/* Platform usage */}
        <Card title="Platform usage" subtitle="Last 30 days">
          {statsLoading ? (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              {[0, 1, 2, 3].map(i => (
                <div key={i} style={{
                  backgroundColor: '#ffffff',
                  border: CARD_BORDER,
                  borderRadius: '8px',
                  padding: '14px',
                }}>
                  <Skeleton height="22px" width="48px" />
                  <Skeleton height="11px" width="80px" style={{ marginTop: '6px' }} />
                  <Skeleton height="11px" width="64px" style={{ marginTop: '4px' }} />
                </div>
              ))}
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <UsageTile
                value={searches.toLocaleString('en-US')}
                label="Doc searches"
                sub={`+${searchesWeek} this week`}
              />
              <UsageTile
                value={totalRuns.toLocaleString('en-US')}
                label="Workflow executions"
                sub={`${successRate}% success rate`}
              />
              <UsageTile
                value={chunks.toLocaleString('en-US')}
                label="Docs indexed"
                sub=""
              />
              <UsageTile
                value={activeUsers !== null ? activeUsers : '—'}
                label={activeUsers === 1 ? 'Active user' : 'Active users'}
                sub=""
              />
            </div>
          )}
        </Card>

      </div>
    </div>
  );
}

import { useState, useEffect, useRef } from 'react';
import { colors, typography } from '../theme';
import SectionHeader from '../components/SectionHeader';
import StatusBadge from '../components/StatusBadge';
import apiClient from '../api/client';

const COL = { id: '90px', workflow: '1fr', status: '110px', duration: '80px', started: '90px' };

function relativeTime(isoString) {
  const secs = Math.floor((Date.now() - new Date(isoString).getTime()) / 1000);
  if (secs < 60) return 'just now';
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
  return `${Math.floor(secs / 86400)}d ago`;
}

function computeStats(runs) {
  if (!runs || runs.length === 0) {
    return { lastRun: 'never', successRate: '—', totalRuns: 0 };
  }
  const sorted = [...runs].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  const lastRun = relativeTime(sorted[0].created_at);
  const totalRuns = runs.length;
  const completed = runs.filter(r => r.status === 'completed').length;
  const failed = runs.filter(r => r.status === 'failed').length;
  const denom = completed + failed;
  const successRate = denom === 0 ? '—' : `${Math.round((completed / denom) * 100)}%`;
  return { lastRun, successRate, totalRuns };
}

function mapRun(run, workflowName) {
  return {
    id: run.id,
    workflow: workflowName,
    status: run.status,
    duration: run.latency_ms != null ? `${(run.latency_ms / 1000).toFixed(1)}s` : '—',
    startedAt: relativeTime(run.created_at),
    created_at: run.created_at,
  };
}

function WorkflowCard({ wf, onRunClick, formOpen, formQuery, onQueryChange, onSubmit, onCancel, formLoading }) {
  const [hovered, setHovered] = useState(false);
  const [runHovered, setRunHovered] = useState(false);

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        backgroundColor: hovered ? colors.surfaceHover : colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: '6px',
        padding: '16px',
        transition: 'background-color 0.15s ease',
        cursor: 'default',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <div style={{ minWidth: 0, marginRight: '16px' }}>
          <div style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.lg,
            fontWeight: typography.weights.medium,
            color: colors.text,
            marginBottom: '2px',
          }}>
            {wf.name}
          </div>
          <div style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.sm,
            color: colors.textSecondary,
          }}>
            {wf.description}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
          {wf.status === 'inactive' && (
            <span style={{
              fontFamily: typography.fontUI,
              fontSize: typography.sizes.sm,
              fontWeight: typography.weights.regular,
              color: colors.textMuted,
            }}>
              Inactive
            </span>
          )}
          {wf.status === 'active' && (
            <button
              disabled={formOpen}
              onClick={() => onRunClick(wf.id)}
              onMouseEnter={() => setRunHovered(true)}
              onMouseLeave={() => setRunHovered(false)}
              style={{
                fontFamily: typography.fontUI,
                fontSize: typography.sizes.sm,
                fontWeight: typography.weights.medium,
                color: formOpen ? colors.textMuted : runHovered ? colors.text : colors.textSecondary,
                backgroundColor: runHovered && !formOpen ? colors.surfaceHover : colors.surface,
                border: `1px solid ${colors.border}`,
                borderRadius: '4px',
                padding: '4px 10px',
                cursor: formOpen ? 'default' : 'pointer',
                transition: 'color 0.15s ease, background-color 0.15s ease',
              }}
            >
              Run
            </button>
          )}
        </div>
      </div>
      <div style={{
        display: 'flex',
        gap: '8px',
        fontFamily: typography.fontMono,
        fontSize: typography.sizes.sm,
        color: colors.textMuted,
      }}>
        <span>Last run: {wf.lastRun}</span>
        <span>·</span>
        <span>Success rate: {wf.successRate}</span>
        <span>·</span>
        <span>{wf.totalRuns} runs total</span>
      </div>
      {formOpen && (
        <form
          onSubmit={onSubmit}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginTop: '12px',
            paddingTop: '12px',
            borderTop: `1px solid ${colors.borderSubtle}`,
          }}
        >
          <input
            autoFocus
            type="text"
            placeholder="Enter a query..."
            value={formQuery}
            onChange={e => onQueryChange(e.target.value)}
            style={{
              flex: 1,
              fontFamily: typography.fontUI,
              fontSize: typography.sizes.sm,
              color: colors.text,
              backgroundColor: colors.background ?? colors.surfaceHover,
              border: `1px solid ${colors.border}`,
              borderRadius: '4px',
              padding: '5px 10px',
              outline: 'none',
            }}
          />
          <button
            type="submit"
            disabled={formLoading || !formQuery.trim()}
            style={{
              fontFamily: typography.fontUI,
              fontSize: typography.sizes.sm,
              color: colors.text,
              backgroundColor: colors.surface,
              border: `1px solid ${colors.border}`,
              borderRadius: '4px',
              padding: '5px 10px',
              cursor: formLoading || !formQuery.trim() ? 'default' : 'pointer',
              opacity: formLoading || !formQuery.trim() ? 0.5 : 1,
            }}
          >
            {formLoading ? '...' : 'Submit'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={formLoading}
            style={{
              fontFamily: typography.fontUI,
              fontSize: typography.sizes.sm,
              color: colors.textMuted,
              backgroundColor: 'transparent',
              border: 'none',
              padding: '5px 4px',
              cursor: formLoading ? 'default' : 'pointer',
            }}
          >
            Cancel
          </button>
        </form>
      )}
    </div>
  );
}

function RunRow({ run, isLast }) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'grid',
        gridTemplateColumns: `${COL.id} ${COL.workflow} ${COL.status} ${COL.duration} ${COL.started}`,
        alignItems: 'center',
        padding: '10px 12px',
        backgroundColor: hovered ? colors.surfaceHover : 'transparent',
        borderBottom: isLast ? 'none' : `1px solid ${colors.borderSubtle}`,
        transition: 'background-color 0.15s ease',
        cursor: 'default',
      }}
    >
      <span style={{ fontFamily: typography.fontMono, fontSize: typography.sizes.sm, color: colors.textMuted }}>
        {run.id.slice(0, 8)}
      </span>
      <span style={{ fontFamily: typography.fontUI, fontSize: typography.sizes.base, color: colors.text }}>
        {run.workflow}
      </span>
      <span>
        <StatusBadge status={run.status} />
      </span>
      <span style={{ fontFamily: typography.fontMono, fontSize: typography.sizes.sm, color: colors.textSecondary }}>
        {run.duration}
      </span>
      <span style={{ fontFamily: typography.fontMono, fontSize: typography.sizes.sm, color: colors.textMuted }}>
        {run.startedAt}
      </span>
    </div>
  );
}

export default function Workflows() {
  const [newHovered, setNewHovered] = useState(false);
  const [workflows, setWorkflows] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [runsByWorkflow, setRunsByWorkflow] = useState({});
  const [activeFormId, setActiveFormId] = useState(null);
  const [formQuery, setFormQuery] = useState('');
  const [formLoading, setFormLoading] = useState(false);
  const pollRef = useRef(null);

  async function fetchWorkflows() {
    const { data } = await apiClient.get('/api/v1/workflow/workflows');
    return data.items ?? [];
  }

  async function fetchAllRuns(wfList) {
    const results = await Promise.all(
      wfList.map(wf =>
        apiClient
          .get(`/api/v1/workflow/workflows/${wf.id}/runs`)
          .then(r => ({ id: wf.id, runs: r.data.items ?? [] }))
          .catch(() => ({ id: wf.id, runs: [] }))
      )
    );
    const map = {};
    results.forEach(({ id, runs }) => { map[id] = runs; });
    return map;
  }

  async function refreshRuns(wfList) {
    try {
      const map = await fetchAllRuns(wfList);
      setRunsByWorkflow(map);
    } catch {
      // silently ignore poll errors
    }
  }

  useEffect(() => {
    let wfList = [];
    fetchWorkflows()
      .then(list => {
        wfList = list;
        setWorkflows(list);
        return fetchAllRuns(list);
      })
      .then(map => {
        setRunsByWorkflow(map);
      })
      .catch(() => {})
      .finally(() => setIsLoading(false));

    pollRef.current = setInterval(() => {
      if (wfList.length > 0) refreshRuns(wfList);
    }, 10000);

    return () => clearInterval(pollRef.current);
  }, []);

  function handleRunClick(workflowId) {
    setActiveFormId(workflowId);
    setFormQuery('');
  }

  async function handleRunSubmit(e, workflowId) {
    e.preventDefault();
    if (!formQuery.trim()) return;
    setFormLoading(true);
    try {
      await apiClient.post(`/api/v1/workflow/workflows/${workflowId}/runs`, {
        input_data: { query: formQuery.trim() },
      });
      const { data } = await apiClient.get(`/api/v1/workflow/workflows/${workflowId}/runs`);
      setRunsByWorkflow(prev => ({ ...prev, [workflowId]: data.items ?? [] }));
      setActiveFormId(null);
    } catch {
      // silently ignore
    } finally {
      setFormLoading(false);
    }
  }

  const workflowNameMap = Object.fromEntries(workflows.map(w => [w.id, w.name]));

  const enrichedWorkflows = workflows.map(wf => {
    const runs = runsByWorkflow[wf.id] ?? [];
    const stats = computeStats(runs);
    return {
      ...wf,
      status: wf.is_active ? 'active' : 'inactive',
      ...stats,
    };
  });

  const allRuns = Object.entries(runsByWorkflow)
    .flatMap(([wfId, runs]) => runs.map(r => mapRun(r, workflowNameMap[wfId] ?? wfId)))
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 5);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px' }}>
        <div style={{
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.xl,
          fontWeight: typography.weights.semibold,
          color: colors.text,
        }}>
          Workflows
        </div>
        <button
          onMouseEnter={() => setNewHovered(true)}
          onMouseLeave={() => setNewHovered(false)}
          style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.base,
            fontWeight: typography.weights.regular,
            color: newHovered ? colors.text : colors.textSecondary,
            backgroundColor: newHovered ? colors.surfaceHover : colors.surface,
            border: `1px solid ${colors.border}`,
            borderRadius: '5px',
            padding: '6px 14px',
            cursor: 'pointer',
            transition: 'color 0.15s ease, background-color 0.15s ease',
          }}
        >
          + New Workflow
        </button>
      </div>

      <div style={{ marginBottom: '32px' }}>
        <SectionHeader>Definitions</SectionHeader>
        {isLoading ? (
          <div style={{ fontFamily: typography.fontUI, fontSize: typography.sizes.base, color: colors.textMuted }}>
            Loading...
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {enrichedWorkflows.map(wf => (
              <WorkflowCard
                key={wf.id}
                wf={wf}
                onRunClick={handleRunClick}
                formOpen={activeFormId === wf.id}
                formQuery={activeFormId === wf.id ? formQuery : ''}
                onQueryChange={setFormQuery}
                onSubmit={e => handleRunSubmit(e, wf.id)}
                onCancel={() => setActiveFormId(null)}
                formLoading={formLoading}
              />
            ))}
          </div>
        )}
      </div>

      <div>
        <SectionHeader>Recent runs</SectionHeader>
        <div style={{
          border: `1px solid ${colors.border}`,
          borderRadius: '6px',
          overflow: 'hidden',
        }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: `${COL.id} ${COL.workflow} ${COL.status} ${COL.duration} ${COL.started}`,
            padding: '8px 12px',
            borderBottom: `1px solid ${colors.border}`,
          }}>
            {['Run ID', 'Workflow', 'Status', 'Duration', 'Started'].map(h => (
              <span key={h} style={{
                fontFamily: typography.fontMono,
                fontSize: typography.sizes.xs,
                color: colors.textMuted,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
              }}>
                {h}
              </span>
            ))}
          </div>
          {allRuns.length === 0 ? (
            <div style={{
              padding: '16px 12px',
              fontFamily: typography.fontUI,
              fontSize: typography.sizes.base,
              color: colors.textMuted,
            }}>
              No runs yet
            </div>
          ) : (
            allRuns.map((run, i) => (
              <RunRow key={run.id} run={run} isLast={i === allRuns.length - 1} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}

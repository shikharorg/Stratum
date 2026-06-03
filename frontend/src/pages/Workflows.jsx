import { useState } from 'react';
import { colors, typography } from '../theme';
import SectionHeader from '../components/SectionHeader';
import StatusBadge from '../components/StatusBadge';

const definitions = [
  { id: 'ff00a735', name: 'RAG Workflow', description: 'Retrieves and generates answers from ingested documents', status: 'active', lastRun: '2m ago', successRate: '98%', totalRuns: 247 },
  { id: 'ab12cd34', name: 'Document Summary', description: 'Summarizes newly ingested documents automatically', status: 'active', lastRun: '1h ago', successRate: '100%', totalRuns: 89 },
  { id: 'ef56gh78', name: 'Slack Digest', description: 'Generates daily digest from Slack channel activity', status: 'inactive', lastRun: '2d ago', successRate: '91%', totalRuns: 34 },
];

const recentRuns = [
  { id: 'cd8432af', workflow: 'RAG Workflow', status: 'completed', duration: '5.3s', startedAt: '2m ago' },
  { id: 'aa886fd9', workflow: 'RAG Workflow', status: 'completed', duration: '2.1s', startedAt: '15m ago' },
  { id: '13432136', workflow: 'Document Summary', status: 'completed', duration: '1.8s', startedAt: '1h ago' },
  { id: '5ba792f4', workflow: 'RAG Workflow', status: 'failed', duration: '1.2s', startedAt: '3h ago' },
  { id: 'bb991cc2', workflow: 'Slack Digest', status: 'completed', duration: '8.7s', startedAt: '2d ago' },
];

const COL = { id: '90px', workflow: '1fr', status: '110px', duration: '80px', started: '90px' };

function WorkflowCard({ wf }) {
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
              onMouseEnter={() => setRunHovered(true)}
              onMouseLeave={() => setRunHovered(false)}
              style={{
                fontFamily: typography.fontUI,
                fontSize: typography.sizes.sm,
                fontWeight: typography.weights.medium,
                color: runHovered ? colors.text : colors.textSecondary,
                backgroundColor: runHovered ? colors.surfaceHover : colors.surface,
                border: `1px solid ${colors.border}`,
                borderRadius: '4px',
                padding: '4px 10px',
                cursor: 'pointer',
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {definitions.map(wf => <WorkflowCard key={wf.id} wf={wf} />)}
        </div>
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
          {recentRuns.map((run, i) => (
            <RunRow key={run.id} run={run} isLast={i === recentRuns.length - 1} />
          ))}
        </div>
      </div>
    </div>
  );
}

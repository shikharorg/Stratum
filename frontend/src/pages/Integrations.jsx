import { useState } from 'react';
import { colors, typography } from '../theme';
import SectionHeader from '../components/SectionHeader';
import { mockConnectors, mockAvailableIntegrations } from '../mock/data';

function formatCount(n) {
  return n.toLocaleString('en-US');
}

function ConnectorCard({ connector }) {
  const [hovered, setHovered] = useState(false);
  const [syncHovered, setSyncHovered] = useState(false);
  const isError = connector.status === 'error';

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        backgroundColor: hovered ? colors.surfaceHover : colors.surface,
        border: `1px solid ${colors.border}`,
        borderLeftWidth: isError ? '4px' : '1px',
        borderLeftColor: isError ? colors.error : colors.border,
        borderRadius: '6px',
        padding: '16px',
        transition: 'background-color 0.15s ease',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '12px' }}>
        <div>
          <div style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.base,
            fontWeight: typography.weights.medium,
            color: colors.text,
            marginBottom: '3px',
          }}>
            {connector.name}
          </div>
          <div style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.sm,
            color: colors.textMuted,
            marginBottom: isError ? '4px' : '0',
          }}>
            {connector.type}
          </div>
          {isError && (
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
              onMouseEnter={() => setSyncHovered(true)}
              onMouseLeave={() => setSyncHovered(false)}
              style={{
                fontFamily: typography.fontUI,
                fontSize: typography.sizes.sm,
                fontWeight: typography.weights.regular,
                color: syncHovered ? colors.text : colors.textSecondary,
                backgroundColor: syncHovered ? colors.surfaceHover : colors.surface,
                border: `1px solid ${colors.border}`,
                borderRadius: '4px',
                padding: '4px 10px',
                cursor: 'pointer',
                transition: 'color 0.15s ease, background-color 0.15s ease',
              }}
            >
              Sync now
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
            {connector.lastSync}
          </span>
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

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '36px' }}>
        {mockConnectors.map(connector => (
          <ConnectorCard key={connector.id} connector={connector} />
        ))}
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

import { useState } from 'react';
import { colors, typography } from '../theme';
import SectionHeader from '../components/SectionHeader';
import { mockTeamMembers, mockTenant, mockProfile } from '../mock/data';

function InlineButton({ children, onClick }) {
  const [hovered, setHovered] = useState(false);
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.xs,
        fontWeight: typography.weights.regular,
        color: hovered ? colors.text : colors.textSecondary,
        backgroundColor: hovered ? colors.surfaceHover : colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: '4px',
        padding: '4px 10px',
        cursor: 'pointer',
        transition: 'color 0.15s ease, background-color 0.15s ease',
      }}
    >
      {children}
    </button>
  );
}

function FieldRow({ label, children, isLast }) {
  return (
    <div style={{
      padding: '12px 16px',
      borderBottom: isLast ? 'none' : `1px solid ${colors.borderSubtle}`,
    }}>
      <div style={{
        fontFamily: typography.fontMono,
        fontSize: typography.sizes.xs,
        color: colors.textMuted,
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
        marginBottom: '4px',
      }}>
        {label}
      </div>
      {children}
    </div>
  );
}

function FieldText({ children, mono }) {
  return (
    <div style={{
      fontFamily: mono ? typography.fontMono : typography.fontUI,
      fontSize: typography.sizes.base,
      color: colors.text,
    }}>
      {children}
    </div>
  );
}

function Container({ children }) {
  return (
    <div style={{
      backgroundColor: colors.surface,
      border: `1px solid ${colors.border}`,
      borderRadius: '6px',
      marginBottom: '28px',
      overflow: 'hidden',
    }}>
      {children}
    </div>
  );
}

function MemberRow({ member, isLast }) {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 16px',
        borderBottom: isLast ? 'none' : `1px solid ${colors.borderSubtle}`,
        backgroundColor: hovered ? colors.surfaceHover : 'transparent',
        transition: 'background-color 0.15s ease',
      }}
    >
      <div>
        <div style={{
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.base,
          color: colors.text,
        }}>
          {member.name}
        </div>
        <div style={{
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.xs,
          color: colors.textMuted,
          marginTop: '1px',
        }}>
          {member.email}
        </div>
      </div>
      {member.role === 'Admin' ? (
        <span style={{
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.xs,
          color: colors.text,
          backgroundColor: colors.surface,
          border: `1px solid ${colors.border}`,
          borderRadius: '3px',
          padding: '2px 8px',
        }}>
          {member.role}
        </span>
      ) : (
        <span style={{
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.xs,
          color: colors.textMuted,
        }}>
          {member.role}
        </span>
      )}
    </div>
  );
}

export default function Settings() {
  const [inviteHovered, setInviteHovered] = useState(false);

  return (
    <div style={{ maxWidth: '680px' }}>
      <div style={{
        fontFamily: typography.fontUI,
        fontSize: typography.sizes.xl,
        fontWeight: typography.weights.semibold,
        color: colors.text,
        marginBottom: '28px',
      }}>
        Settings
      </div>

      <div>
        <SectionHeader>Team</SectionHeader>
        <Container>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 16px',
            borderBottom: `1px solid ${colors.borderSubtle}`,
          }}>
            <span style={{
              fontFamily: typography.fontMono,
              fontSize: typography.sizes.xs,
              color: colors.textMuted,
            }}>
              {mockTeamMembers.length} members
            </span>
            <button
              onMouseEnter={() => setInviteHovered(true)}
              onMouseLeave={() => setInviteHovered(false)}
              style={{
                fontFamily: typography.fontUI,
                fontSize: typography.sizes.xs,
                fontWeight: typography.weights.regular,
                color: inviteHovered ? colors.text : colors.textSecondary,
                backgroundColor: inviteHovered ? colors.surfaceHover : colors.surface,
                border: `1px solid ${colors.border}`,
                borderRadius: '4px',
                padding: '4px 10px',
                cursor: 'pointer',
                transition: 'color 0.15s ease, background-color 0.15s ease',
              }}
            >
              + Invite
            </button>
          </div>
          {mockTeamMembers.map((member, i) => (
            <MemberRow key={member.id} member={member} isLast={i === mockTeamMembers.length - 1} />
          ))}
        </Container>
      </div>

      <div>
        <SectionHeader>Workspace</SectionHeader>
        <Container>
          <FieldRow label="Name">
            <FieldText>{mockTenant.name}</FieldText>
          </FieldRow>
          <FieldRow label="Workspace URL">
            <FieldText mono>app.stratum.ai/{mockTenant.slug}</FieldText>
          </FieldRow>
          <FieldRow label="API Key" isLast>
            <FieldText mono>{mockTenant.apiKeyPreview}****************</FieldText>
            <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
              <InlineButton>Copy</InlineButton>
              <InlineButton>Regenerate</InlineButton>
            </div>
          </FieldRow>
        </Container>
      </div>

      <div>
        <SectionHeader>Account</SectionHeader>
        <Container>
          <FieldRow label="Email">
            <FieldText>{mockProfile.email}</FieldText>
          </FieldRow>
          <FieldRow label="Password" isLast>
            <FieldText>••••••••</FieldText>
            <div style={{ marginTop: '8px' }}>
              <InlineButton>Change Password</InlineButton>
            </div>
          </FieldRow>
        </Container>
      </div>
    </div>
  );
}

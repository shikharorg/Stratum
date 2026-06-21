import { useState, useEffect } from 'react';
import { colors, typography } from '../theme';
import SectionHeader from '../components/SectionHeader';
import { mockTenant, mockProfile } from '../mock/data';
import apiClient from '../api/client';

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

const ROLE_LABELS = {
  tenant_admin: 'Admin',
  editor: 'Editor',
  viewer: 'Viewer',
};

function RoleBadge({ role }) {
  const label = ROLE_LABELS[role] || role;
  const isAdmin = role === 'tenant_admin';
  return (
    <span style={{
      fontFamily: typography.fontUI,
      fontSize: typography.sizes.xs,
      color: isAdmin ? colors.text : colors.textMuted,
      backgroundColor: isAdmin ? colors.surface : 'transparent',
      border: isAdmin ? `1px solid ${colors.border}` : 'none',
      borderRadius: '3px',
      padding: isAdmin ? '2px 8px' : '0',
    }}>
      {label}
    </span>
  );
}

function MemberRow({ user, isLast, isSelf, onRemove }) {
  const [hovered, setHovered] = useState(false);
  const [removing, setRemoving] = useState(false);

  async function handleRemove() {
    setRemoving(true);
    try {
      await apiClient.delete(`/api/v1/identity/users/${user.id}`);
      onRemove(user.id);
    } catch {
      setRemoving(false);
    }
  }

  const role = user.roles?.[0];
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
          {user.full_name || user.email}
        </div>
        {user.full_name && (
          <div style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.xs,
            color: colors.textMuted,
            marginTop: '1px',
          }}>
            {user.email}
          </div>
        )}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {role && <RoleBadge role={role} />}
        {!isSelf && hovered && (
          <button
            onClick={handleRemove}
            disabled={removing}
            style={{
              fontFamily: typography.fontUI,
              fontSize: typography.sizes.xs,
              color: colors.textMuted,
              background: 'none',
              border: 'none',
              cursor: removing ? 'default' : 'pointer',
              padding: '0',
              opacity: removing ? 0.5 : 1,
            }}
          >
            {removing ? 'Removing…' : 'Remove'}
          </button>
        )}
      </div>
    </div>
  );
}

export default function Settings() {
  const [users, setUsers] = useState([]);
  const [currentUserId, setCurrentUserId] = useState(null);
  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteHovered, setInviteHovered] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('editor');
  const [inviteError, setInviteError] = useState('');
  const [inviteLoading, setInviteLoading] = useState(false);

  useEffect(() => {
    apiClient.get('/api/v1/identity/users/me').then(({ data }) => {
      setCurrentUserId(data.id);
    }).catch(() => {});
    apiClient.get('/api/v1/identity/users').then(({ data }) => {
      setUsers(data.items);
    }).catch(() => {});
  }, []);

  function handleRemove(userId) {
    setUsers(prev => prev.filter(u => u.id !== userId));
  }

  async function handleInviteSubmit(e) {
    e.preventDefault();
    setInviteError('');
    setInviteLoading(true);
    try {
      await apiClient.post('/api/v1/identity/users', {
        email: inviteEmail,
        password: 'changeme123',
        full_name: inviteEmail,
        role: inviteRole,
      });
      const { data } = await apiClient.get('/api/v1/identity/users');
      setUsers(data.items);
      setInviteOpen(false);
      setInviteEmail('');
      setInviteRole('editor');
    } catch (err) {
      const detail = err.response?.data?.detail;
      setInviteError(typeof detail === 'string' ? detail : 'Failed to invite user');
    } finally {
      setInviteLoading(false);
    }
  }

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
              {users.length} members
            </span>
            <button
              onMouseEnter={() => setInviteHovered(true)}
              onMouseLeave={() => setInviteHovered(false)}
              onClick={() => { setInviteOpen(o => !o); setInviteError(''); }}
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

          {inviteOpen && (
            <form
              onSubmit={handleInviteSubmit}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 16px',
                borderBottom: `1px solid ${colors.borderSubtle}`,
                backgroundColor: colors.surfaceHover,
                flexWrap: 'wrap',
              }}
            >
              <input
                type="email"
                placeholder="email@example.com"
                value={inviteEmail}
                onChange={e => setInviteEmail(e.target.value)}
                required
                style={{
                  fontFamily: typography.fontUI,
                  fontSize: typography.sizes.xs,
                  color: colors.text,
                  backgroundColor: colors.surface,
                  border: `1px solid ${colors.border}`,
                  borderRadius: '4px',
                  padding: '4px 8px',
                  outline: 'none',
                  flex: '1',
                  minWidth: '160px',
                }}
              />
              <select
                value={inviteRole}
                onChange={e => setInviteRole(e.target.value)}
                style={{
                  fontFamily: typography.fontUI,
                  fontSize: typography.sizes.xs,
                  color: colors.text,
                  backgroundColor: colors.surface,
                  border: `1px solid ${colors.border}`,
                  borderRadius: '4px',
                  padding: '4px 8px',
                  cursor: 'pointer',
                  outline: 'none',
                }}
              >
                <option value="editor">Member</option>
                <option value="tenant_admin">Admin</option>
                <option value="viewer">Viewer</option>
              </select>
              <button
                type="submit"
                disabled={inviteLoading}
                style={{
                  fontFamily: typography.fontUI,
                  fontSize: typography.sizes.xs,
                  color: colors.text,
                  backgroundColor: colors.surface,
                  border: `1px solid ${colors.border}`,
                  borderRadius: '4px',
                  padding: '4px 10px',
                  cursor: inviteLoading ? 'default' : 'pointer',
                  opacity: inviteLoading ? 0.6 : 1,
                }}
              >
                {inviteLoading ? 'Inviting…' : 'Submit'}
              </button>
              {inviteError && (
                <span style={{
                  fontFamily: typography.fontUI,
                  fontSize: typography.sizes.xs,
                  color: colors.error,
                  width: '100%',
                }}>
                  {inviteError}
                </span>
              )}
            </form>
          )}

          {users.map((user, i) => (
            <MemberRow
              key={user.id}
              user={user}
              isLast={i === users.length - 1}
              isSelf={user.id === currentUserId}
              onRemove={handleRemove}
            />
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
            <FieldText mono>localhost:5173/{mockTenant.slug}</FieldText>
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

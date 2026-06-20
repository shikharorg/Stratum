import { useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  BookOpen,
  GitBranch,
  Search,
  Plug,
  Settings,
} from 'lucide-react';
import { colors, typography } from '../theme';
import { logout } from '../api/auth';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/knowledge', icon: BookOpen, label: 'Docs' },
  { to: '/workflows', icon: GitBranch, label: 'Workflows' },
  { to: '/search', icon: Search, label: 'Search' },
  { to: '/integrations', icon: Plug, label: 'Integrations' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

function NavItem({ to, icon: Icon, label }) {
  const location = useLocation();
  const isActive = to === '/' ? location.pathname === '/' : location.pathname.startsWith(to);
  const [hovered, setHovered] = useState(false);

  return (
    <NavLink
      to={to}
      end={to === '/'}
      style={{ textDecoration: 'none' }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        margin: '1px 8px',
        padding: '7px 10px',
        borderRadius: '6px',
        backgroundColor: isActive ? '#f3f2f0' : hovered ? '#f3f2f0' : 'transparent',
        transition: 'background-color 0.15s ease',
        cursor: 'pointer',
      }}>
        <Icon
          size={15}
          color={isActive ? colors.text : hovered ? colors.text : colors.textSecondary}
        />
        <span style={{
          fontFamily: typography.fontUI,
          fontSize: '13px',
          fontWeight: isActive ? typography.weights.medium : 500,
          color: isActive ? colors.text : hovered ? colors.text : colors.textSecondary,
          transition: 'color 0.15s ease',
        }}>
          {label}
        </span>
      </div>
    </NavLink>
  );
}

export default function Sidebar() {
  const navigate = useNavigate();
  const [signOutHovered, setSignOutHovered] = useState(false);

  async function handleSignOut() {
    await logout();
    navigate('/login');
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '220px',
      height: '100vh',
      backgroundColor: colors.surface,
      borderRight: '1px solid #e2e1de',
      display: 'flex',
      flexDirection: 'column',
      zIndex: 100,
    }}>
      <div style={{
        padding: '20px 16px 18px',
        borderBottom: '1px solid #e2e1de',
      }}>
        <span style={{
          fontFamily: typography.fontMono,
          fontSize: typography.sizes.base,
          fontWeight: typography.weights.medium,
          color: colors.text,
        }}>
          Stratum
        </span>
      </div>

      <nav style={{ flex: 1, paddingTop: '8px' }}>
        {navItems.map(item => (
          <NavItem key={item.to} {...item} />
        ))}
      </nav>

      <div style={{
        padding: '16px',
        borderTop: '1px solid #e2e1de',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
      }}>
        <div style={{
          width: '28px',
          height: '28px',
          borderRadius: '50%',
          backgroundColor: colors.accentMuted,
          border: '1px solid #e2e1de',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}>
          <span style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.sm,
            fontWeight: typography.weights.medium,
            color: colors.textSecondary,
          }}>
            A
          </span>
        </div>
        <div style={{
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.xs,
          color: colors.textMuted,
        }}>
          Admin
        </div>
      </div>

      <div
        onMouseEnter={() => setSignOutHovered(true)}
        onMouseLeave={() => setSignOutHovered(false)}
        onClick={handleSignOut}
        style={{
          borderTop: '1px solid #e2e1de',
          padding: '10px 16px',
          fontFamily: typography.fontUI,
          fontSize: '11px',
          color: signOutHovered ? '#999' : '#bbb',
          cursor: 'pointer',
          transition: 'color 0.15s ease',
        }}
      >
        Sign Out
      </div>
    </div>
  );
}

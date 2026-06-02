import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  BookOpen,
  GitBranch,
  Search,
  Plug,
  Settings,
} from 'lucide-react';
import { colors, typography } from '../theme';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/knowledge', icon: BookOpen, label: 'Knowledge' },
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
        padding: '7px 16px',
        borderLeft: isActive ? `2px solid ${colors.accent}` : '2px solid transparent',
        backgroundColor: isActive ? colors.accentMuted : hovered ? colors.surfaceHover : 'transparent',
        transition: 'background-color 0.15s ease',
        cursor: 'pointer',
      }}>
        <Icon
          size={15}
          color={isActive ? colors.text : hovered ? colors.text : colors.textSecondary}
        />
        <span style={{
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.base,
          fontWeight: isActive ? typography.weights.medium : typography.weights.regular,
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
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '220px',
      height: '100vh',
      backgroundColor: colors.surface,
      borderRight: `1px solid ${colors.border}`,
      display: 'flex',
      flexDirection: 'column',
      zIndex: 100,
    }}>
      <div style={{
        padding: '20px 16px 16px',
        borderBottom: `1px solid ${colors.border}`,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
          <div style={{
            width: '24px',
            height: '24px',
            backgroundColor: colors.border,
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}>
            <div style={{
              width: '10px',
              height: '10px',
              backgroundColor: colors.accent,
              borderRadius: '2px',
            }} />
          </div>
          <span style={{
            fontFamily: typography.fontMono,
            fontSize: typography.sizes.base,
            fontWeight: typography.weights.medium,
            color: colors.text,
          }}>
            Stratum
          </span>
        </div>
        <div style={{
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.xs,
          color: colors.textMuted,
          paddingLeft: '34px',
        }}>
          stratum-test
        </div>
      </div>

      <nav style={{ flex: 1, paddingTop: '8px' }}>
        {navItems.map(item => (
          <NavItem key={item.to} {...item} />
        ))}
      </nav>

      <div style={{
        padding: '16px',
        borderTop: `1px solid ${colors.border}`,
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
      }}>
        <div style={{
          width: '28px',
          height: '28px',
          borderRadius: '50%',
          backgroundColor: colors.accentMuted,
          border: `1px solid ${colors.border}`,
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
        <div style={{ minWidth: 0 }}>
          <div style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.sm,
            fontWeight: typography.weights.medium,
            color: colors.text,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}>
            admin@test.com
          </div>
          <div style={{
            fontFamily: typography.fontUI,
            fontSize: typography.sizes.xs,
            color: colors.textMuted,
          }}>
            Admin
          </div>
        </div>
      </div>
    </div>
  );
}

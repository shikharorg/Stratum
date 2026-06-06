import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { colors, typography } from '../theme';
import { login } from '../api/auth';
import useAuthStore from '../store/authStore';

export default function Login() {
  const navigate = useNavigate();
  const { isLoading } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [emailFocused, setEmailFocused] = useState(false);
  const [passwordFocused, setPasswordFocused] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    const result = await login(email, password);
    if (result.success) {
      navigate('/');
    } else {
      setError(result.error);
    }
  }

  const inputStyle = (focused) => ({
    width: '100%',
    fontFamily: typography.fontUI,
    fontSize: typography.sizes.base,
    color: colors.text,
    backgroundColor: colors.surface,
    border: `1px solid ${focused ? colors.textMuted : colors.borderSubtle}`,
    borderRadius: '6px',
    padding: '10px 14px',
    outline: 'none',
    transition: 'border-color 0.15s ease',
    boxSizing: 'border-box',
  });

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: colors.bg,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <div style={{ width: '100%', maxWidth: '360px', padding: '0 24px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '40px' }}>
          <div style={{
            width: '24px',
            height: '24px',
            backgroundColor: colors.border,
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '10px',
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
            fontSize: typography.sizes.lg,
            fontWeight: typography.weights.medium,
            color: colors.text,
          }}>
            Stratum
          </span>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            onFocus={() => setEmailFocused(true)}
            onBlur={() => setEmailFocused(false)}
            required
            style={inputStyle(emailFocused)}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            onFocus={() => setPasswordFocused(true)}
            onBlur={() => setPasswordFocused(false)}
            required
            style={inputStyle(passwordFocused)}
          />
          <button
            type="submit"
            disabled={isLoading}
            style={{
              marginTop: '8px',
              width: '100%',
              fontFamily: typography.fontUI,
              fontSize: typography.sizes.base,
              fontWeight: typography.weights.medium,
              color: colors.bg,
              backgroundColor: colors.accent,
              border: 'none',
              borderRadius: '6px',
              padding: '10px',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              opacity: isLoading ? 0.7 : 1,
              transition: 'opacity 0.15s ease',
            }}
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
          {error && (
            <div style={{
              fontFamily: typography.fontUI,
              fontSize: typography.sizes.sm,
              color: colors.error,
              marginTop: '8px',
            }}>
              {error}
            </div>
          )}
        </form>

        <div style={{
          marginTop: '24px',
          textAlign: 'center',
          fontFamily: typography.fontUI,
          fontSize: typography.sizes.xs,
          color: colors.textMuted,
        }}>
          AI Operations Platform
        </div>
      </div>
    </div>
  );
}

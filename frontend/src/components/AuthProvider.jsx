import { useEffect } from 'react';
import { refreshToken } from '../api/auth';
import useAuthStore from '../store/authStore';

export default function AuthProvider({ children }) {
  const { isInitializing, setInitializing } = useAuthStore();

  useEffect(() => {
    refreshToken().finally(() => setInitializing(false));
  }, []);

  if (isInitializing) return null;

  return children;
}

import authClient from './authClient';
import useAuthStore from '../store/authStore';

export async function login(email, password) {
  const { setAuth, setLoading } = useAuthStore.getState();
  setLoading(true);
  try {
    const { data } = await authClient.post('/api/v1/identity/auth/login', {
      email,
      password,
      tenant_slug: 'stratum-test',
    });
    setAuth(data.access_token);
    return { success: true };
  } catch (error) {
    if (error.response?.status === 401) {
      return { success: false, error: 'Invalid email or password' };
    }
    return { success: false, error: 'Unable to reach server' };
  } finally {
    setLoading(false);
  }
}

export async function logout() {
  const { clearAuth } = useAuthStore.getState();
  try {
    await authClient.post('/api/v1/identity/auth/logout');
  } finally {
    clearAuth();
  }
}

export async function refreshToken() {
  const { setAuth, clearAuth } = useAuthStore.getState();
  try {
    const { data } = await authClient.post('/api/v1/identity/auth/refresh');
    setAuth(data.access_token);
    return data.access_token;
  } catch {
    clearAuth();
    return null;
  }
}

import axios from 'axios';
import { API_BASE_URL } from '../config';
import useAuthStore from '../store/authStore';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

let refreshPromise = null;

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;

    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error);
    }

    original._retry = true;

    try {
      if (!refreshPromise) {
        const { refreshToken } = await import('./auth.js');
        refreshPromise = refreshToken().finally(() => {
          refreshPromise = null;
        });
      }

      await refreshPromise;

      const newToken = useAuthStore.getState().accessToken;
      if (newToken) {
        original.headers.Authorization = `Bearer ${newToken}`;
      }
      return apiClient(original);
    } catch {
      useAuthStore.getState().clearAuth();
      return Promise.reject(error);
    }
  },
);

export default apiClient;

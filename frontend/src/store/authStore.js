import { create } from 'zustand';

const useAuthStore = create((set) => ({
  accessToken: null,
  isAuthenticated: false,
  isInitializing: true,
  isLoading: false,

  setAuth: (accessToken) => set({ accessToken, isAuthenticated: true }),
  clearAuth: () => set({ accessToken: null, isAuthenticated: false }),
  setInitializing: (isInitializing) => set({ isInitializing }),
  setLoading: (isLoading) => set({ isLoading }),
}));

export default useAuthStore;

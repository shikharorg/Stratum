import { Navigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';

export default function ProtectedRoute({ children }) {
  const { isInitializing, isAuthenticated } = useAuthStore();

  if (isInitializing) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return children;
}

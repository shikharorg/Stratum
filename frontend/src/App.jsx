import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { colors, typography } from './theme';
import AuthProvider from './components/AuthProvider';
import ProtectedRoute from './components/ProtectedRoute';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Knowledge from './pages/Knowledge';
import Workflows from './pages/Workflows';
import Search from './pages/Search';
import Integrations from './pages/Integrations';
import Settings from './pages/Settings';

function AppLayout() {
  return (
    <div style={{
      fontFamily: typography.fontUI,
      color: colors.text,
      minHeight: '100vh',
      backgroundColor: '#ffffff',
    }}>
      <Sidebar />
      <main style={{
        marginLeft: '220px',
        padding: '28px 48px',
        minHeight: '100vh',
        backgroundColor: '#ffffff',
      }}>
        <div style={{ maxWidth: '900px' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/knowledge" element={<Knowledge />} />
            <Route path="/workflows" element={<Workflows />} />
            <Route path="/search" element={<Search />} />
            <Route path="/integrations" element={<Integrations />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

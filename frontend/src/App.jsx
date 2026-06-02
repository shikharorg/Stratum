import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { colors, typography } from './theme';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Knowledge from './pages/Knowledge';
import Workflows from './pages/Workflows';
import Search from './pages/Search';
import Integrations from './pages/Integrations';
import Settings from './pages/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <div style={{
        fontFamily: typography.fontUI,
        color: colors.text,
        minHeight: '100vh',
        backgroundColor: colors.bg,
      }}>
        <Sidebar />
        <main style={{
          marginLeft: '220px',
          padding: '28px 48px',
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
    </BrowserRouter>
  );
}

import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
import AboutPage from './pages/AboutPage';
import AnalyzePage from './pages/AnalyzePage';
import AuthPage from './pages/AuthPage';
import CompanyPage from './pages/CompanyPage';
import Dashboard from './pages/Dashboard';
import HistoryPage from './pages/HistoryPage';
import Landing from './pages/Landing';
import OcrPage from './pages/OcrPage';
import ProfilePage from './pages/ProfilePage';
import ReportsPage from './pages/ReportsPage';
import ResultPage from './pages/ResultPage';
import UrlPage from './pages/UrlPage';

function Guard({ children }) {
  return <ProtectedRoute>{children}</ProtectedRoute>;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="flex min-h-screen flex-col">
          <Navbar />
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/auth" element={<AuthPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/dashboard" element={<Guard><Dashboard /></Guard>} />
              <Route path="/analyze" element={<Guard><AnalyzePage /></Guard>} />
              <Route path="/ocr" element={<Guard><OcrPage /></Guard>} />
              <Route path="/result/:id" element={<Guard><ResultPage /></Guard>} />
              <Route path="/company" element={<Guard><CompanyPage /></Guard>} />
              <Route path="/url" element={<Guard><UrlPage /></Guard>} />
              <Route path="/reports" element={<Guard><ReportsPage /></Guard>} />
              <Route path="/history" element={<Guard><HistoryPage /></Guard>} />
              <Route path="/profile" element={<Guard><ProfilePage /></Guard>} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          <footer className="border-t border-ink/10 py-4 text-center text-xs text-ink/50">
            AI JobShield — local mini project · guidance only, not a verdict
          </footer>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

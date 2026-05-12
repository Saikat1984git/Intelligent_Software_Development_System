import { Routes, Route, Outlet, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import DashboardLayout from './components/DashboardLayout';
import Codegen from './pages/Codegen';
import Codeedit from './pages/Codeedit';
import BugSupport from './pages/BugSupport';
import Login from './pages/Login';

// Protected Route Wrapper
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

// Public Route - Redirect if already authenticated
const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/codegen" replace />;
  }

  return children;
};

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={
        <PublicRoute>
          <Login />
        </PublicRoute>
      } />

      {/* Protected Routes */}
      <Route element={<ProtectedRoute><DashboardLayout><Outlet /></DashboardLayout></ProtectedRoute>}>
        <Route path="/" element={<Codegen />} />
        <Route path="/codegen" element={<Codegen />} />
        <Route path="/codemod" element={<Codeedit />} />
        <Route path="/support" element={<BugSupport />} />
      </Route>

      {/* 404 Page */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

export default App;
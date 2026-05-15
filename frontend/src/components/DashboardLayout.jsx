import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import TopNavbar from './organisms/TopNavbar';
import SideNavbar from './organisms/SideNavbar';

/* ============================================================
   DashboardLayout
   Shell layout — wraps all protected pages.
   TopNavbar and SideNavbar are now separate organism files.
   All logic and behaviour identical to the original.
   ============================================================ */

const DashboardLayout = ({ children }) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(() => {
    const saved = localStorage.getItem('sidebarOpen');
    return saved !== null ? JSON.parse(saved) : true;
  });

  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    const saved = localStorage.getItem('sidebarCollapsed');
    return saved !== null ? JSON.parse(saved) : true;
  });

  React.useEffect(() => {
    localStorage.setItem('sidebarOpen', JSON.stringify(isSidebarOpen));
  }, [isSidebarOpen]);

  React.useEffect(() => {
    localStorage.setItem('sidebarCollapsed', JSON.stringify(isSidebarCollapsed));
  }, [isSidebarCollapsed]);

  const { darkMode, toggleTheme } = useTheme();
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const sidebarMarginClass = isSidebarCollapsed ? 'lg:ml-16' : 'lg:ml-64';

  return (
    <div className={`h-screen flex flex-col font-sans transition-colors duration-300 ${
      darkMode ? 'bg-slate-900 text-white' : 'bg-slate-50 text-slate-900'
    }`}>

      <TopNavbar
        isSidebarOpen={isSidebarOpen}
        setIsSidebarOpen={setIsSidebarOpen}
        darkMode={darkMode}
        toggleTheme={toggleTheme}
        user={user}
        onLogout={handleLogout}
      />

      <div className="flex h-full overflow-hidden pt-16 lg:pt-0">
        <SideNavbar
          isSidebarOpen={isSidebarOpen}
          setIsSidebarOpen={setIsSidebarOpen}
          isSidebarCollapsed={isSidebarCollapsed}
          setIsSidebarCollapsed={setIsSidebarCollapsed}
          darkMode={darkMode}
          onLogout={handleLogout}
        />

        <main className={`flex-1 overflow-y-auto transition-all duration-300 ${sidebarMarginClass} ${
          darkMode ? 'bg-slate-900 text-slate-200' : 'bg-slate-50 text-slate-800'
        }`}>
          {children}
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;

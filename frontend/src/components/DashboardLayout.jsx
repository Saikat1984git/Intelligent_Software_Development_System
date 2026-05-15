import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import TopNavbar from './organisms/TopNavbar';
import SideNavbar from './organisms/SideNavbar';

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
    /*
      Root: 100dvh (dynamic viewport — handles mobile browsers correctly)
      flex flex-col — stacks TopNavbar + content area vertically
    */
    <div className={`font-sans transition-colors duration-300 ${darkMode ? 'bg-slate-900 text-white' : 'bg-slate-50 text-slate-900'
      }`} style={{ height: '100dvh', display: 'flex', flexDirection: 'column' }}>

      {/* Fixed top navbar — takes up 4rem (h-16) */}
      <TopNavbar
        isSidebarOpen={isSidebarOpen}
        setIsSidebarOpen={setIsSidebarOpen}
        darkMode={darkMode}
        toggleTheme={toggleTheme}
        user={user}
        onLogout={handleLogout}
      />

      {/*
        Content row: sits directly BELOW the navbar.
        TopNavbar is fixed so we add a spacer div (h-16) to push
        this row below it — avoids the pt-16 overflow problem.
        flex-1 min-h-0 — takes remaining height, allows shrinking.
      */}
      <div style={{ height: '4rem', flexShrink: 0 }} /> {/* spacer for fixed navbar */}

      <div className={`flex flex-1 min-h-0 overflow-hidden`}>
        <SideNavbar
          isSidebarOpen={isSidebarOpen}
          setIsSidebarOpen={setIsSidebarOpen}
          isSidebarCollapsed={isSidebarCollapsed}
          setIsSidebarCollapsed={setIsSidebarCollapsed}
          darkMode={darkMode}
          onLogout={handleLogout}
        />

        {/*
          main: flex-1 min-h-0 overflow-hidden
          Pages use h-full to fill this exactly.
          overflow-hidden — each page controls its own scroll.
        */}
        <main className={`flex-1 min-h-0 overflow-hidden transition-all duration-300 ${sidebarMarginClass} ${darkMode ? 'bg-slate-900 text-slate-200' : 'bg-slate-50 text-slate-800'
          }`}>
          {children}
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
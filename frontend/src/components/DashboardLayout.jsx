import React, { useState } from 'react';
import {
  Code2,
  PenTool,
  Layout,
  Menu,
  Bell,
  User,
  Sun,
  Moon,
  LogOut,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const DashboardLayout = ({ children }) => {
  // State for Sidebar
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true);
  const { darkMode, toggleTheme } = useTheme();

  // Calculate sidebar width class for main content margin
  const sidebarMarginClass = isSidebarCollapsed ? 'lg:ml-16' : 'lg:ml-64';

  return (
    <div
        className={`min-h-screen flex flex-col font-sans transition-colors duration-300 ${
          darkMode
            ? 'bg-slate-900 text-white'
            : 'bg-slate-50 text-slate-900'
        }`}
      >
      {/* --- TOP NAVBAR --- */}
      <TopNavbar
        isSidebarOpen={isSidebarOpen}
        setIsSidebarOpen={setIsSidebarOpen}
        isSidebarCollapsed={isSidebarCollapsed}
        setIsSidebarCollapsed={setIsSidebarCollapsed}
        darkMode={darkMode}
        toggleTheme={toggleTheme}
      />

      <div className="flex flex-1 overflow-hidden pt-16 lg:pt-0">
        {/* --- LEFT SIDEBAR --- */}
        <SideNavbar
          isSidebarOpen={isSidebarOpen}
          setIsSidebarOpen={setIsSidebarOpen}
          isSidebarCollapsed={isSidebarCollapsed}
          setIsSidebarCollapsed={setIsSidebarCollapsed}
          darkMode={darkMode}
        />

        {/* --- PAGE CONTENT (Route Injection Point) --- */}
        <main
          className={`flex-1 overflow-y-auto transition-all duration-300 ${sidebarMarginClass} ${
            darkMode
              ? 'bg-slate-900 text-slate-200'
              : 'bg-slate-50 text-slate-800'
          }`}
        >
          {children}
        </main>
      </div>
    </div>
  );
};

// --- Sub-Component: Top Header ---
const TopNavbar = ({ isSidebarOpen, setIsSidebarOpen, darkMode, toggleTheme }) => {
  return (
    <header
  className={`
    z-40 w-full h-16 flex items-center justify-between px-4 fixed top-0 left-0 shadow-sm transition-colors duration-300 backdrop-blur-md
    ${darkMode
      ? 'bg-gradient-to-r from-slate-900 via-slate-900 to-slate-800'
      : 'bg-white/90 border-b border-slate-200/50'
    }
  `}
>
      <div className="flex items-center gap-4">
        {/* Mobile Toggle - Hidden on large screens */}
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className={`p-2 rounded-lg transition-all lg:hidden ${
            darkMode ? 'text-white/90 hover:text-white hover:bg-white/10' : 'text-slate-700 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Menu size={24} />
        </button>

        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className={`font-bold px-3 py-1.5 rounded-lg text-xl shadow-sm transition-colors duration-300 ${
            darkMode
              ? 'bg-gradient-to-br from-cyan-400 to-cyan-600 text-slate-900'
              : 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
          }`}>
            iSDS
          </div>
          <span className={`font-semibold text-lg hidden md:block tracking-wide transition-colors duration-300 ${
            darkMode ? 'text-white opacity-90' : 'text-slate-700'
          }`}>
            Intelligent System Development System
          </span>
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-2">
        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className={`relative p-2.5 rounded-xl transition-all duration-300 group overflow-hidden ${
            darkMode
              ? 'hover:bg-white/10'
              : 'hover:bg-slate-100'
          }`}
          title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          <div className="relative z-10 transition-transform duration-300 group-hover:rotate-12">
            {darkMode ? (
              <Sun size={20} className="text-amber-400" />
            ) : (
              <Moon size={20} className="text-slate-600" />
            )}
          </div>
          {/* Glow effect */}
          <div className={`absolute inset-0 scale-0 group-hover:scale-100 transition-transform duration-300 rounded-full ${
            darkMode ? 'bg-white/5' : 'bg-blue-500/10'
          }`} />
        </button>

        <button className={`relative p-2.5 rounded-xl transition-all ${
          darkMode ? 'hover:bg-white/10' : 'hover:bg-slate-100'
        }`}>
          <Bell size={20} className={darkMode ? 'text-white/90' : 'text-slate-600'} />
          <span className={`absolute top-1.5 right-1.5 w-2 h-2 bg-red-400 rounded-full ring-2 ${
            darkMode ? 'ring-blue-400' : 'ring-white'
          }`}></span>
        </button>

        <div className={`h-9 w-9 rounded-xl flex items-center justify-center cursor-pointer transition-all ${
          darkMode
            ? 'bg-gradient-to-br from-white/20 to-white/5 border border-white/20 hover:bg-white/10'
            : 'bg-slate-100 border border-slate-200 hover:bg-slate-200'
        }`}>
          <User size={18} className={darkMode ? 'text-white/90' : 'text-slate-600'} />
        </div>
      </div>
    </header>
  );
};

// --- Sub-Component: Left Sidebar ---
const SideNavbar = ({ isSidebarOpen, setIsSidebarOpen, isSidebarCollapsed, setIsSidebarCollapsed, darkMode }) => {
  // Navigation Links
  const navItems = [
    { id: 'codegen', label: 'Code Generation', icon: <Code2 size={20} /> },
    { id: 'codemod', label: 'Code Modification', icon: <PenTool size={20} /> },
    { id: 'sysdesign', label: 'System Design', icon: <Layout size={20} /> },
  ];

  // Calculate width based on collapsed state
  const sidebarWidth = isSidebarCollapsed ? 'lg:w-16' : 'lg:w-64';

  return (
    <>
      {/* Mobile Overlay */}
      <div
        className={`fixed inset-0 bg-black/50 z-20 lg:hidden transition-opacity duration-300 ${isSidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={() => setIsSidebarOpen(false)}
      />

      <aside
        className={`
          fixed
          top-16
          left-0
          z-30
          h-[calc(100vh-4rem)]
          ${sidebarWidth}

          ${darkMode
            ? 'bg-slate-900 border-slate-800'
            : 'bg-white border-slate-200'
          }

          transition-all duration-300 ease-in-out
          border-r
          ${darkMode ? 'shadow-xl' : 'shadow-sm'}

          ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}

          flex flex-col
        `}
      >
        {/* Collapse Button (visible on desktop) */}
        <button
          onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          className={`hidden lg:flex absolute -right-3 top-1/2 -translate-y-1/2 z-40 h-6 w-6 items-center justify-center rounded-full transition-colors ${
            darkMode
              ? 'bg-slate-900 border-slate-700 text-slate-400 hover:bg-slate-800'
              : 'bg-white border-slate-300 text-slate-600 hover:bg-slate-100'
          }`}
        >
          {isSidebarCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>

        <div className={`flex-1 py-6 overflow-hidden`}>
          {!isSidebarCollapsed && (
            <div className={`px-6 mb-4 text-xs font-bold uppercase tracking-widest ${
              darkMode ? 'text-slate-500' : 'text-slate-400'
            }`}>
              Core Modules
            </div>
          )}

          <nav className={`space-y-1 ${isSidebarCollapsed ? 'lg:flex lg:flex-col lg:items-center lg:px-0' : ''}`}>
            {navItems.map((item) => (
              <a
                key={item.id}
                href={`${item.id}`}
                className={`
                  group flex items-center gap-3 py-3 text-sm font-medium transition-all duration-200 border-l-4 border-transparent
                  ${darkMode
                    ? 'text-slate-400 hover:bg-slate-800/80 hover:text-white hover:border-cyan-500'
                    : 'text-slate-500 hover:bg-blue-50 hover:text-blue-600 hover:border-blue-500'
                  }
                  ${isSidebarCollapsed ? 'lg:justify-center lg:px-3 lg:w-full' : 'lg:px-6'}
                `}
              >
                <span className={`group-hover:scale-110 transition-transform flex-shrink-0 ${
                  darkMode ? 'group-hover:text-cyan-400' : 'text-blue-500'
                } ${isSidebarCollapsed ? 'lg:mx-0 lg:w-auto' : ''}`}>{item.icon}</span>
                {!isSidebarCollapsed && <span>{item.label}</span>}
              </a>
            ))}
          </nav>
        </div>

        {/* Footer */}
        <div className={`p-4 border-t transition-colors ${
          darkMode
            ? 'border-slate-800 bg-slate-950'
            : 'border-slate-100 bg-slate-50'
        } ${isSidebarCollapsed ? 'lg:px-2 lg:flex lg:justify-center' : ''}`}>
          <button className={`flex items-center gap-3 text-sm font-medium text-red-500 hover:text-red-600 hover:bg-red-500/10 rounded transition-colors ${
            isSidebarCollapsed ? 'lg:justify-center' : ''
          }`}>
            <LogOut size={18} />
            {!isSidebarCollapsed && <span>Logout</span>}
          </button>
        </div>
      </aside>
    </>
  );
};

export default DashboardLayout;
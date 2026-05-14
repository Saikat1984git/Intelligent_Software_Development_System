import React from 'react';
import { Code2, PenTool, Bug, ChevronLeft, ChevronRight } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';

/* ============================================================
   SideNavbar
   Extracted from DashboardLayout.jsx.
   Bug Support nav item added.
   Active route highlight based on current path.

   Props:
     isSidebarOpen        bool
     setIsSidebarOpen     fn
     isSidebarCollapsed   bool
     setIsSidebarCollapsed fn
     darkMode             bool
     onLogout             fn
   ============================================================ */

const NAV_ITEMS = [
  { id: 'codegen',  label: 'Code Generation',   icon: <Code2 size={20} />,  path: '/codegen' },
  { id: 'codemod',  label: 'Code Modification',  icon: <PenTool size={20} />, path: '/codemod' },
  { id: 'support',  label: 'Bug Support',         icon: <Bug size={20} />,    path: '/support' },
];

const SideNavbar = ({
  isSidebarOpen,
  setIsSidebarOpen,
  isSidebarCollapsed,
  setIsSidebarCollapsed,
  darkMode,
  onLogout,
}) => {
  const location = useLocation();
  const sidebarWidth = isSidebarCollapsed ? 'lg:w-16' : 'lg:w-64';

  return (
    <>
      {/* Mobile overlay */}
      <div
        className={`fixed inset-0 bg-black/50 z-20 lg:hidden transition-opacity duration-300 ${
          isSidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={() => setIsSidebarOpen(false)}
      />

      <aside
        className={`
          fixed top-16 left-0 z-30
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
        {/* Collapse toggle (desktop only) */}
        <button
          onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          className={`hidden lg:flex absolute -right-3 top-1/2 -translate-y-1/2 z-40
            h-6 w-6 items-center justify-center rounded-full border transition-colors ${
            darkMode
              ? 'bg-slate-900 border-slate-700 text-slate-400 hover:bg-slate-800'
              : 'bg-white border-slate-300 text-slate-600 hover:bg-slate-100'
          }`}
        >
          {isSidebarCollapsed
            ? <ChevronRight size={14} />
            : <ChevronLeft size={14} />
          }
        </button>

        <div className="flex-1 py-6 overflow-hidden">
          {!isSidebarCollapsed && (
            <div className={`px-6 mb-4 text-xs font-bold uppercase tracking-widest ${
              darkMode ? 'text-slate-500' : 'text-slate-400'
            }`}>
              Core Modules
            </div>
          )}

          <nav className={`space-y-1 ${
            isSidebarCollapsed ? 'lg:flex lg:flex-col lg:items-center lg:px-0' : ''
          }`}>
            {NAV_ITEMS.map((item) => {
              const isActive = location.pathname === item.path ||
                (item.path === '/codegen' && location.pathname === '/');

              return (
                <a
                  key={item.id}
                  href={item.path}
                  className={`
                    group flex items-center gap-3 py-3 text-sm font-medium
                    transition-all duration-200 border-l-4
                    ${isActive
                      ? darkMode
                        ? 'border-cyan-500 bg-slate-800/80 text-white'
                        : 'border-blue-500 bg-blue-50 text-blue-600'
                      : darkMode
                        ? 'border-transparent text-slate-400 hover:bg-slate-800/80 hover:text-white hover:border-cyan-500'
                        : 'border-transparent text-slate-500 hover:bg-blue-50 hover:text-blue-600 hover:border-blue-500'
                    }
                    ${isSidebarCollapsed
                      ? 'lg:justify-center lg:px-3 lg:w-full'
                      : 'lg:px-6'
                    }
                  `}
                  onClick={() => setIsSidebarOpen(false)}
                >
                  <span className={`group-hover:scale-110 transition-transform flex-shrink-0 ${
                    isActive
                      ? darkMode ? 'text-cyan-400' : 'text-blue-500'
                      : darkMode ? 'group-hover:text-cyan-400' : 'text-blue-500'
                  }`}>
                    {item.icon}
                  </span>
                  {!isSidebarCollapsed && <span>{item.label}</span>}
                </a>
              );
            })}
          </nav>
        </div>
      </aside>
    </>
  );
};

export default SideNavbar;

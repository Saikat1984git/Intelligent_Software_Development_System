import React, { useState } from 'react';
import { Menu, Bell, Sun, Moon, LogOut } from 'lucide-react';

/* ============================================================
   TopNavbar
   Extracted from DashboardLayout.jsx — zero logic changes.

   Props:
     isSidebarOpen      bool
     setIsSidebarOpen   fn
     darkMode           bool
     toggleTheme        fn
     user               { name?, username?, email? } | null
     onLogout           fn
   ============================================================ */

const TopNavbar = ({
  isSidebarOpen,
  setIsSidebarOpen,
  darkMode,
  toggleTheme,
  user,
  onLogout,
}) => {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const menuRef = React.useRef(null);

  // Close dropdown on outside click
  React.useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const userName = user?.name || user?.username || user?.email || 'User';
  const displayInitial = userName.charAt(0).toUpperCase();

  return (
    <header
      className={`
        z-40 w-full h-16 flex items-center justify-between px-4
        fixed top-0 left-0 shadow-sm transition-colors duration-300 backdrop-blur-md
        ${darkMode
          ? 'bg-gradient-to-r from-slate-900 via-slate-900 to-slate-800'
          : 'bg-white/90 border-b border-slate-200/50'
        }
      `}
    >
      {/* Left: mobile toggle + brand */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className={`p-2 rounded-lg transition-all lg:hidden ${
            darkMode
              ? 'text-white/90 hover:text-white hover:bg-white/10'
              : 'text-slate-700 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Menu size={24} />
        </button>

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
            Intelligent Software Development System
          </span>
        </div>
      </div>

      {/* Right: theme toggle + notifications + user menu */}
      <div className="flex items-center gap-2">

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className={`relative p-2.5 rounded-xl transition-all duration-300 group overflow-hidden ${
            darkMode ? 'hover:bg-white/10' : 'hover:bg-slate-100'
          }`}
          title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          <div className="relative z-10 transition-transform duration-300 group-hover:rotate-12">
            {darkMode
              ? <Sun size={20} className="text-amber-400" />
              : <Moon size={20} className="text-slate-600" />
            }
          </div>
          <div className={`absolute inset-0 scale-0 group-hover:scale-100 transition-transform duration-300 rounded-full ${
            darkMode ? 'bg-white/5' : 'bg-blue-500/10'
          }`} />
        </button>

        {/* Notifications */}
        <button className={`relative p-2.5 rounded-xl transition-all ${
          darkMode ? 'hover:bg-white/10' : 'hover:bg-slate-100'
        }`}>
          <Bell size={20} className={darkMode ? 'text-white/90' : 'text-slate-600'} />
          <span className={`absolute top-1.5 right-1.5 w-2 h-2 bg-red-400 rounded-full ring-2 ${
            darkMode ? 'ring-blue-400' : 'ring-white'
          }`} />
        </button>

        {/* User avatar + dropdown */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className={`h-9 w-9 rounded-xl flex items-center justify-center cursor-pointer transition-all ${
              darkMode
                ? 'bg-gradient-to-br from-cyan-500 to-cyan-600 hover:from-cyan-400 hover:to-cyan-500'
                : 'bg-gradient-to-br from-blue-500 to-blue-600 hover:from-blue-400 hover:to-blue-500'
            }`}
          >
            <span className="text-white font-semibold text-sm">{displayInitial}</span>
          </button>

          {showUserMenu && (
            <div className={`absolute right-0 mt-2 w-48 rounded-lg shadow-lg py-1 z-50 ${
              darkMode
                ? 'bg-slate-800 border border-slate-700'
                : 'bg-white border border-slate-200'
            }`}>
              <div className={`px-4 py-2 border-b ${
                darkMode ? 'border-slate-700' : 'border-slate-100'
              }`}>
                <p className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-slate-900'}`}>
                  {userName}
                </p>
                <p className={`text-xs ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
                  {user?.email || 'Logged in'}
                </p>
              </div>
              <button
                onClick={() => { setShowUserMenu(false); onLogout(); }}
                className={`w-full flex items-center gap-2 px-4 py-2 text-sm transition-colors ${
                  darkMode
                    ? 'text-red-400 hover:bg-slate-700'
                    : 'text-red-600 hover:bg-red-50'
                }`}
              >
                <LogOut size={16} />
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default TopNavbar;

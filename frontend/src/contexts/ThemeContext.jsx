import { createContext, useContext, useState, useEffect } from 'react';

/* ============================================================
   ThemeContext
   Used in main.jsx as <ThemeProvider> — already there, good.

   Flash/jerk fix:
   1. index.html inline script → applies .dark before React
   2. index.css blocks transitions on html:not(.theme-ready)
   3. This file adds .theme-ready 50ms after mount → unlocks
      smooth 200ms colour transitions from that point on
   ============================================================ */

const ThemeContext = createContext({
  darkMode:    false,
  toggleTheme: () => {},
  isDark:      false,
});

export const useTheme = () => useContext(ThemeContext);

export const ThemeProvider = ({ children }) => {
  const getInitialTheme = () => {
    if (typeof window === 'undefined') return false;
    const stored = localStorage.getItem('theme');
    if (stored) return stored === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  };

  const [darkMode, setDarkMode] = useState(getInitialTheme);

  // Sync .dark class + localStorage whenever darkMode changes
  useEffect(() => {
    const html = document.documentElement;
    if (darkMode) {
      html.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      html.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [darkMode]);

  // Unlock CSS transitions after first paint
  useEffect(() => {
    const id = setTimeout(() => {
      document.documentElement.classList.add('theme-ready');
    }, 50);
    return () => clearTimeout(id);
  }, []);

  const toggleTheme = () => setDarkMode(prev => !prev);

  return (
    <ThemeContext.Provider value={{ darkMode, toggleTheme, isDark: darkMode }}>
      {children}
    </ThemeContext.Provider>
  );
};

export default ThemeContext;
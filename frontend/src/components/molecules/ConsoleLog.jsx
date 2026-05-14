import React, { useRef, useEffect } from 'react';
import { Terminal, ChevronDown, AlertCircle, CheckCircle, Bug } from 'lucide-react';
import SummaryCard from './SummaryCard';

/* ============================================================
   ConsoleLog
   Collapsible console log panel from Codegen.jsx.

   Props:
     logs            array of { text, type, timestamp, summary? }
     summary         parsed summary object | null
     isCollapsed     bool
     onToggleCollapse fn
   ============================================================ */

const getLogIcon = (type) => {
  switch (type) {
    case 'error':   return <AlertCircle size={14} className="text-red-500 shrink-0" />;
    case 'warning': return <AlertCircle size={14} className="text-amber-500 shrink-0" />;
    case 'success': return <CheckCircle size={14} className="text-green-600 shrink-0" />;
    case 'debug':   return <Bug size={14} className="text-purple-500 shrink-0" />;
    default:        return <Terminal size={14} className="text-slate-400 shrink-0" />;
  }
};

const formatLogText = (text) => {
  if (!text) return '';
  if (text.length > 200 && text.includes('Summary of Codebase')) {
    const lines = text.split('\n').filter(l => l.trim().startsWith('*'));
    const keyItems = lines.slice(0, 3).map(l => l.replace(/^\*\s*\*?\*/g, '').trim()).join(' | ');
    return keyItems || text.substring(0, 100).replace(/\n/g, ' ') + '...';
  }
  let formatted = text
    .replace(/###\s*/g, '')
    .replace(/##\s*/g, '')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/```[\s\S]*?```/g, '[code]')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/^\s*[-*]\s+/gm, '• ')
    .replace(/^\s*\d+\.\s+/gm, '• ');
  if (formatted.length > 150) formatted = formatted.substring(0, 150) + '...';
  return formatted;
};

const ConsoleLog = ({ logs = [], summary = null, isCollapsed, onToggleCollapse }) => {
  const logEndRef = useRef(null);

  useEffect(() => {
    if (!isCollapsed && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isCollapsed]);

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm overflow-hidden">

      {/* Collapsible header */}
      <button
        onClick={onToggleCollapse}
        className="w-full flex items-center justify-between p-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Terminal size={16} className="text-violet-500" />
          <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">Console Logs</span>
          <span className="text-xs text-slate-500 dark:text-slate-500">({logs.length})</span>
        </div>
        <ChevronDown
          size={18}
          className={`text-slate-400 transition-transform ${isCollapsed ? '-rotate-90' : ''}`}
        />
      </button>

      {!isCollapsed && (
        <div className="border-t border-slate-200 dark:border-slate-700">
          {/* Summary card at top */}
          {summary && (
            <div className="p-3 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-br from-emerald-50 to-cyan-50 dark:from-emerald-900/10 dark:to-cyan-900/10">
              <SummaryCard summary={summary} />
            </div>
          )}

          <div className="h-48 overflow-y-auto p-3 space-y-1.5 font-mono text-xs custom-scrollbar">
            {logs.length === 0 ? (
              <div className="text-slate-400 dark:text-slate-500 italic">No logs yet...</div>
            ) : (
              logs.map((log, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2 animate-in fade-in slide-in-from-left-2 duration-150"
                >
                  <span className="text-slate-400 dark:text-slate-500 shrink-0">
                    {new Date(log.timestamp).toLocaleTimeString('en-US', { hour12: false })}
                  </span>
                  {getLogIcon(log.type)}
                  <span className={`flex-1 break-all ${
                    log.type === 'error'   ? 'text-red-600 dark:text-red-400'    :
                    log.type === 'warning' ? 'text-amber-600 dark:text-amber-400' :
                    log.type === 'success' ? 'text-green-700 dark:text-green-400' :
                    log.type === 'debug'   ? 'text-purple-600 dark:text-purple-400' :
                    'text-slate-600 dark:text-slate-300'
                  }`}>
                    {formatLogText(log.text)}
                  </span>
                </div>
              ))
            )}
            <div ref={logEndRef} />
          </div>
        </div>
      )}
    </div>
  );
};

export default ConsoleLog;

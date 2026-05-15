import React, { useRef, useEffect } from 'react';
import { Terminal, CheckCircle, AlertCircle } from 'lucide-react';

/* ============================================================
   TerminalPane
   The dark macOS-style terminal window used in Codeedit
   and reused in BugSupport.

   Props:
     logs             array of { id, content, timestamp, isError }
     connectionStatus 'idle' | 'connecting' | 'streaming' | 'done' | 'error'
     title            string — shown in the terminal header bar (default: 'isds-agent-cli — v2.4.0')
     autoScroll       bool   — auto-scroll to latest log (default: true)
   ============================================================ */

const TerminalPane = ({
  logs = [],
  connectionStatus = 'idle',
  title = 'isds-agent-cli — v2.4.0',
  autoScroll = true,
}) => {
  const logsEndRef = useRef(null);

  useEffect(() => {
    if (autoScroll) {
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  return (
    <div className="flex-1 bg-slate-900 rounded-xl overflow-hidden shadow-2xl flex flex-col border border-slate-800 dark:border-slate-700">

      {/* macOS-style header bar */}
      <div className="h-9 bg-slate-800 flex items-center px-4 gap-2 border-b border-slate-700 shrink-0">
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/80" />
          <div className="w-2.5 h-2.5 rounded-full bg-green-500/80" />
        </div>
        <div className="ml-4 text-xs font-mono text-slate-400 opacity-60 truncate">
          {title}
        </div>
      </div>

      {/* Log body */}
      <div className="flex-1 p-4 overflow-y-auto font-mono text-sm space-y-2 custom-scrollbar">

        {/* Empty state */}
        {logs.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-slate-600 opacity-50">
            <Terminal size={48} className="mb-4" />
            <p>Ready for input...</p>
          </div>
        )}

        {/* Log entries */}
        {logs.map((log) => (
          <div
            key={log.id}
            className={`flex gap-3 ${
              log.isError ? 'text-red-400' : 'text-slate-300'
            } animate-in fade-in slide-in-from-left-2 duration-300`}
          >
            <span className="text-slate-600 select-none text-xs pt-1 min-w-[60px] shrink-0">
              {log.timestamp}
            </span>
            <div className="flex-1 break-words">
              <span className="text-blue-500 mr-2 opacity-70">➜</span>
              {log.content}
            </div>
          </div>
        ))}

        {/* Done / Error footer line */}
        {connectionStatus === 'done' && (
          <div className="flex gap-3 text-green-400 py-2 border-t border-slate-700/50 mt-4">
            <span className="text-slate-600 text-xs pt-1 min-w-[60px] shrink-0">
              {new Date().toLocaleTimeString()}
            </span>
            <div className="flex-1 flex items-center gap-1.5">
              <CheckCircle size={12} />
              Process completed successfully. Connection closed.
            </div>
          </div>
        )}

        {connectionStatus === 'error' && (
          <div className="flex gap-3 text-red-400 py-2 border-t border-slate-700/50 mt-4">
            <span className="text-slate-600 text-xs pt-1 min-w-[60px] shrink-0">
              {new Date().toLocaleTimeString()}
            </span>
            <div className="flex-1 flex items-center gap-1.5">
              <AlertCircle size={12} />
              Process completed with errors. Check logs above.
            </div>
          </div>
        )}

        <div ref={logsEndRef} />
      </div>
    </div>
  );
};

export default TerminalPane;

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Send, Cpu, Download, Zap, Folder, FileCode,
  CheckCircle, Loader2, Terminal, Activity, HardDrive
} from 'lucide-react';
import { API_BASE_URL } from "../config/env";


/// // CHANGE IF BACKEND IS ON ANOTHER HOST/PORT
// const API_BASE = 'http://localhost:5000';

/* ---------- Utility ---------- */

// Strip ANSI escape codes for clean display
const stripAnsi = (text) => {
  if (!text) return '';
  return text
    .replace(/\x1b\[[0-9;]*[a-zA-Z]/g, '')
    .replace(/\x1b\][^\x07]*\x07/g, '')
    .replace(/\x1bP[^\x07]*\x07/g, '')
    .replace(/\x1b\^[^\x07]*\x07/g, '')
    .replace(/\x1b_[^\x07]*\x07/g, '')
    .replace(/\[([0-9;]+)?m/g, '')
    .replace(/\[.*?[@-~]/g, '')
    .trim();
};

const Scanline = () => (
  <div className="pointer-events-none absolute inset-0 overflow-hidden opacity-[0.03] z-0 mix-blend-overlay">
    <div className="h-full w-full bg-[linear-gradient(transparent_50%,rgba(0,0,0,1)_50%)] bg-[length:100%_4px]" />
  </div>
);

/* ---------- Sub-Components ---------- */

const SystemMonitor = () => {
  const [stats, setStats] = useState({ cpu: 12, ram: 24, net: 45 });

  useEffect(() => {
    const interval = setInterval(() => {
      setStats({
        cpu: Math.floor(Math.random() * 30) + 10,
        ram: Math.floor(Math.random() * 10) + 20,
        net: Math.floor(Math.random() * 50) + 30,
      });
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="grid grid-cols-3 gap-2 mb-4 font-mono text-[10px]">
      <div className="bg-white dark:bg-slate-900/50 border border-slate-100 dark:border-cyan-900/30 p-2 rounded-lg shadow-sm">
        <div className="flex justify-between text-slate-400 dark:text-cyan-600 mb-1">CPU</div>
        <div className="text-slate-700 dark:text-cyan-300 font-bold text-lg">{stats.cpu}%</div>
        <div className="h-1 bg-slate-100 dark:bg-slate-800 mt-1 overflow-hidden rounded-full">
          <div className="h-full bg-blue-500 dark:bg-cyan-500 transition-all duration-500 rounded-full" style={{ width: `${stats.cpu}%` }} />
        </div>
      </div>
      <div className="bg-white dark:bg-slate-900/50 border border-slate-100 dark:border-cyan-900/30 p-2 rounded-lg shadow-sm">
        <div className="flex justify-between text-slate-400 dark:text-violet-600 mb-1">RAM</div>
        <div className="text-slate-700 dark:text-violet-300 font-bold text-lg">{stats.ram}%</div>
        <div className="h-1 bg-slate-100 dark:bg-slate-800 mt-1 overflow-hidden rounded-full">
          <div className="h-full bg-violet-500 transition-all duration-500 rounded-full" style={{ width: `${stats.ram}%` }} />
        </div>
      </div>
      <div className="bg-white dark:bg-slate-900/50 border border-slate-100 dark:border-cyan-900/30 p-2 rounded-lg shadow-sm">
        <div className="flex justify-between text-slate-400 dark:text-emerald-600 mb-1">NET</div>
        <div className="text-slate-700 dark:text-emerald-300 font-bold text-lg">{stats.net}ms</div>
        <div className="h-1 bg-slate-100 dark:bg-slate-800 mt-1 overflow-hidden rounded-full">
          <div
            className="h-full bg-emerald-500 transition-all duration-500 rounded-full"
            style={{ width: `${Math.min(stats.net, 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
};

const TerminalLog = ({ logs }) => (
  // 1. Outer: flex-1 to fill space, min-h-0 to allow shrinking, flex-col to organize internals
  <div className="flex-1 min-h-0 flex flex-col font-mono text-xs h-full">

    {/* 2. Visual Box: Relative for positioning, overflow-hidden to clip content */}
    <div className="flex-1 bg-slate-900 dark:bg-slate-950 border border-slate-700 dark:border-slate-800 rounded-lg shadow-inner relative group flex flex-col overflow-hidden">

      {/* Floating Status Icon */}
      <div className="absolute top-2 right-2 z-10 p-2 opacity-50 group-hover:opacity-100 transition-opacity pointer-events-none">
        <Activity size={14} className="text-blue-500 dark:text-cyan-500 animate-pulse" />
      </div>

      {/* 3. Scroll Area: Absolute inset-0 is the most robust way to force scrolling within a flex item */}
      <div className="absolute inset-0 overflow-y-auto custom-scrollbar p-4 space-y-1 scroll-smooth">

        {logs.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 opacity-50">
            <Terminal size={32} className="mb-2" />
            <span>AWAITING INPUT STREAM</span>
          </div>
        )}

        {logs.map((log, i) => (
          <div key={i} className="flex gap-3 animate-in fade-in slide-in-from-left-2 duration-100">
            <span className="text-slate-500 shrink-0 w-12 text-right">
              {(log.timestamp % 10000).toString().padStart(4, '0')}
            </span>
            <span
              className={
                log.type === 'error'
                  ? 'text-red-400'
                  : log.type === 'success'
                    ? 'text-emerald-400'
                    : log.type === 'warning'
                      ? 'text-yellow-400'
                      : 'text-blue-300 dark:text-cyan-300'
              }
            >
              <span className="opacity-50 mr-2">{'>'}</span>
              {log.text}
            </span>
          </div>
        ))}

        {/* Scroll Anchor */}
        <div id="terminal-end" className="h-1" />
      </div>
    </div>
  </div>
);
const ChatMessage = ({ msg }) => {
  const isUser = msg.type === 'user';
  const isLogBubble = msg.mode === 'logs';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[85%] rounded-lg p-4 relative overflow-hidden ${isUser
          ? 'bg-blue-500 text-white'
          : 'bg-white dark:bg-slate-900/80 border border-slate-100 dark:border-slate-700 text-slate-600 dark:text-slate-300'
          } shadow-sm dark:shadow-lg transition-colors duration-300`}
      >
        {!isUser && (
          <div className="flex items-center gap-2 mb-2 pb-2 border-b border-slate-100 dark:border-slate-700/50">
            <div className="w-1.5 h-1.5 bg-blue-500 dark:bg-cyan-500 rounded-full shadow-[0_0_5px_rgba(59,130,246,0.5)] dark:shadow-[0_0_5px_#06b6d4]" />
            <span className="text-[10px] font-mono font-bold text-blue-500 dark:text-cyan-500 tracking-widest uppercase">
              {isLogBubble ? 'Build Telemetry' : 'Core Intelligence'}
            </span>
          </div>
        )}

        <div className="text-sm leading-relaxed font-light space-y-1">
          {isLogBubble ? (
            <>
              {(msg.lines || []).map((line, idx) => (
                <div key={idx} className="text-xs font-mono text-slate-600 dark:text-slate-200">
                  <span className="opacity-40 mr-2">{'>'}</span>
                  {line}
                </div>
              ))}
              {msg.downloadUrl && (
                <div className="pt-2 mt-2 border-t border-slate-200 dark:border-slate-700 text-xs font-mono">
                  <span className="opacity-70 mr-1">here is the project zip:</span>
                  <a
                    href={msg.downloadUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 dark:text-cyan-400 underline underline-offset-2"
                  >
                    {msg.downloadUrl}
                  </a>
                </div>
              )}
            </>
          ) : (
            msg.text
          )}
        </div>
      </div>
    </div>
  );
};

const ResizeHandle = ({ onMouseDown }) => (
  <div
    onMouseDown={onMouseDown}
    className="w-1 hover:w-2 bg-slate-200 dark:bg-slate-800 hover:bg-blue-500 dark:hover:bg-cyan-600 cursor-col-resize flex items-center justify-center transition-all duration-200 z-30 group border-l border-r border-slate-200 dark:border-slate-700"
  >
    <div className="h-8 w-0.5 bg-slate-400 dark:bg-slate-600 group-hover:bg-white rounded-full" />
  </div>
);

/* ---------- Main Component ---------- */

const Codegen = () => {
  /* State */
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'ai',
      text: 'Identity verified. iSDS Vibe Engine online. Define project parameters.',
    },
  ]);
  const [input, setInput] = useState('');
  const [status, setStatus] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([]);
  const [leftPanelWidth, setLeftPanelWidth] = useState(60);
  const containerRef = useRef(null);

  const [jobId, setJobId] = useState(null);
  const [filesDone, setFilesDone] = useState([]);
  const [logMessageId, setLogMessageId] = useState(null);

  const addLog = (text, type = 'info') => {
    setLogs(prev => [...prev, { text, type, timestamp: Date.now() }]);
  };

  useEffect(() => {
    const el = document.getElementById('terminal-end');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Auto-scroll chat to bottom when new messages arrive
  useEffect(() => {
    const chatContainer = document.getElementById('chat-messages-end');
    if (chatContainer) {
      chatContainer.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const mergeFilesDone = useCallback(incoming => {
    if (!Array.isArray(incoming) || incoming.length === 0) return;
    setFilesDone(prev => {
      const s = new Set(prev);
      incoming.forEach(f => s.add(f));
      return Array.from(s);
    });
  }, []);

  const appendLogBubbleLine = useCallback(
    line => {
      if (!line) return;
      setMessages(prev =>
        prev.map(m => {
          if (m.id === logMessageId && m.mode === 'logs') {
            const lines = m.lines || [];
            return { ...m, lines: [...lines, line] };
          }
          return m;
        })
      );
    },
    [logMessageId]
  );

  const handleSend = async e => {
    e.preventDefault();
    if (!input.trim() || status === 'working') return;

    const userText = input.trim();
    setMessages(prev => [...prev, { id: `user-${Date.now()}`, type: 'user', text: userText }]);
    setInput('');
    setStatus('working');
    setProgress(0);

    addLog(`Input received: "${userText.substring(0, 48)}..."`, 'info');
    addLog('Dispatching to iSDS codegen engine...', 'warning');

    // Generate a unique job ID based on timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const generatedJobId = `latest_${timestamp}`;
    setJobId(generatedJobId);
    setFilesDone([]);

    const newLogId = `log-${Date.now()}`;
    setLogMessageId(newLogId);
    // Don't add Build Telemetry bubble here - we'll add it when we know it's codegen

    try {
      const res = await fetch(`${API_BASE_URL}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirements: userText }),
      });

      if (!res.ok || !res.body) {
        const msg = `Backend error: HTTP ${res.status}`;
        addLog(msg, 'error');
        appendLogBubbleLine(msg);
        setStatus('idle');
        return;
      }

      setMessages(prev => [
        ...prev,
        {
          id: `ai-init-${Date.now()}`,
          type: 'ai',
          text: 'Processing your request...',
        },
      ]);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let jobIdFromBackend = null;
      let messageCounter = 0;
      let buildTelemetryAdded = false;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          let payload;
          try {
            payload = JSON.parse(trimmed);
          } catch {
            // If not JSON, treat as plain text log
            if (trimmed) {
              addLog(trimmed, 'info');
              appendLogBubbleLine(trimmed);
            }
            continue;
          }

          const { event, job_id, comprehensive_status, progress: jobProgress, files_done, response_type } = payload;

          // Store job_id from backend for download URL
          if (job_id && !jobIdFromBackend) {
            jobIdFromBackend = job_id;
            setJobId(job_id);
          }

          // Handle progress updates
          if (jobProgress !== undefined && jobProgress !== null) {
            const value =
              typeof jobProgress === "string"
                ? parseFloat(jobProgress.replace("%", ""))
                : Number(jobProgress);

            if (!Number.isNaN(value)) {
              setProgress(value);
            }
          }

          // Handle files_done updates (only for codegen)
          if (Array.isArray(files_done) && files_done.length > 0 && response_type === 'codegen') {
            mergeFilesDone(files_done);
          }

          if (event === 'started') {
            if (response_type === 'chat') {
              addLog('Orchestrator is analyzing...', 'info');
            } else {
              addLog('Job started on backend node.', 'info');
              appendLogBubbleLine('Job started on backend node.');
            }
            continue;
          }

          if (event === 'update' && comprehensive_status) {
            const cleanStatus = stripAnsi(comprehensive_status);

            if (response_type === 'chat') {
              // For chat: add as regular AI message in Core Intelligence
              // Use unique ID combining timestamp + job_id + counter
              messageCounter++;
              const uniqueId = `${Date.now()}-${messageCounter}-${job_id?.slice(0, 8) || 'noid'}`;
              setMessages(prev => [
                ...prev,
                {
                  id: uniqueId,
                  type: 'ai',
                  text: cleanStatus
                }
              ]);
              addLog(cleanStatus, 'info');
            } else {
              // For codegen: show in build telemetry
              // Add Build Telemetry bubble if not added yet
              if (!buildTelemetryAdded) {
                buildTelemetryAdded = true;
                const codegenLogId = `codegen-${Date.now()}`;
                setMessages(prev => [
                  ...prev,
                  {
                    id: codegenLogId,
                    type: 'ai',
                    mode: 'logs',
                    lines: [],
                    downloadUrl: null,
                  },
                ]);
                // Set the logMessageId so appendLogBubbleLine works
                setLogMessageId(codegenLogId);
              }
              addLog(cleanStatus, 'info');
              appendLogBubbleLine(cleanStatus);
            }
          }

          if (event === 'error' && comprehensive_status) {
            const cleanStatus = stripAnsi(comprehensive_status);
            addLog(cleanStatus, 'error');
            if (response_type !== 'chat') {
              appendLogBubbleLine(cleanStatus);
            }
          }

          if (event === 'completed') {
            setProgress(100);

            if (response_type === 'chat') {
              // Chat responses already added via 'update' events
              const doneMsg = 'Response complete';
              addLog(doneMsg, 'success');
              setStatus('idle');
            } else {
              // For codegen: show build telemetry with download

              if (comprehensive_status) {
                const cleanStatus = stripAnsi(comprehensive_status);
                addLog(cleanStatus, 'info');
                appendLogBubbleLine(cleanStatus);
              }

              // Handle final files_done if any
              if (Array.isArray(files_done) && files_done.length > 0) {
                mergeFilesDone(files_done);
              }

              const doneMsg = 'Codebase generation complete. Artifact bundle ready.';
              addLog(doneMsg, 'success');
              appendLogBubbleLine(doneMsg);

              // Create download URL using the job_id from backend
              const finalJobId = job_id || jobIdFromBackend || generatedJobId;
              const downloadUrl = `${API_BASE_URL}/download/${finalJobId}`;

              // Update message with download URL
              setMessages(prev =>
                prev.map(m => {
                  if (m.id === newLogId && m.mode === 'logs') {
                    return { ...m, downloadUrl };
                  }
                  return m;
                })
              );
              setStatus('idle');
            }
          }
        }
      }

      if (status === 'working') {
        setStatus('idle');
      }
    } catch (err) {
      const msg = `Network or streaming error: ${String(err)}`;
      addLog(msg, 'error');
      appendLogBubbleLine(msg);
      setStatus('idle');
    }
  };

  const handleMouseDown = useCallback(e => {
    e.preventDefault();
    const onMouseMove = moveEvent => {
      if (containerRef.current) {
        const containerWidth = containerRef.current.offsetWidth;
        const newLeftWidth = ((moveEvent.clientX - 256) / containerWidth) * 100; // Offset for sidebar width
        if (newLeftWidth > 20 && newLeftWidth < 80) {
          setLeftPanelWidth(newLeftWidth);
        }
      }
    };
    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  }, []);

  return (
    <>
      {/* Header */}
      <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between px-8 shadow-sm transition-colors duration-300">
        <h1 className="text-lg font-semibold text-slate-700 dark:text-slate-100 flex items-center gap-2">
          <FileCode className="text-blue-500" size={20} />
          AI Code generation Studio
        </h1>
        <div className="flex items-center gap-4">
          <span className="px-3 py-1 rounded-full text-xs font-medium border bg-blue-50 text-blue-600 border-blue-100">
            AGENT READY
          </span>
        </div>
      </header>
      <div
        className="
    flex
    h-[calc(100vh-4rem)]
    w-full
    overflow-hidden
    bg-slate-100/50
    dark:bg-slate-950
    border-b
    border-slate-100
    dark:border-slate-800
    relative
  "
      >
        <Scanline />
        <main
          className="
    flex
    w-full
    h-full
    min-h-0
    overflow-hidden
    relative
  "
          ref={containerRef}
        >



          {/* LEFT PANEL: Chat + Input */}
          <section
            style={{ width: `${leftPanelWidth}%` }}
            className="
    flex flex-col
    h-full
    min-h-0
    overflow-hidden
    min-w-[300px]
    relative
    bg-slate-100/30
    dark:bg-transparent
    transition-colors
  "
          >
            <div
              className="
    flex-1
    min-h-0
    overflow-y-auto
    overflow-x-hidden
    custom-scrollbar
    p-4
    md:p-6
    pb-4
  "
            >
              {messages.map(msg => (
                <ChatMessage key={msg.id} msg={msg} />
              ))}
              <div id="chat-messages-end" />
            </div>

            <div className="p-4 bg-white dark:bg-slate-950 border-t border-slate-100 dark:border-cyan-900/30 flex-shrink-0 z-30">
              <form onSubmit={handleSend} className="relative">
                <input
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  placeholder="Enter requirements..."
                  className="w-full pl-4 pr-12 py-3 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 focus:border-blue-400 focus:dark:border-cyan-500/50 text-sm text-slate-700 dark:text-cyan-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:focus:ring-cyan-500/20 font-mono transition-all"
                />
                <button
                  type="submit"
                  disabled={!input.trim() || status === 'working'}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-blue-500 dark:text-cyan-500 hover:text-blue-600 dark:hover:text-cyan-300 hover:bg-blue-50 dark:hover:bg-cyan-900/30 rounded-md transition-colors disabled:opacity-30"
                >
                  <Send size={16} />
                </button>
              </form>
            </div>
          </section>

          {/* RESIZER */}
          <ResizeHandle onMouseDown={handleMouseDown} />

          {/* RIGHT PANEL: System & Logs */}
          <section
            className="
    flex-1
    flex
    flex-col
    h-full
    min-h-0
    overflow-hidden
    min-w-[300px]
    bg-slate-50
    dark:bg-slate-950
    border-l
    border-slate-100
    dark:border-slate-800
    transition-colors
  "
          >
            <div className="h-10 bg-white dark:bg-slate-900 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between px-4 shrink-0">
              <span className="text-xs font-mono font-bold text-slate-500 dark:text-slate-400 flex items-center gap-2">
                <Terminal size={14} className="text-violet-500 dark:text-violet-400" /> SYSTEM OUTPUT
              </span>
              <div className="flex gap-2">
                <div className="w-2 h-2 rounded-full bg-red-500/20 border border-red-500/50" />
                <div className="w-2 h-2 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
                <div className="w-2 h-2 rounded-full bg-green-500/20 border border-green-500/50" />
              </div>
            </div>

            <div
              className="
    flex-1
    min-h-0
    flex
    flex-col
    p-4
    gap-4
    overflow-hidden
  "
            >
              <SystemMonitor />

              {/* Progress Bar */}
              {status === 'working' && (
                <div className="bg-white dark:bg-slate-900 border border-slate-100 dark:border-cyan-900/50 p-3 rounded-lg shadow-sm animate-in fade-in slide-in-from-top-2 shrink-0">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Loader2 className="animate-spin text-blue-500 dark:text-cyan-400" size={14} />
                      <span className="text-[10px] font-mono font-bold text-slate-500 dark:text-cyan-300 uppercase tracking-wider">
                        Compiling Assets
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-slate-400 dark:text-cyan-600">
                      {Math.round(progress)}%
                    </span>
                  </div>
                  <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden relative">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 to-blue-600 dark:from-cyan-500 dark:to-cyan-400 transition-all duration-300 ease-out animate-stripes relative"
                      style={{ width: `${progress}%` }}
                    >
                      <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex-1 flex flex-col min-h-0">
                <div className="flex items-center justify-between mb-2 shrink-0">
                  <span className="text-[10px] font-mono text-slate-400 dark:text-slate-500 uppercase tracking-widest">
                    Console Log
                  </span>
                  <span className="text-[10px] font-mono text-slate-400 dark:text-slate-500">
                    {logs.length} events
                  </span>
                </div>
                <TerminalLog logs={logs} />
              </div>

              <div className="h-1/3 bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-lg p-3 overflow-hidden flex flex-col shadow-sm shrink-0">
                <div className="flex items-center justify-between mb-3 border-b border-slate-50 dark:border-slate-800 pb-2">
                  <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                    <FileCode size={14} /> Generated Project Artifacts
                  </div>
                  <span className="text-[10px] font-mono text-slate-400 dark:text-slate-500">
                    {filesDone.length} files
                  </span>
                </div>
                <div className="flex-1 overflow-y-auto custom-scrollbar space-y-1 opacity-80 hover:opacity-100 transition-opacity">
                  {filesDone.length === 0 && (
                    <div className="text-[10px] font-mono text-slate-400 dark:text-slate-600">
                      Awaiting generated artifacts...
                    </div>
                  )}
                  {filesDone.map(f => {
                    const segments = f.split('/');
                    const fileName = segments.pop();
                    const dir = segments.join('/');
                    return (
                      <div
                        key={f}
                        className="text-[12px] font-mono text-blue-600 dark:text-cyan-600 flex items-center gap-2"
                      >
                        <span className="w-1 h-1 bg-blue-400 dark:bg-cyan-800 rounded-full shrink-0" />
                        <span className="truncate">
                          {dir && (
                            <span className="text-slate-400 dark:text-slate-500 mr-1">{dir}/</span>
                          )}
                          <span>{fileName}</span>
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </section>
        </main>

        <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 0; }
        .dark .custom-scrollbar::-webkit-scrollbar-track { background: #0f172a; }
        .dark .custom-scrollbar::-webkit-scrollbar-thumb { background: #1e293b; }
        .dark .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #06b6d4; }

        @keyframes progress-stripes {
          from { background-position: 0 0; }
          to { background-position: 30px 0; }
        }
        .animate-stripes {
          background-image: linear-gradient(45deg, rgba(255, 255, 255, 0.15) 25%, transparent 25%, transparent 50%, rgba(255, 255, 255, 0.15) 50%, rgba(255, 255, 255, 0.15) 75%, transparent 75%, transparent);
          background-size: 30px 30px;
          animation: progress-stripes 1s linear infinite;
        }
      `}</style>
      </div>
    </>

  );
};

export default Codegen;
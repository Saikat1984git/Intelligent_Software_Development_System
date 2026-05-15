import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Loader2, Code2 } from 'lucide-react';
import { API_BASE_URL } from '../config/env';

// Atoms
import WorkflowProgress, {
  CODEGEN_STAGES,
  CODEGEN_FULL_STAGES,
} from '../components/atoms/WorkflowProgress';

// Molecules
import ChatMessage from '../components/molecules/ChatMessage';
import ConsoleLog from '../components/molecules/ConsoleLog';
import FileExplorer from '../components/molecules/FileExplorer';
import SuccessOutput from '../components/molecules/SuccessOutput';
import DebugConfirmBar from '../components/molecules/DebugConfirmBar';

// Hooks
import useResizablePanel from '../hooks/useResizablePanel';

// Utils
import { stripAnsi, categorizeLog, parseSummary } from '../utils/logUtils';

/* ============================================================
   Codegen — Code Generation page
   Thin orchestrator: state + API logic only.
   All UI components imported from atoms/molecules.
   ============================================================ */

const Codegen = () => {

  /* ── State ─────────────────────────────────────────────── */
  const [messages, setMessages] = useState([
    { id: 1, type: 'system', text: 'Welcome to iSDS Code Generator' },
    { id: 2, type: 'ai', text: "Hi! I'm ready to help you generate code. Describe your project requirements and I'll create a complete implementation." },
  ]);
  const [input, setInput] = useState('');
  const [status, setStatus] = useState('idle'); // idle | working | completed | error | ask_debugging | debugging
  const [progress, setProgress] = useState(0);
  const [displayProgress, setDisplayProgress] = useState(0);
  const [logs, setLogs] = useState([]);
  const [parsedSummary, setParsedSummary] = useState(null);
  const [files, setFiles] = useState([]);
  const [currentStage, setCurrentStage] = useState(null);

  // UI collapse state
  const [consoleCollapsed, setConsoleCollapsed] = useState(false);
  const [filesCollapsed, setFilesCollapsed] = useState(false);

  // Debugging state
  const [askDebugging, setAskDebugging] = useState(false);
  const [isDebugging, setIsDebugging] = useState(false);
  const [debugIteration, setDebugIteration] = useState(0);
  const [bugsFound, setBugsFound] = useState(0);
  const [bugsFixed, setBugsFixed] = useState(0);
  const [isDebugMode, setIsDebugMode] = useState(false);
  const [debugErrorCount, setDebugErrorCount] = useState(0);
  const [activeStages, setActiveStages] = useState(CODEGEN_STAGES);

  // Backend job ref
  const [jobIdFromBackend, setJobIdFromBackend] = useState(null);

  // Refs
  const messagesEndRef = useRef(null);
  const lastStageRef = useRef(null);

  // Resizable panel
  const { leftPanelWidth, handleMouseDown, containerRef } = useResizablePanel(55);

  /* ── Auto-scroll chat ──────────────────────────────────── */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /* ── Debounce progress bar ─────────────────────────────── */
  useEffect(() => {
    const timer = setTimeout(() => setDisplayProgress(progress), 100);
    return () => clearTimeout(timer);
  }, [progress]);

  /* ── Helpers ───────────────────────────────────────────── */

  // Only surface important log lines — suppress noise
  const addLog = useCallback((text, type = 'info') => {
    const summary = parseSummary(text);
    if (summary) setParsedSummary(summary);

    const lower = text.toLowerCase();
    const isImportant =
      type === 'error' || type === 'warning' || type === 'success' ||
      lower.includes('started') || lower.includes('completed') ||
      lower.includes('ready') || lower.includes('generated') ||
      lower.includes('created') || lower.includes('failed') ||
      lower.includes('error') || lower.includes('warning') ||
      lower.includes('summary of codebase') ||
      lower.includes('project summary') ||
      lower.includes('accomplishments') ||
      lower.includes('execution highlights') ||
      lower.includes('codebase generation') ||
      lower.includes('node:') ||
      summary;

    if (isImportant || type === 'error' || type === 'success') {
      setLogs(prev => [...prev, { text, type, timestamp: Date.now(), summary }]);
    }
  }, []);

  const addChatMessage = useCallback((text, type = 'ai', summary = null) => {
    const parsed = summary || parseSummary(text);
    setMessages(prev => [...prev, {
      id: `msg-${Date.now()}`,
      type,
      text: parsed ? '' : text,
      summary: parsed,
    }]);
  }, []);

  // Map progress value → workflow stage, emit chat message on stage change
  const updateStage = useCallback((progressVal) => {
    let newStage;
    if (progressVal < 12) newStage = 'analysis';
    else if (progressVal < 25) newStage = 'architecture';
    else if (progressVal < 50) newStage = 'generation';
    else if (progressVal < 70) newStage = 'files';
    else if (progressVal < 85) newStage = 'dependencies';
    else if (progressVal < 95) newStage = 'debugging';
    else if (progressVal < 100) newStage = 'packaging';
    else newStage = 'completed';

    setCurrentStage(newStage);

    if (newStage !== lastStageRef.current) {
      lastStageRef.current = newStage;
      const stageMessages = {
        analysis: 'Analyzing your requirements...',
        architecture: 'Planning project structure...',
        generation: 'Generating code...',
        files: 'Creating files...',
        dependencies: 'Setting up dependencies...',
        debugging: 'Running QA checks...',
        packaging: 'Packaging project...',
        completed: 'All done!',
      };
      if (newStage !== 'completed') {
        addChatMessage(stageMessages[newStage], 'ai');
      }
    }
  }, [addChatMessage]);

  // Map debug event/status → debug workflow stage
  const updateDebugStage = useCallback((event, statusMessage, progressVal) => {
    let newStage = 'debugging';

    if (event === 'debug_started' || event === 'debug_start') {
      newStage = 'debugging';
      setIsDebugMode(true);
      setActiveStages(CODEGEN_FULL_STAGES);
      setDebugIteration(prev => prev + 1);
    } else if (
      event === 'detect_bugs' ||
      statusMessage?.toLowerCase().includes('detecting') ||
      statusMessage?.toLowerCase().includes('analyzing')
    ) {
      newStage = 'debugging';
    } else if (
      event === 'analyze_errors' || event === 'apply_fixes' ||
      statusMessage?.toLowerCase().includes('fix') ||
      statusMessage?.toLowerCase().includes('applying')
    ) {
      newStage = 'fixing_bugs';
    } else if (
      event === 'rebuild_docker' ||
      statusMessage?.toLowerCase().includes('rebuild') ||
      statusMessage?.toLowerCase().includes('building')
    ) {
      newStage = 'fixing_bugs';
    } else if (
      event === 'validate_qa' ||
      statusMessage?.toLowerCase().includes('validating') ||
      statusMessage?.toLowerCase().includes('qa')
    ) {
      newStage = 'fixing_bugs';
    } else if (
      event === 'repackage' ||
      statusMessage?.toLowerCase().includes('repackage') ||
      statusMessage?.toLowerCase().includes('packaging')
    ) {
      newStage = 'packaging';
    } else if (
      event === 'debug_completed' || event === 'debug_complete' ||
      progressVal >= 100
    ) {
      newStage = 'completed';
      setIsDebugMode(false);
    }

    setCurrentStage(newStage);

    const stageProgress = {
      debugging: 15,
      fixing_bugs: 50,
      packaging: 80,
      completed: 100,
    };
    setProgress(stageProgress[newStage] || progressVal);
  }, []);

  /* ── Reset ─────────────────────────────────────────────── */
  const handleReset = () => {
    setMessages([
      { id: 1, type: 'system', text: 'Ready for new project' },
      { id: 2, type: 'ai', text: 'What would you like to build next?' },
    ]);
    setInput('');
    setStatus('idle');
    setProgress(0);
    setLogs([]);
    setParsedSummary(null);
    setFiles([]);
    setCurrentStage(null);
    setAskDebugging(false);
    setIsDebugging(false);
    setDebugIteration(0);
    setBugsFound(0);
    setBugsFixed(0);
    setIsDebugMode(false);
    setDebugErrorCount(0);
    setActiveStages(CODEGEN_STAGES);
    lastStageRef.current = null;
  };

  /* ── Main generation submit ────────────────────────────── */
  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || status === 'working') return;

    const trimmedInput = input.trim().toLowerCase();
    if (!trimmedInput || trimmedInput.length < 10) {
      addChatMessage(
        'Please write requirements for an application only. Describe what you want to build, including features, functionality, and any specific details.',
        'ai'
      );
      return;
    }

    const userText = input.trim();
    setInput('');
    setStatus('working');
    setProgress(0);
    setCurrentStage('analysis');

    setMessages(prev => [...prev, { id: `user-${Date.now()}`, type: 'user', text: userText }]);
    const thinkingId = `thinking-${Date.now()}`;
    setMessages(prev => [...prev, { id: thinkingId, type: 'system', text: 'Processing your request...' }]);
    addLog(`User input: "${userText.substring(0, 40)}..."`, 'info');

    try {
      const res = await fetch(`${API_BASE_URL}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirements: userText }),
      });

      if (!res.ok || !res.body) throw new Error(`Backend error: HTTP ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8', { fatal: false });
      let buffer = '';
      let currentJobId = null;
      let currentDownloadUrl = null;

      setMessages(prev => prev.filter(m => m.id !== thinkingId));

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        try {
          buffer += decoder.decode(value, { stream: true });
        } catch {
          buffer += new TextDecoder('utf-8', { fatal: false }).decode(value, { stream: true });
        }

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          let payload;
          try {
            payload = JSON.parse(trimmed);
          } catch {
            if (trimmed.length > 5) addLog(trimmed, categorizeLog(trimmed));
            continue;
          }

          const {
            event,
            job_id,
            comprehensive_status,
            progress: jobProgress,
            files_done,
            ask_debugging,
          } = payload;

          // Store job ID once
          if (job_id && !currentJobId) {
            currentJobId = job_id;
            currentDownloadUrl = `${API_BASE_URL}/download/${job_id}`;
            setJobIdFromBackend(job_id);
          }

          // Progress
          if (jobProgress !== undefined && jobProgress !== null) {
            const val = typeof jobProgress === 'string'
              ? parseFloat(jobProgress.replace('%', ''))
              : Number(jobProgress);
            if (!Number.isNaN(val)) {
              setProgress(val);
              updateStage(val);
            }
          }

          // Files
          if (Array.isArray(files_done) && files_done.length > 0) {
            setFiles(prev => Array.from(new Set([...prev, ...files_done])));
          }

          if (event === 'started') addLog('Code generation started', 'info');

          if (event === 'update' && comprehensive_status) {
            const clean = stripAnsi(comprehensive_status);
            addLog(clean, categorizeLog(clean));
          }

          if (event === 'error' && comprehensive_status) {
            addLog(stripAnsi(comprehensive_status), 'error');
          }

          if (event === 'completed') {
            setProgress(100);
            setCurrentStage('completed');

            const clean = comprehensive_status
              ? stripAnsi(comprehensive_status)
              : 'Code generation complete!';
            addLog(clean, 'success');

            const summary = parseSummary(clean);
            if (summary) {
              setParsedSummary(summary);
            } else {
              const fileCount = files_done?.length || files.length || 0;
              setParsedSummary({
                title: 'Code Generation Complete',
                sections: [{
                  title: 'Results',
                  bullets: [`Generated ${fileCount} files`],
                  stats: { 'Files Generated': fileCount.toString() },
                }],
                stats: { 'Files Generated': fileCount.toString() },
                raw: clean,
              });
            }

            if (Array.isArray(files_done) && files_done.length > 0) {
              setFiles(prev => Array.from(new Set([...prev, ...files_done])));
            }

            if (ask_debugging) {
              setStatus('ask_debugging');
              setAskDebugging(true);
              addChatMessage(
                'Your project is ready! Would you like me to run the debugging process to check for any issues?',
                'ai'
              );
            } else {
              setStatus('completed');
              addChatMessage(
                `Your project is ready! I've generated ${files.length || files_done?.length || 0} files. You can download the complete package as a ZIP file.`,
                'ai'
              );
            }
          }
        }
      }
    } catch (err) {
      addLog(`Error: ${String(err)}`, 'error');
      setStatus('error');
      addChatMessage('Sorry, an error occurred during code generation. Please check the logs or try again.', 'ai');
    } finally {
      if (status === 'working') setStatus('idle');
    }
  };

  /* ── Debugging flow ────────────────────────────────────── */
  const handleDebuggingResponse = async (wantsDebug) => {
    if (!wantsDebug) {
      setAskDebugging(false);
      setStatus('completed');
      addLog('User opted to skip debugging', 'info');
      return;
    }

    setAskDebugging(false);
    setIsDebugging(true);
    setStatus('debugging');
    setProgress(0);
    setDebugIteration(0);
    setBugsFound(0);
    setBugsFixed(0);
    setDebugErrorCount(0);
    setIsDebugMode(true);
    setActiveStages(CODEGEN_FULL_STAGES);
    setCurrentStage('debugging');
    addLog('Starting debugging process...', 'info');

    try {
      const res = await fetch(`${API_BASE_URL}/run-debug`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: jobIdFromBackend,
          requirements: messages.find(m => m.type === 'user')?.text || '',
        }),
      });

      if (!res.ok || !res.body) throw new Error(`Debugging error: HTTP ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8', { fatal: false });
      let buffer = '';

      addChatMessage('Running debugging process...', 'ai');

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        try {
          buffer += decoder.decode(value, { stream: true });
        } catch {
          buffer += new TextDecoder('utf-8', { fatal: false }).decode(value, { stream: true });
        }

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          let payload;
          try { payload = JSON.parse(trimmed); } catch { continue; }

          const {
            event,
            comprehensive_status,
            progress: debugProgress,
            files_done,
            bugs_detected,
            bugs_fixed,
            error_count,
          } = payload;

          if (bugs_detected !== undefined) setBugsFound(bugs_detected);
          if (bugs_fixed !== undefined) setBugsFixed(bugs_fixed);
          if (error_count !== undefined) setDebugErrorCount(error_count);

          // Route to debug stage
          const isDebugEvent = event && (
            event.startsWith('debug_') ||
            ['detect_bugs', 'analyze_errors', 'apply_fixes', 'rebuild_docker', 'validate_qa', 'repackage'].includes(event)
          );
          if (isDebugEvent) {
            updateDebugStage(event, comprehensive_status, debugProgress ? Number(debugProgress) : 0);
          } else if (comprehensive_status) {
            updateDebugStage(null, comprehensive_status, debugProgress ? Number(debugProgress) : 0);
          }

          if (debugProgress !== undefined && debugProgress !== null) {
            setProgress(Number(debugProgress));
          }

          if (comprehensive_status) {
            const clean = stripAnsi(comprehensive_status);
            const logType = categorizeLog(clean);
            addLog(clean, logType);
            addChatMessage(clean, 'ai');

            // Bug count heuristics from log text
            if (clean.toLowerCase().includes('error') || clean.toLowerCase().includes('failed')) {
              const matches = clean.match(/error|failed|exception/gi);
              if (matches) setBugsFound(prev => prev + matches.length);
            }
            if (clean.toLowerCase().includes('fixed') || clean.toLowerCase().includes('success')) {
              setBugsFixed(prev => prev + 1);
            }
          }

          if (Array.isArray(files_done) && files_done.length > 0) {
            setFiles(prev => Array.from(new Set([...prev, ...files_done])));
          }

          if (event === 'debug_completed') {
            setProgress(100);
            setCurrentStage('completed');
            setStatus('completed');
            setIsDebugging(false);
            setIsDebugMode(false);
            addLog('Debugging complete! All issues have been fixed.', 'success');
            addChatMessage('Debugging complete! Your project is ready with all fixes applied. You can now download the updated package.', 'ai');
          }

          if (event === 'debug_error') {
            setStatus('completed');
            setIsDebugging(false);
            setIsDebugMode(false);
            addChatMessage('Debugging completed with some issues. You can try again or download the current version.', 'ai');
          }
        }
      }
    } catch (err) {
      addLog(`Debugging error: ${String(err)}`, 'error');
      setStatus('completed');
      setIsDebugging(false);
      setIsDebugMode(false);
      addChatMessage('Debugging encountered an error. You can try again or proceed with the current version.', 'ai');
    }
  };

  /* ── Render ────────────────────────────────────────────── */
  return (
    <div className="h-[calc(100vh)] flex flex-col bg-slate-50 dark:bg-slate-950">

      {/* Page header */}
      <header className="h-14 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-5 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
            <Code2 size={18} className="text-white" />
          </div>
          <h1 className="text-lg font-semibold text-slate-700 dark:text-slate-100">
            Code Generator
          </h1>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${status === 'working' || status === 'debugging'
            ? 'bg-amber-50 text-amber-600 border-amber-200 animate-pulse'
            : status === 'completed'
              ? 'bg-emerald-50 text-emerald-600 border-emerald-200'
              : 'bg-blue-50 text-blue-600 border-blue-200'
          }`}>
          {status === 'working' ? 'Generating...' :
            status === 'debugging' ? 'Debugging...' :
              status === 'completed' ? 'Complete' : 'Ready'}
        </span>
      </header>

      {/* Resizable split layout */}
      <div className="flex-1 flex overflow-hidden" ref={containerRef}>

        {/* LEFT — Chat panel */}
        <div
          style={{ width: `${leftPanelWidth}%` }}
          className="flex flex-col border-r border-slate-200 dark:border-slate-800 min-w-[300px]"
        >
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
            {messages.map(msg => (
              <ChatMessage key={msg.id} msg={msg} />
            ))}

            {status === 'working' && (
              <div className="flex justify-start mb-3">
                <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-3 shadow-sm">
                  <div className="flex items-center gap-2">
                    <Loader2 size={16} className="animate-spin text-blue-500" />
                    <span className="text-sm text-slate-600 dark:text-slate-300">Processing...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Debug confirm / in-progress bar */}
          <DebugConfirmBar
            showConfirm={askDebugging || status === 'ask_debugging'}
            isDebugging={isDebugging}
            onConfirm={handleDebuggingResponse}
          />

          {/* Chat input */}
          <div className="p-4 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 shrink-0">
            <form onSubmit={handleSend} className="relative">
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder="Describe your project requirements..."
                disabled={status === 'working'}
                className="w-full pl-4 pr-12 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:border-blue-500 text-sm text-slate-700 dark:text-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!input.trim() || status === 'working'}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-blue-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <Send size={18} />
              </button>
            </form>
          </div>
        </div>

        {/* Resize handle */}
        <div
          onMouseDown={handleMouseDown}
          className="w-1.5 bg-slate-200 dark:bg-slate-800 hover:bg-blue-500 dark:hover:bg-cyan-500 cursor-col-resize flex items-center justify-center transition-all duration-200 z-30 group border-l border-r border-slate-200 dark:border-slate-700"
        >
          <div className="h-10 w-0.5 bg-slate-400 dark:bg-slate-600 group-hover:bg-white rounded-full" />
        </div>

        {/* RIGHT — Progress + logs + files */}
        <div className="flex-1 min-w-[300px] flex flex-col overflow-y-auto p-4 gap-4 custom-scrollbar">

          {/* WorkflowProgress — fixed height, always visible */}
          <div className="shrink-0">
            <WorkflowProgress
              currentStage={currentStage}
              progress={displayProgress}
              stages={activeStages}
              isDebugMode={isDebugMode}
              debugIteration={debugIteration}
              bugsFound={bugsFound}
              bugsFixed={bugsFixed}
            />
          </div>

          {/* ConsoleLog — grows to fill space, min-h ensures visible on small screens */}
          <ConsoleLog
            logs={logs}
            summary={parsedSummary}
            isCollapsed={consoleCollapsed}
            onToggleCollapse={() => setConsoleCollapsed(c => !c)}
            fillHeight
          />

          {/* FileExplorer — shrink-0, fixed height */}
          <div className="shrink-0">
            <FileExplorer
              files={files}
              isCollapsed={filesCollapsed}
              onToggleCollapse={() => setFilesCollapsed(c => !c)}
            />
          </div>

          {status === 'completed' && (
            <div className="shrink-0">
              <SuccessOutput
                jobId={jobIdFromBackend}
                fileCount={files.length}
                downloadUrl={jobIdFromBackend ? `${API_BASE_URL}/download/${jobIdFromBackend}` : null}
                onReset={handleReset}
              />
            </div>
          )}
        </div>
      </div>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
        .dark .custom-scrollbar::-webkit-scrollbar-track { background: #1e293b; }
        .dark .custom-scrollbar::-webkit-scrollbar-thumb { background: #475569; }
        .dark .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #64748b; }
      `}</style>
    </div>
  );
};

export default Codegen;
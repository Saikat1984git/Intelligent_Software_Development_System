import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  FolderOpen, Terminal, Upload, Play,
  FileCode, Activity, X, CheckCircle,
  AlertCircle, Image as ImageIcon,
} from 'lucide-react';
import { API_BASE_URL } from '../config/env';

// Atoms
import WorkflowProgress, { CODEEDIT_STAGES } from '../components/atoms/WorkflowProgress';
import TerminalPane from '../components/atoms/TerminalPane';

// Hooks
import useResizablePanel from '../hooks/useResizablePanel';

/* ============================================================
   Codeedit — Code Modification page
   Thin orchestrator: state + API logic only.
   WorkflowProgress and TerminalPane imported from atoms.
   useResizablePanel replaces inline drag logic.
   Dead NavItem component removed.
   All existing logic and UI preserved exactly.
   ============================================================ */

const Codeedit = () => {

  /* ── State ─────────────────────────────────────────────── */
  const [projectPath,      setProjectPath]      = useState('');
  const [prompt,           setPrompt]           = useState('');
  const [images,           setImages]           = useState([]);
  const [logs,             setLogs]             = useState([]);
  const [isProcessing,     setIsProcessing]     = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('idle'); // idle | connecting | streaming | done | error

  // Workflow state
  const [currentStage, setCurrentStage] = useState(null);
  const [progress,     setProgress]     = useState(0);

  // Drag state for image drop zone
  const [isDragging, setIsDragging] = useState(false);

  // Resizable panel — replaces inline handleMouseDown + leftPanelWidth
  const { leftPanelWidth, handleMouseDown, containerRef } = useResizablePanel(40);

  /* ── Update stage from log text ────────────────────────── */
  const updateStageFromLogs = (logContent) => {
    const lower = logContent.toLowerCase();

    if (lower.includes('[step 1]') || lower.includes('analyzing project') || lower.includes('analyzing')) {
      setCurrentStage('analysis');
      setProgress(15);
    } else if (lower.includes('[step 2]') || lower.includes('selecting files') || lower.includes('selecting')) {
      setCurrentStage('selecting');
      setProgress(35);
    } else if (lower.includes('[step 3]') || lower.includes('rewriting') || lower.includes('generating')) {
      setCurrentStage('rewriting');
      setProgress(60);
    } else if (lower.includes('[step 4]') || lower.includes('applying') || lower.includes('applying changes')) {
      setCurrentStage('applying');
      setProgress(85);
    } else if (lower.includes('complete') || lower.includes('success') || lower.includes('done')) {
      setCurrentStage('completed');
      setProgress(100);
    }
  };

  /* ── Image drag & drop handlers ────────────────────────── */
  const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = (e) => { e.preventDefault(); setIsDragging(false); };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
    if (dropped.length > 0) setImages(prev => [...prev, ...dropped]);
  };

  const handleFileSelect = (e) => {
    if (e.target.files) {
      const selected = Array.from(e.target.files).filter(f => f.type.startsWith('image/'));
      setImages(prev => [...prev, ...selected]);
    }
  };

  const removeImage = (indexToRemove) => {
    setImages(prev => prev.filter((_, i) => i !== indexToRemove));
  };

  /* ── SSE streaming submit ──────────────────────────────── */
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!projectPath || !prompt) return;

    setIsProcessing(true);
    setConnectionStatus('connecting');
    setLogs([]);
    setCurrentStage('analysis');
    setProgress(10);

    const formData = new FormData();
    formData.append('project_path', projectPath);
    formData.append('prompt', prompt);
    images.forEach(image => formData.append('images', image));

    try {
      const response = await fetch(`${API_BASE_URL}/rewrite`, {
        method: 'POST',
        body:   formData,
      });

      if (!response.ok) throw new Error(`Server Error: ${response.statusText}`);

      setConnectionStatus('streaming');

      const reader  = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer   = '';
      let hasError = false;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // SSE: split on double newline
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';

        for (const part of parts) {
          if (part.trim().startsWith('data:')) {
            const message = part.replace(/^data:\s*/, '').trim();

            if (message === '[DONE]') {
              setCurrentStage('completed');
              setProgress(100);
              setConnectionStatus(hasError ? 'error' : 'done');
              setIsProcessing(false);
              return;
            }

            const lowerMsg = message.toLowerCase();
            if (
              lowerMsg.includes('error:') ||
              lowerMsg.includes('failed') ||
              lowerMsg.includes('exception') ||
              lowerMsg.includes('traceback')
            ) {
              hasError = true;
            }

            updateStageFromLogs(message);

            setLogs(prev => [...prev, {
              id:        Date.now() + Math.random(),
              content:   message,
              timestamp: new Date().toLocaleTimeString(),
              isError:   lowerMsg.includes('error') || lowerMsg.includes('failed') || lowerMsg.includes('exception'),
            }]);
          }
        }
      }
    } catch (error) {
      setCurrentStage('completed');
      setProgress(100);
      setLogs(prev => [...prev, {
        id:        Date.now(),
        content:   `Error: ${error.message}`,
        isError:   true,
        timestamp: new Date().toLocaleTimeString(),
      }]);
      setConnectionStatus('error');
      setIsProcessing(false);
    }
  };

  /* ── Render ────────────────────────────────────────────── */
  return (
    <div className="flex h-[calc(100vh)] bg-slate-50 dark:bg-slate-950 font-sans text-slate-800 dark:text-slate-200 overflow-hidden transition-colors duration-300">
      <main className="flex-1 flex flex-col min-w-0 bg-slate-50 dark:bg-slate-950 transition-colors duration-300">

        {/* Page header */}
        <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between px-8 shadow-sm transition-colors duration-300">
          <h1 className="text-lg font-semibold text-slate-700 dark:text-slate-100 flex items-center gap-2">
            <FileCode className="text-blue-500" size={20} />
            AI Code modification Studio
          </h1>
          <span className={`px-3 py-1 rounded-full text-xs font-medium border ${
            isProcessing
              ? 'bg-blue-50 text-blue-600 border-blue-100 animate-pulse'
              : connectionStatus === 'error'
                ? 'bg-red-50 text-red-600 border-red-100'
                : connectionStatus === 'done'
                  ? 'bg-green-50 text-green-600 border-green-100'
                  : 'bg-blue-50 text-blue-600 border-blue-100'
          }`}>
            {isProcessing
              ? 'PROCESSING AGENT ACTIVE'
              : connectionStatus === 'error'
                ? 'ERROR OCCURRED'
                : connectionStatus === 'done'
                  ? 'COMPLETED'
                  : 'AGENT READY'
            }
          </span>
        </header>

        {/* Resizable split layout */}
        <div className="flex-1 flex overflow-hidden p-4" ref={containerRef}>

          {/* LEFT — Input form */}
          <div
            style={{ width: `${leftPanelWidth}%` }}
            className="flex flex-col h-full overflow-y-auto pr-4 custom-scrollbar min-w-[300px]"
          >
            <form onSubmit={handleSubmit} className="space-y-6">

              {/* Project path */}
              <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm transition-all hover:shadow-md">
                <label className="block text-sm font-semibold text-slate-600 dark:text-slate-300 mb-2 flex items-center gap-2">
                  <FolderOpen size={16} className="text-blue-500" />
                  Project Root Path
                </label>
                <input
                  type="text"
                  value={projectPath}
                  onChange={e => setProjectPath(e.target.value)}
                  placeholder="e.g. D:/Development/MyProject"
                  className="w-full px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 focus:ring-2 focus:ring-blue-500 focus:border-blue-400 outline-none text-slate-700 dark:text-slate-200 text-sm placeholder-slate-400 dark:placeholder-slate-600 transition-all"
                  required
                  disabled={isProcessing}
                />
                <p className="mt-2 text-xs text-slate-400">
                  Absolute path to the directory containing package.json or requirements.txt.
                </p>
              </div>

              {/* Prompt / instructions */}
              <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm transition-all hover:shadow-md">
                <label className="block text-sm font-semibold text-slate-600 dark:text-slate-300 mb-2 flex items-center gap-2">
                  <Terminal size={16} className="text-blue-500" />
                  Rewrite Instructions
                </label>
                <textarea
                  value={prompt}
                  onChange={e => setPrompt(e.target.value)}
                  placeholder="Describe the desired changes (e.g., 'Refactor the authentication flow to use JWT...')"
                  rows={5}
                  className="w-full px-4 py-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 focus:ring-2 focus:ring-blue-500 focus:border-blue-400 outline-none text-slate-700 dark:text-slate-200 text-sm placeholder-slate-400 dark:placeholder-slate-600 resize-none transition-all"
                  required
                  disabled={isProcessing}
                />
              </div>

              {/* Image upload */}
              <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm transition-all hover:shadow-md">
                <label className="block text-sm font-semibold text-slate-600 dark:text-slate-300 mb-3 flex items-center gap-2">
                  <ImageIcon size={16} className="text-blue-500" />
                  Visual References
                </label>

                {/* Drop zone */}
                <div
                  className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-all duration-200 ${
                    isDragging
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/10'
                      : 'border-slate-300 dark:border-slate-700 hover:border-blue-400 dark:hover:border-blue-500 hover:bg-slate-50 dark:hover:bg-slate-800'
                  } ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => !isProcessing && document.getElementById('file-upload').click()}
                >
                  <input
                    id="file-upload"
                    type="file"
                    multiple
                    accept="image/*"
                    className="hidden"
                    onChange={handleFileSelect}
                    disabled={isProcessing}
                  />
                  <div className="flex flex-col items-center justify-center gap-2">
                    <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-full text-slate-500 dark:text-slate-400">
                      <Upload size={24} />
                    </div>
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                      Click to upload or drag and drop
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-500">
                      PNG, JPG, GIF up to 10MB
                    </p>
                  </div>
                </div>

                {/* Image previews */}
                {images.length > 0 && (
                  <div className="mt-4 grid grid-cols-4 gap-2">
                    {images.map((file, idx) => (
                      <div key={idx} className="relative group aspect-square rounded-lg overflow-hidden border border-slate-200 dark:border-slate-700">
                        <img
                          src={URL.createObjectURL(file)}
                          alt="preview"
                          className="w-full h-full object-cover"
                        />
                        <button
                          type="button"
                          onClick={() => removeImage(idx)}
                          disabled={isProcessing}
                          className="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity disabled:hidden hover:bg-red-600"
                        >
                          <X size={12} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={isProcessing}
                className={`w-full py-3.5 px-6 rounded-xl flex items-center justify-center gap-2 font-semibold text-white shadow-lg shadow-blue-500/30 transition-all ${
                  isProcessing
                    ? 'bg-slate-400 dark:bg-slate-600 cursor-not-allowed'
                    : 'bg-gradient-to-r from-blue-600 to-blue-500 hover:translate-y-[-1px] hover:shadow-blue-500/40 active:translate-y-[1px]'
                }`}
              >
                {isProcessing ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Processing Request...
                  </>
                ) : (
                  <>
                    <Play size={18} fill="currentColor" />
                    Initiate code rewriting
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Resize handle */}
          <div
            onMouseDown={handleMouseDown}
            className="w-1.5 hover:w-1.5 bg-slate-200 dark:bg-slate-800 hover:bg-blue-500 dark:hover:bg-cyan-500 cursor-col-resize flex items-center justify-center transition-all duration-200 z-30 group border-l border-r border-slate-200 dark:border-slate-700"
          >
            <div className="h-10 w-0.5 bg-slate-400 dark:bg-slate-600 group-hover:bg-white rounded-full" />
          </div>

          {/* RIGHT — Workflow + terminal */}
          <div className="flex-1 min-w-[300px] flex flex-col h-full pl-4">

            {/* Workflow progress */}
            <div className="mb-4">
              <WorkflowProgress
                currentStage={currentStage}
                progress={progress}
                stages={CODEEDIT_STAGES}
              />
            </div>

            {/* Live log label */}
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-slate-600 dark:text-slate-300 flex items-center gap-2">
                <Activity size={16} className="text-blue-500" />
                Live Execution Logs
              </h3>
              {connectionStatus === 'streaming' && (
                <span className="text-xs text-blue-600 dark:text-blue-400 animate-pulse font-mono">
                  Receiving Data Stream...
                </span>
              )}
              {connectionStatus === 'done' && (
                <span className="text-xs text-green-600 dark:text-green-400 font-mono flex items-center gap-1">
                  <CheckCircle size={12} /> Complete
                </span>
              )}
              {connectionStatus === 'error' && (
                <span className="text-xs text-red-600 dark:text-red-400 font-mono flex items-center gap-1">
                  <AlertCircle size={12} /> Failed
                </span>
              )}
            </div>

            {/* Terminal pane — atom */}
            <TerminalPane
              logs={logs}
              connectionStatus={connectionStatus}
              title="isds-agent-cli — v2.4.0"
            />
          </div>
        </div>
      </main>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 20px; }
        .dark .custom-scrollbar::-webkit-scrollbar-thumb { background-color: #334155; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background-color: #94a3b8; }
        .dark .custom-scrollbar::-webkit-scrollbar-thumb:hover { background-color: #475569; }
      `}</style>
    </div>
  );
};

export default Codeedit;

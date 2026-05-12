import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  FolderOpen,
  Terminal,
  Upload,
  Play,
  FileCode,
  Layers,
  Activity,
  X,
  CheckCircle,
  AlertCircle,
  Image as ImageIcon,
  Cpu,
  Brain,
  FileEdit,
  Wand2,
  Save,
  CheckCircle2
} from 'lucide-react';
import { API_BASE_URL } from "../config/env";


/* ========== WORKFLOW STAGES FOR CODE EDITING ========== */

const CODEEDIT_STAGES = [
  { id: 'analysis', label: 'Project Analysis', icon: Brain },
  { id: 'selecting', label: 'Selecting Files', icon: FileEdit },
  { id: 'rewriting', label: 'Rewriting Code', icon: Wand2 },
  { id: 'applying', label: 'Applying Changes', icon: Save },
  { id: 'completed', label: 'Completed', icon: CheckCircle2 },
];


/* ========== WORKFLOW PROGRESS COMPONENT ========== */

const WorkflowProgress = ({ currentStage, progress, stages = CODEEDIT_STAGES }) => {
  const currentIndex = stages.findIndex(s => s.id === currentStage) || 0;

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">Workflow Progress</span>
        </div>
        <span className="text-xs font-medium text-blue-600 dark:text-blue-400">{Math.round(progress)}%</span>
      </div>

      <div className="relative h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden mb-4">
        <div
          className="absolute inset-y-0 left-0 rounded-full transition-all duration-500 bg-gradient-to-r from-blue-500 to-cyan-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="flex flex-wrap gap-1">
        {stages.map((stage, idx) => {
          const Icon = stage.icon;
          const isActive = idx === currentIndex;
          const isCompleted = idx < currentIndex;

          return (
            <div
              key={stage.id}
              className={`
                flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium
                transition-all duration-300
                ${isCompleted
                  ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                  : isActive
                    ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-500'
                }
              `}
            >
              <Icon size={12} className={isActive ? 'animate-pulse' : ''} />
              <span className="hidden sm:inline">{stage.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};


const Codeedit = () => {
  // --- State Management ---
  const [projectPath, setProjectPath] = useState('');
  const [prompt, setPrompt] = useState('');
  const [images, setImages] = useState([]);
  const [logs, setLogs] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('idle'); // idle, connecting, streaming, done, error

  // Workflow state
  const [currentStage, setCurrentStage] = useState(null);
  const [progress, setProgress] = useState(0);

  // Refs for scrolling and drag handling
  const logsEndRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  // Resizable panel state
  const [leftPanelWidth, setLeftPanelWidth] = useState(40);
  const containerRef = useRef(null);

  // --- Auto-scroll logs ---
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // --- Update workflow stage based on logs ---
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

  // --- File Handling (Drag & Drop + Select) ---
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files).filter(file =>
      file.type.startsWith('image/')
    );

    if (droppedFiles.length > 0) {
      setImages(prev => [...prev, ...droppedFiles]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files).filter(file =>
        file.type.startsWith('image/')
      );
      setImages(prev => [...prev, ...selectedFiles]);
    }
  };

  const removeImage = (indexToRemove) => {
    setImages(prev => prev.filter((_, index) => index !== indexToRemove));
  };

  // --- Resizable Panel Handler ---
  const handleMouseDown = useCallback((e) => {
    e.preventDefault();
    const onMouseMove = (moveEvent) => {
      if (containerRef.current) {
        const containerWidth = containerRef.current.offsetWidth;
        const newLeftWidth = ((moveEvent.clientX) / containerWidth) * 100;
        if (newLeftWidth > 25 && newLeftWidth < 75) {
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

  // --- API Streaming Logic ---
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
    images.forEach((image) => {
      formData.append('images', image);
    });

    try {
      const response = await fetch(`${API_BASE_URL}/rewrite`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error(`Server Error: ${response.statusText}`);

      setConnectionStatus('streaming');

      // Initialize Stream Reader
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let hasError = false;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Split by double newline (SSE standard delimiter)
        const parts = buffer.split('\n\n');

        // Keep the last part in buffer if it's incomplete
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

            // Check for error indicators in the message
            const lowerMsg = message.toLowerCase();
            if (lowerMsg.includes('error:') ||
                lowerMsg.includes('failed') ||
                lowerMsg.includes('exception') ||
                lowerMsg.includes('traceback')) {
              hasError = true;
            }

            // Update workflow progress based on log content
            updateStageFromLogs(message);

            // Add to logs
            setLogs(prev => [...prev, {
              id: Date.now() + Math.random(),
              content: message,
              timestamp: new Date().toLocaleTimeString(),
              isError: lowerMsg.includes('error') || lowerMsg.includes('failed') || lowerMsg.includes('exception')
            }]);
          }
        }
      }
    } catch (error) {
      setCurrentStage('completed');
      setProgress(100);
      setLogs(prev => [...prev, {
        id: Date.now(),
        content: `Error: ${error.message}`,
        isError: true,
        timestamp: new Date().toLocaleTimeString()
      }]);
      setConnectionStatus('error');
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh)] bg-slate-50 dark:bg-slate-950 font-sans text-slate-800 dark:text-slate-200 overflow-hidden transition-colors duration-300">

      {/* --- Main Content --- */}
      <main className="flex-1 flex flex-col min-w-0 bg-slate-50 dark:bg-slate-950 transition-colors duration-300">

        {/* Header */}
        <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between px-8 shadow-sm transition-colors duration-300">
          <h1 className="text-lg font-semibold text-slate-700 dark:text-slate-100 flex items-center gap-2">
            <FileCode className="text-blue-500" size={20} />
            AI Code modification Studio
          </h1>
          <div className="flex items-center gap-4">
            <span className={`px-3 py-1 rounded-full text-xs font-medium border ${
              isProcessing
                ? 'bg-blue-50 text-blue-600 border-blue-100 animate-pulse'
                : connectionStatus === 'error'
                  ? 'bg-red-50 text-red-600 border-red-100'
                  : connectionStatus === 'done'
                    ? 'bg-green-50 text-green-600 border-green-100'
                    : 'bg-blue-50 text-blue-600 border-blue-100'
            }`}>
              {isProcessing ? 'PROCESSING AGENT ACTIVE' : connectionStatus === 'error' ? 'ERROR OCCURRED' : connectionStatus === 'done' ? 'COMPLETED' : 'AGENT READY'}
            </span>
          </div>
        </header>

        {/* Content Grid - Resizable Layout */}
        <div className="flex-1 flex overflow-hidden p-4" ref={containerRef}>

            {/* LEFT COLUMN: Input Form */}
            <div
              style={{ width: `${leftPanelWidth}%` }}
              className="flex flex-col h-full overflow-y-auto pr-4 custom-scrollbar min-w-[300px]"
            >
              <form onSubmit={handleSubmit} className="space-y-6">

                {/* Project Path Input */}
                <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm transition-all hover:shadow-md">
                  <label className="block text-sm font-semibold text-slate-600 dark:text-slate-300 mb-2 flex items-center gap-2">
                    <FolderOpen size={16} className="text-blue-500" />
                    Project Root Path
                  </label>
                  <input
                    type="text"
                    value={projectPath}
                    onChange={(e) => setProjectPath(e.target.value)}
                    placeholder="e.g. D:/Development/MyProject"
                    className="w-full px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 focus:ring-2 focus:ring-blue-500 focus:border-blue-400 outline-none text-slate-700 dark:text-slate-200 text-sm placeholder-slate-400 dark:placeholder-slate-600 transition-all"
                    required
                    disabled={isProcessing}
                  />
                  <p className="mt-2 text-xs text-slate-400">
                    Absolute path to the directory containing package.json or requirements.txt.
                  </p>
                </div>

                {/* Prompt Input */}
                <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm transition-all hover:shadow-md">
                  <label className="block text-sm font-semibold text-slate-600 dark:text-slate-300 mb-2 flex items-center gap-2">
                    <Terminal size={16} className="text-blue-500" />
                    Rewrite Instructions
                  </label>
                  <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="Describe the desired changes (e.g., 'Refactor the authentication flow to use JWT...')"
                    rows={5}
                    className="w-full px-4 py-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 focus:ring-2 focus:ring-blue-500 focus:border-blue-400 outline-none text-slate-700 dark:text-slate-200 text-sm placeholder-slate-400 dark:placeholder-slate-600 resize-none transition-all"
                    required
                    disabled={isProcessing}
                  />
                </div>

                {/* Image Upload */}
                <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm transition-all hover:shadow-md">
                  <label className="block text-sm font-semibold text-slate-600 dark:text-slate-300 mb-3 flex items-center gap-2">
                    <ImageIcon size={16} className="text-blue-500" />
                    Visual References
                  </label>

                  {/* Drop Zone */}
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

                  {/* Image Previews */}
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

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={isProcessing}
                  className={`w-full py-3.5 px-6 rounded-xl flex items-center justify-center gap-2 font-semibold text-white shadow-lg shadow-blue-500/30 transition-all ${
                    isProcessing
                      ? 'bg-slate-400 dark:bg-slate-600 cursor-not-allowed transform-none'
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

            {/* RESIZE HANDLE */}
            <div
              onMouseDown={handleMouseDown}
              className="w-1.5 hover:w-1.5 bg-slate-200 dark:bg-slate-800 hover:bg-blue-500 dark:hover:bg-cyan-500 cursor-col-resize flex items-center justify-center transition-all duration-200 z-30 group border-l border-r border-slate-200 dark:border-slate-700"
            >
              <div className="h-10 w-0.5 bg-slate-400 dark:bg-slate-600 group-hover:bg-white rounded-full" />
            </div>

            {/* RIGHT COLUMN: Terminal / Output */}
            <div className="flex-1 min-w-[300px] flex flex-col h-full pl-4">

              {/* Workflow Progress - Show when processing */}
              <div className="mb-4">
                <WorkflowProgress
                  currentStage={currentStage}
                  progress={progress}
                  stages={CODEEDIT_STAGES}
                />
              </div>

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

              <div className="flex-1 bg-slate-900 rounded-xl overflow-hidden shadow-2xl flex flex-col border border-slate-800 dark:border-slate-700">
                {/* Terminal Header */}
                <div className="h-9 bg-slate-800 flex items-center px-4 gap-2 border-b border-slate-700">
                  <div className="flex gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-red-500/80"></div>
                    <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/80"></div>
                    <div className="w-2.5 h-2.5 rounded-full bg-green-500/80"></div>
                  </div>
                  <div className="ml-4 text-xs font-mono text-slate-400 opacity-60">isds-agent-cli — v2.4.0</div>
                </div>

                {/* Terminal Body */}
                <div className="flex-1 p-4 overflow-y-auto font-mono text-sm space-y-2 custom-scrollbar">
                  {logs.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-slate-600 opacity-50">
                      <Terminal size={48} className="mb-4" />
                      <p>Ready for input...</p>
                    </div>
                  )}

                  {logs.map((log) => (
                    <div key={log.id} className={`flex gap-3 ${log.isError ? 'text-red-400' : 'text-slate-300'} animate-in fade-in slide-in-from-left-2 duration-300`}>
                      <span className="text-slate-600 select-none text-xs pt-1 min-w-[60px]">{log.timestamp}</span>
                      <div className="flex-1 break-words">
                        <span className="text-blue-500 mr-2 opacity-70">➜</span>
                        {log.content}
                      </div>
                    </div>
                  ))}

                  {connectionStatus === 'done' && (
                     <div className="flex gap-3 text-green-400 py-2 border-t border-slate-700/50 mt-4">
                       <span className="text-slate-600 text-xs pt-1 min-w-[60px]">{new Date().toLocaleTimeString()}</span>
                       <div className="flex-1">
                         <span className="text-green-500 mr-2">✓</span>
                         Process completed successfully. Connection closed.
                       </div>
                     </div>
                  )}

                  {connectionStatus === 'error' && (
                     <div className="flex gap-3 text-red-400 py-2 border-t border-slate-700/50 mt-4">
                       <span className="text-slate-600 text-xs pt-1 min-w-[60px]">{new Date().toLocaleTimeString()}</span>
                       <div className="flex-1">
                         <span className="text-red-500 mr-2">✗</span>
                         Process completed with errors. Check logs above.
                       </div>
                     </div>
                  )}

                  <div ref={logsEndRef} />
                </div>
              </div>
            </div>
        </div>
      </main>

      <style>{`
        /* Custom Scrollbar for dark mode compatibility */
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background-color: #cbd5e1;
          border-radius: 20px;
        }
        .dark .custom-scrollbar::-webkit-scrollbar-thumb {
          background-color: #334155;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background-color: #94a3b8;
        }
        .dark .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background-color: #475569;
        }
      `}</style>
    </div>
  );
};

// Sub-component for Navigation Items
const NavItem = ({ icon, label, active = false }) => (
  <button className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
    active
      ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
  }`}>
    <span className={active ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400 dark:text-slate-500'}>{icon}</span>
    {label}
  </button>
);

export default Codeedit;
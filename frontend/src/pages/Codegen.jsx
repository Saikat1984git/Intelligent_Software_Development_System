import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  Send,
  Download,
  Folder,
  FileCode,
  File,
  CheckCircle,
  Loader2,
  Terminal,
  Activity,
  ChevronDown,
  ChevronRight,
  X,
  Play,
  Sparkles,
  Zap,
  Package,
  Bug,
  Clock,
  AlertCircle,
  Info,
  Cpu,
  Brain,
  Wrench,
  Box,
  Archive,
  Copy,
  ExternalLink,
  RefreshCw,
  Code,
  Layout,
  Code2
} from 'lucide-react';
import { API_BASE_URL } from "../config/env";

/* ========== UTILITIES ========== */

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

// Categorize logs for display
const categorizeLog = (text) => {
  const lower = text.toLowerCase();
  // Check for success/complete first before error
  if (lower.includes('success') || lower.includes('complete') || lower.includes('done') || lower.includes('ready') || lower.includes('generated')) return 'success';
  if (lower.includes('warning') || lower.includes('warn')) return 'warning';
  if (lower.includes('error') || lower.includes('failed') || lower.includes('exception')) return 'error';
  if (lower.includes('debugging') || lower.includes('fixing') || lower.includes('retry')) return 'debug';
  return 'info';
};

// Format terminal output for better UI display
const formatLogText = (text) => {
  if (!text) return '';

  // Check if this is a large summary (show condensed)
  if (text.length > 200 && text.includes('Summary of Codebase')) {
    // Extract key info for display - show the actual content instead of "Generated ? files"
    const lines = text.split('\n').filter(l => l.trim().startsWith('*'));
    const keyItems = lines.slice(0, 3).map(l => l.replace(/^\*\s*\*?\*/g, '').trim()).join(' | ');
    if (keyItems) {
      return keyItems;
    }
    // If no bullet points found, show a portion of the text
    return text.substring(0, 100).replace(/\n/g, ' ') + '...';
  }

  // Remove markdown formatting for cleaner display
  let formatted = text
    .replace(/###\s*/g, '')
    .replace(/##\s*/g, '')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/```[\s\S]*?```/g, '[code]')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/^\s*[-*]\s+/gm, '• ')
    .replace(/^\s*\d+\.\s+/gm, '• ');

  // Truncate very long lines
  if (formatted.length > 150) {
    formatted = formatted.substring(0, 150) + '...';
  }

  return formatted;
};

// Parse terminal-friendly summary into structured format
const parseSummary = (text) => {
  if (!text || typeof text !== 'string') return null;

  // Check if this is a codebase generation summary (more flexible detection)
  const isSummary = text.toLowerCase().includes('summary of codebase') ||
                    text.toLowerCase().includes('project summary') ||
                    text.toLowerCase().includes('accomplishments') ||
                    text.toLowerCase().includes('execution highlights') ||
                    text.toLowerCase().includes('codebase generation') ||
                    (text.includes('*') && text.includes(':') && text.length > 100);

  if (!isSummary) return null;

  const result = {
    title: '',
    sections: [],
    stats: {},
    raw: text
  };

  // Extract title - more flexible pattern
  const titlePatterns = [
    /###?\s*\*\*Project Summary:\*\*\s*(.+?)(?:\n|$)/i,
    /Project Summary:?\s*(.+?)(?:\n|$)/i,
    /##?\s*(.+? Application)/i,
    /^(.+? To-Do Application)/i,
  ];
  for (const pattern of titlePatterns) {
    const match = text.match(pattern);
    if (match) {
      result.title = match[1].trim();
      break;
    }
  }

  // If no title found, try to extract from first line
  if (!result.title) {
    const firstLine = text.split('\n').find(l => l.trim() && l.includes('*'));
    if (firstLine) {
      result.title = 'Code Generation Complete';
    }
  }

  // Parse all bullet points and key-value pairs
  const lines = text.split('\n');
  const bullets = [];
  const sectionBullets = {};

  lines.forEach(line => {
    line = line.trim();
    if (!line) return;

    // Match bullet points like "* **Key:** value" or "* Key"
    const bulletMatch = line.match(/^\*\*?\s*(.+?)(?:\*\*:?|\s*:\s*)(.+)$/);
    if (bulletMatch) {
      const key = bulletMatch[1].trim().replace(/\*\*?/g, '').trim();
      const value = bulletMatch[2].trim();
      if (value && (key.toLowerCase().includes('rate') || key.toLowerCase().includes('files') || key.toLowerCase().includes('error') || key.toLowerCase().includes('success'))) {
        result.stats[key] = value;
      } else {
        bullets.push(`${key}: ${value}`);
      }
    } else if (line.startsWith('* ')) {
      // Simple bullet point
      const content = line.replace(/^\*\s*/, '').trim();
      if (content) bullets.push(content);
    }
  });

  // Try to extract numeric stats
  const successMatch = text.match(/success.*?rate.*?(\d+%)/i);
  if (successMatch) result.stats['Success Rate'] = successMatch[1];

  const filesMatch = text.match(/(?:generated|files?)\D*(\d+)/i);
  if (filesMatch) result.stats['Files Generated'] = filesMatch[1];

  const errorsMatch = text.match(/errors?.*?(\d+)/i);
  if (errorsMatch) result.stats['Errors'] = errorsMatch[1];

  // Add sections if we have bullets
  if (bullets.length > 0) {
    result.sections.push({
      title: 'Key Accomplishments',
      bullets: bullets.slice(0, 8), // Limit to 8 items
      stats: {...result.stats}
    });
  }

  // If we found stats but no sections, add a stats section
  if (Object.keys(result.stats).length > 0 && result.sections.length === 0) {
    result.sections.push({
      title: 'Results',
      bullets: [],
      stats: {...result.stats}
    });
  }

  return result;
};

/* ========== WORKFLOW STAGES ========== */

// Code generation workflow (ends at Dependency Setup)
const WORKFLOW_STAGES = [
  { id: 'analysis', label: 'Requirement Analysis', icon: Brain },
  { id: 'architecture', label: 'Architecture Planning', icon: Layout },
  { id: 'generation', label: 'Code Generation', icon: Code },
  { id: 'files', label: 'File Creation', icon: FileCode },
  { id: 'dependencies', label: 'Dependency Setup', icon: Package },
  { id: 'completed', label: 'Completed', icon: CheckCircle },
];

// Full workflow stages including debugging (shown when QA starts)
const FULL_WORKFLOW_STAGES = [
  { id: 'analysis', label: 'Requirement Analysis', icon: Brain },
  { id: 'architecture', label: 'Architecture Planning', icon: Layout },
  { id: 'generation', label: 'Code Generation', icon: Code },
  { id: 'files', label: 'File Creation', icon: FileCode },
  { id: 'dependencies', label: 'Dependency Setup', icon: Package },
  { id: 'debugging', label: 'Debugging & QA', icon: Bug },
  { id: 'fixing_bugs', label: 'Fixing Bugs', icon: Wrench },
  { id: 'packaging', label: 'Packaging', icon: Archive },
  { id: 'completed', label: 'Completed', icon: CheckCircle },
];

/* ========== SUB-COMPONENTS ========== */

// Workflow Progress Indicator
const WorkflowProgress = ({ currentStage, progress, stages = WORKFLOW_STAGES, isDebugMode = false, debugIteration = 0, bugsFound = 0, bugsFixed = 0 }) => {
  const currentIndex = stages.findIndex(s => s.id === currentStage) || 0;

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">Workflow Progress</span>
          {isDebugMode && (
            <span className="px-2 py-0.5 text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded-full">
              Debug Round {debugIteration}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {isDebugMode && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-red-600 dark:text-red-400">🐛 {bugsFound}</span>
              <span className="text-emerald-600 dark:text-emerald-400">✓ {bugsFixed}</span>
            </div>
          )}
          <span className="text-xs font-medium text-blue-600 dark:text-blue-400">{Math.round(progress)}%</span>
        </div>
      </div>

      <div className="relative h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden mb-4">
        <div
          className={`absolute inset-y-0 left-0 rounded-full transition-all duration-500 ${
            isDebugMode
              ? 'bg-gradient-to-r from-amber-500 to-orange-500'
              : 'bg-gradient-to-r from-blue-500 to-cyan-500'
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="flex flex-wrap gap-1">
        {stages.map((stage, idx) => {
          const Icon = stage.icon;
          const isActive = idx === currentIndex;
          const isCompleted = idx < currentIndex;
          const isDebugStage = stage.id.startsWith('debug_') || stage.id === 'detect_bugs' || stage.id === 'analyze_errors' || stage.id === 'apply_fixes' || stage.id === 'rebuild_docker' || stage.id === 'validate_qa' || stage.id === 'repackage';

          return (
            <div
              key={stage.id}
              className={`
                flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium
                transition-all duration-300
                ${isCompleted
                  ? isDebugStage
                    ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                    : 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                  : isActive
                    ? isDebugStage
                      ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
                      : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
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

// Console Log Panel
const ConsoleLog = ({ logs, summary, isCollapsed, onToggleCollapse }) => {
  const logEndRef = useRef(null);

  useEffect(() => {
    if (!isCollapsed && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isCollapsed]);

  const getLogIcon = (type) => {
    switch (type) {
      case 'error': return <AlertCircle size={14} className="text-red-500" />;
      case 'warning': return <AlertCircle size={14} className="text-amber-500" />;
      case 'success': return <CheckCircle size={14} className="text-green-600" />;
      case 'debug': return <Bug size={14} className="text-purple-500" />;
      default: return <Terminal size={14} className="text-slate-400" />;
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm overflow-hidden">
      <button
        onClick={onToggleCollapse}
        className="w-full flex items-center justify-between p-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Terminal size={16} className="text-violet-500" />
          <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">Console Logs</span>
          <span className="text-xs text-slate-500 dark:text-slate-500">({logs.length})</span>
        </div>
        <ChevronDown size={18} className={`text-slate-400 transition-transform ${isCollapsed ? '-rotate-90' : ''}`} />
      </button>

      {!isCollapsed && (
        <div className="border-t border-slate-200 dark:border-slate-700">
          {/* Summary Card - displayed at top when available */}
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
                <div key={idx} className="flex items-start gap-2 animate-in fade-in slide-in-from-left-2 duration-150">
                  <span className="text-slate-400 dark:text-slate-500 shrink-0">
                    {new Date(log.timestamp).toLocaleTimeString('en-US', { hour12: false })}
                  </span>
                  {getLogIcon(log.type)}
                  <span className={`flex-1 break-all ${
                    log.type === 'error' ? 'text-red-600 dark:text-red-400' :
                    log.type === 'warning' ? 'text-amber-600 dark:text-amber-400' :
                    log.type === 'success' ? 'text-green-700 dark:text-green-400' :
                    log.type === 'debug' ? 'text-purple-600 dark:text-purple-400' :
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

// Structured Summary Card for displaying parsed terminal output
const SummaryCard = ({ summary, onDismiss }) => {
  if (!summary) return null;

  const hasStats = summary.stats && Object.keys(summary.stats).length > 0;
  const hasSections = summary.sections && summary.sections.length > 0;
  const hasBullets = hasSections && summary.sections.some(s => s.bullets && s.bullets.length > 0);

  // If nothing parsed, show the raw text in a nice format
  if (!hasStats && !hasBullets && summary.raw) {
    return (
      <div className="bg-white dark:bg-slate-900 border border-emerald-200 dark:border-emerald-800 rounded-xl shadow-sm overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-300">
        <div className="flex items-center justify-between p-3 bg-gradient-to-r from-emerald-50 to-cyan-50 dark:from-emerald-900/20 dark:to-cyan-900/20 border-b border-emerald-200 dark:border-emerald-800">
          <div className="flex items-center gap-2">
            <CheckCircle size={16} className="text-emerald-500" />
            <span className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">
              Generation Complete
            </span>
          </div>
        </div>
        <div className="p-3 max-h-48 overflow-y-auto">
          <div className="text-xs text-slate-600 dark:text-slate-300 whitespace-pre-wrap font-mono">
            {summary.raw}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-900 border border-emerald-200 dark:border-emerald-800 rounded-xl shadow-sm overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className="flex items-center justify-between p-3 bg-gradient-to-r from-emerald-50 to-cyan-50 dark:from-emerald-900/20 dark:to-cyan-900/20 border-b border-emerald-200 dark:border-emerald-800">
        <div className="flex items-center gap-2">
          <CheckCircle size={16} className="text-emerald-500" />
          <span className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">
            {summary.title || 'Generation Summary'}
          </span>
        </div>
        {onDismiss && (
          <button onClick={onDismiss} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
            <X size={14} />
          </button>
        )}
      </div>

      <div className="p-3 space-y-3 max-h-48 overflow-y-auto">
        {/* Stats Row */}
        {hasStats && (
          <div className="flex flex-wrap gap-2">
            {Object.entries(summary.stats).map(([key, value]) => (
              <div
                key={key}
                className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 rounded-lg text-xs font-medium"
              >
                <span className="text-slate-500 dark:text-slate-400">{key}: </span>
                <span className="text-slate-700 dark:text-slate-200">{value}</span>
              </div>
            ))}
          </div>
        )}

        {/* Sections */}
        {hasSections && summary.sections.map((section, idx) => (
          <div key={idx} className="space-y-1.5">
            <h4 className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
              {section.title}
            </h4>
            <ul className="space-y-1">
              {section.bullets && section.bullets.map((bullet, bIdx) => (
                <li key={bIdx} className="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-300">
                  <span className="text-emerald-500 mt-0.5">•</span>
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
};

// Chat Summary Display - inline version for chat messages
const ChatSummaryMessage = ({ summary }) => {
  if (!summary) return null;

  return (
    <div className="bg-gradient-to-br from-emerald-50 to-cyan-50 dark:from-emerald-900/20 dark:to-cyan-900/20 border border-emerald-200 dark:border-emerald-800 rounded-xl p-4 my-2">
      <div className="flex items-center gap-2 mb-3">
        <CheckCircle size={16} className="text-emerald-500" />
        <span className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">
          {summary.title || 'Generation Complete'}
        </span>
      </div>

      {/* Stats */}
      {Object.keys(summary.stats).length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {Object.entries(summary.stats).map(([key, value]) => (
            <div
              key={key}
              className="px-2 py-1 bg-white dark:bg-slate-800 rounded-md text-xs border border-emerald-100 dark:border-emerald-900"
            >
              <span className="text-slate-500 dark:text-slate-400">{key}: </span>
              <span className="font-semibold text-emerald-600 dark:text-emerald-400">{value}</span>
            </div>
          ))}
        </div>
      )}

      {/* Bullet points */}
      {summary.sections.map((section, idx) => (
        <div key={idx} className="mt-2">
          <h5 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase mb-1">
            {section.title}
          </h5>
          <ul className="space-y-0.5">
            {section.bullets.slice(0, 5).map((bullet, bIdx) => (
              <li key={bIdx} className="flex items-start gap-1.5 text-xs text-slate-600 dark:text-slate-300">
                <CheckCircle size={10} className="text-emerald-500 mt-0.5 shrink-0" />
                <span>{bullet}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
};

// File Explorer / Artifacts Panel
const FileExplorer = ({ files, isCollapsed, onToggleCollapse }) => {
  const [expandedDirs, setExpandedDirs] = useState({});

  const toggleDir = (dir) => {
    setExpandedDirs(prev => ({ ...prev, [dir]: !prev[dir] }));
  };

  // Build tree structure
  const fileTree = useMemo(() => {
    const tree = {};
    files.forEach(file => {
      const parts = file.split('/');
      let current = tree;
      parts.forEach((part, idx) => {
        if (!current[part]) {
          current[part] = idx === parts.length - 1 ? null : {};
        }
        if (current[part] !== null) {
          current = current[part];
        }
      });
    });
    return tree;
  }, [files]);

  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'js':
      case 'jsx':
      case 'ts':
      case 'tsx': return <FileCode size={14} className="text-yellow-500" />;
      case 'py': return <FileCode size={14} className="text-blue-500" />;
      case 'json': return <FileCode size={14} className="text-amber-500" />;
      case 'md': return <FileCode size={14} className="text-slate-500" />;
      case 'html':
      case 'css': return <FileCode size={14} className="text-orange-500" />;
      case 'yaml':
      case 'yml': return <FileCode size={14} className="text-red-500" />;
      case 'dockerfile':
      case 'docker': return <FileCode size={14} className="text-cyan-500" />;
      default: return <File size={14} className="text-slate-400" />;
    }
  };

  const renderTree = (node, path = '') => {
    return Object.entries(node).map(([name, children]) => {
      const fullPath = path ? `${path}/${name}` : name;
      const isDir = children !== null;
      const isExpanded = expandedDirs[fullPath];

      return (
        <div key={fullPath}>
          <div
            className={`
              flex items-center gap-1.5 py-1 px-2 rounded text-xs cursor-pointer
              hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors
              text-slate-700 dark:text-slate-300
            `}
            style={{ paddingLeft: path ? `${(path.split('/').length) * 12 + 8}px` : '8px' }}
          >
            {isDir ? (
              <button onClick={() => toggleDir(fullPath)} className="shrink-0 text-slate-400 hover:text-slate-600">
                {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
              </button>
            ) : (
              <span className="w-3" />
            )}
            {isDir ? (
              <Folder size={14} className="text-amber-500" />
            ) : (
              getFileIcon(name)
            )}
            <span className="truncate">{name}</span>
          </div>
          {isDir && isExpanded && renderTree(children, fullPath)}
        </div>
      );
    });
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm overflow-hidden">
      <button
        onClick={onToggleCollapse}
        className="w-full flex items-center justify-between p-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Folder size={16} className="text-amber-500" />
          <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">Generated Files</span>
          <span className="text-xs text-slate-500 dark:text-slate-500">({files.length})</span>
        </div>
        <ChevronDown size={18} className={`text-slate-400 transition-transform ${isCollapsed ? '-rotate-90' : ''}`} />
      </button>

      {!isCollapsed && (
        <div className="border-t border-slate-200 dark:border-slate-700">
          <div className="h-64 overflow-y-auto p-2 custom-scrollbar">
            {files.length === 0 ? (
              <div className="text-slate-400 dark:text-slate-500 italic text-xs p-2">No files generated yet...</div>
            ) : (
              renderTree(fileTree)
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Clean Chat Message
const ChatMessage = ({ msg }) => {
  const isUser = msg.type === 'user';
  const isSystem = msg.type === 'system';

  // Check for summary in message
  const hasSummary = msg.summary && Object.keys(msg.summary).length > 0;

  if (isSystem) {
    return (
      <div className="flex justify-center mb-4">
        <div className="bg-slate-100 dark:bg-slate-800 rounded-full px-4 py-1.5 text-xs text-slate-500 dark:text-slate-400">
          {msg.text}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div
        className={`
          max-w-[85%] rounded-xl shadow-sm
          ${isUser
            ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white p-3.5'
            : hasSummary
              ? 'bg-transparent p-0'
              : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 p-3.5'
          }
        `}
      >
        {!isUser && !hasSummary && (
          <div className="flex items-center gap-2 mb-2">
            <Sparkles size={12} className="text-amber-500" />
            <span className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
              AI Assistant
            </span>
          </div>
        )}

        {/* Display parsed summary if available */}
        {hasSummary ? (
          <ChatSummaryMessage summary={msg.summary} />
        ) : (
          <div className="text-sm leading-relaxed">
            {msg.text}
          </div>
        )}
      </div>
    </div>
  );
};

// Success Output Card
const SuccessOutput = ({ jobId, fileCount, downloadUrl, onReset }) => {
  const [copied, setCopied] = useState(false);

  const copyUrl = () => {
    if (downloadUrl) {
      navigator.clipboard.writeText(downloadUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-gradient-to-br from-emerald-50 to-cyan-50 dark:from-emerald-900/20 dark:to-cyan-900/20 border border-emerald-200 dark:border-emerald-800 rounded-xl p-5 animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center shrink-0">
          <Sparkles size={24} className="text-white" />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-emerald-800 dark:text-emerald-300 mb-1">
            Generation Complete!
          </h3>
          <p className="text-sm text-emerald-700 dark:text-emerald-400 mb-3">
            Your project has been generated successfully with {fileCount} files.
          </p>

          <div className="flex flex-wrap gap-2">
            {downloadUrl && (
              <a
                href={downloadUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white rounded-lg text-sm font-medium hover:shadow-lg hover:shadow-emerald-500/25 transition-all"
              >
                <Download size={16} />
                Download ZIP
              </a>
            )}
            <button
              onClick={copyUrl}
              className="inline-flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
            >
              {copied ? <CheckCircle size={16} /> : <Copy size={16} />}
              {copied ? 'Copied!' : 'Copy Link'}
            </button>
            <button
              onClick={onReset}
              className="inline-flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
            >
              <RefreshCw size={16} />
              New Project
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

/* ========== MAIN COMPONENT ========== */

const Codegen = () => {
  // State
  const [messages, setMessages] = useState([
    { id: 1, type: 'system', text: 'Welcome to iSDS Code Generator' },
    { id: 2, type: 'ai', text: 'Hi! I\'m ready to help you generate code. Describe your project requirements and I\'ll create a complete implementation.' }
  ]);
  const [input, setInput] = useState('');
  const [status, setStatus] = useState('idle'); // idle, working, completed, error, debugging
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([]);
  const [parsedSummary, setParsedSummary] = useState(null);
  const [files, setFiles] = useState([]);
  const [currentStage, setCurrentStage] = useState(null); // Start with null - no stage active until user submits

  // UI State
  const [consoleCollapsed, setConsoleCollapsed] = useState(false);
  const [filesCollapsed, setFilesCollapsed] = useState(false);
  const [jobIdFromBackend, setJobIdFromBackend] = useState(null);
  const [leftPanelWidth, setLeftPanelWidth] = useState(55);
  const containerRef = useRef(null);
  const [askDebugging, setAskDebugging] = useState(false);
  const [isDebugging, setIsDebugging] = useState(false);

  // Debug tracking state
  const [debugIteration, setDebugIteration] = useState(0);
  const [bugsFound, setBugsFound] = useState(0);
  const [bugsFixed, setBugsFixed] = useState(0);
  const [activeStages, setActiveStages] = useState(WORKFLOW_STAGES);
  const [isDebugMode, setIsDebugMode] = useState(false);
  const [debugErrorCount, setDebugErrorCount] = useState(0);

  // Refs
  const messagesEndRef = useRef(null);

  // Debounced progress update
  const [displayProgress, setDisplayProgress] = useState(0);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Debounce progress updates for smoother UI
  useEffect(() => {
    const timer = setTimeout(() => {
      setDisplayProgress(progress);
    }, 100);
    return () => clearTimeout(timer);
  }, [progress]);

  // Only add important logs to console (filter noise)
  const addLog = useCallback((text, type = 'info') => {
    // Check for summary first
    const summary = parseSummary(text);
    if (summary) {
      setParsedSummary(summary);
    }

    // Filter: show more messages including all summaries
    const lower = text.toLowerCase();
    const isImportant = type === 'error' || type === 'warning' || type === 'success' ||
      lower.includes('started') || lower.includes('completed') || lower.includes('ready') ||
      lower.includes('generated') || lower.includes('created') || lower.includes('failed') ||
      lower.includes('error') || lower.includes('warning') ||
      lower.includes('summary of codebase') || lower.includes('project summary') ||
      lower.includes('accomplishments') || lower.includes('execution highlights') ||
      lower.includes('codebase generation') || lower.includes('node:') ||
      summary; // Show all summaries

    if (isImportant || type === 'error' || type === 'success') {
      setLogs(prev => [...prev, { text, type, timestamp: Date.now(), summary }]);
    }
  }, []);

  // Last stage for tracking changes
  const lastStageRef = useRef(null);

  // Determine current stage based on progress
  const updateStage = useCallback((progressVal) => {
    let newStage = 'analysis';
    if (progressVal < 12) newStage = 'analysis';
    else if (progressVal < 25) newStage = 'architecture';
    else if (progressVal < 50) newStage = 'generation';
    else if (progressVal < 70) newStage = 'files';
    else if (progressVal < 85) newStage = 'dependencies';
    else if (progressVal < 95) newStage = 'debugging';
    else if (progressVal < 100) newStage = 'packaging';
    else newStage = 'completed';

    setCurrentStage(newStage);

    // Only add stage updates to chat when stage changes
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
        completed: 'All done!'
      };
      if (newStage !== 'completed') {
        addChatMessage(stageMessages[newStage], 'ai');
      }
    }
  }, []);

  // Update debugging stage based on events from backend
  const updateDebugStage = useCallback((event, statusMessage, progressVal) => {
    let newStage = 'debugging';

    // Map events to debug stages
    if (event === 'debug_started' || event === 'debug_start') {
      newStage = 'debugging';
      setIsDebugMode(true);
      setActiveStages(FULL_WORKFLOW_STAGES);
      setDebugIteration(prev => prev + 1);
    } else if (event === 'detect_bugs' || statusMessage?.toLowerCase().includes('detecting') || statusMessage?.toLowerCase().includes('analyzing')) {
      newStage = 'debugging';
    } else if (event === 'analyze_errors' || event === 'apply_fixes' || statusMessage?.toLowerCase().includes('fix') || statusMessage?.toLowerCase().includes('applying')) {
      newStage = 'fixing_bugs';
    } else if (event === 'rebuild_docker' || statusMessage?.toLowerCase().includes('rebuild') || statusMessage?.toLowerCase().includes('building')) {
      newStage = 'fixing_bugs';
    } else if (event === 'validate_qa' || statusMessage?.toLowerCase().includes('validating') || statusMessage?.toLowerCase().includes('qa')) {
      newStage = 'fixing_bugs';
    } else if (event === 'repackage' || statusMessage?.toLowerCase().includes('repackage') || statusMessage?.toLowerCase().includes('packaging')) {
      newStage = 'packaging';
    } else if (event === 'debug_completed' || event === 'debug_complete' || progressVal >= 100) {
      newStage = 'completed';
      setIsDebugMode(false);
    }

    setCurrentStage(newStage);

    // Update progress based on debug stage
    const stageProgress = {
      'debugging': 15,
      'fixing_bugs': 50,
      'packaging': 80,
      'completed': 100
    };
    setProgress(stageProgress[newStage] || progressVal);
  }, []);

  // Add clean message to chat (only for user prompts and AI responses)
  const addChatMessage = useCallback((text, type = 'ai', summary = null) => {
    // Try to parse summary if not provided
    const parsedSummary = summary || parseSummary(text);
    setMessages(prev => [...prev, {
      id: `msg-${Date.now()}`,
      type,
      text: parsedSummary ? '' : text, // Hide raw text if we have summary
      summary: parsedSummary
    }]);
  }, []);

  // Handle sending message
  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || status === 'working') return;

    // Validate: Check if requirements are meaningful (not just placeholders or empty)
    const trimmedInput = input.trim().toLowerCase();
    if (!trimmedInput || trimmedInput.length < 10) {
      setStatus('idle');
      addChatMessage('Please write requirements for an application only. Describe what you want to build, including features, functionality, and any specific details.', 'ai');
      return;
    }

    const userText = input.trim();
    setInput('');
    setStatus('working');
    setProgress(0);
    setCurrentStage('analysis');

    // Add user message
    setMessages(prev => [...prev, { id: `user-${Date.now()}`, type: 'user', text: userText }]);

    // Add thinking indicator
    const thinkingId = `thinking-${Date.now()}`;
    setMessages(prev => [...prev, { id: thinkingId, type: 'system', text: 'Processing your request...' }]);

    addLog(`User input: "${userText.substring(0, 40)}..."`, 'info');

    try {
      const res = await fetch(`${API_BASE_URL}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirements: userText }),
      });

      if (!res.ok || !res.body) {
        throw new Error(`Backend error: HTTP ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8', { fatal: false });
      let buffer = '';
      let currentJobId = null;
      let currentDownloadUrl = null;

      // Remove thinking message and add initial AI response
      setMessages(prev => prev.filter(m => m.id !== thinkingId));
      // Stage-based messages will be added by updateStage callback

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        try {
          buffer += decoder.decode(value, { stream: true });
        } catch (e) {
          const fallbackDecoder = new TextDecoder('utf-8', { fatal: false });
          buffer += fallbackDecoder.decode(value, { stream: true });
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
            // Non-JSON text - log it but don't spam chat
            if (trimmed.length > 5) {
              const type = categorizeLog(trimmed);
              addLog(trimmed, type);
            }
            continue;
          }

          const { event, job_id, comprehensive_status, progress: jobProgress, files_done, response_type, ask_debugging } = payload;

          // Store job ID
          if (job_id && !currentJobId) {
            currentJobId = job_id;
            currentDownloadUrl = `${API_BASE_URL}/download/${job_id}`;
            setJobIdFromBackend(job_id);
          }

          // Update progress
          if (jobProgress !== undefined && jobProgress !== null) {
            const value = typeof jobProgress === 'string'
              ? parseFloat(jobProgress.replace('%', ''))
              : Number(jobProgress);
            if (!Number.isNaN(value)) {
              setProgress(value);
              updateStage(value);
            }
          }

          // Update files
          if (Array.isArray(files_done) && files_done.length > 0) {
            setFiles(prev => {
              const s = new Set(prev);
              files_done.forEach(f => s.add(f));
              return Array.from(s);
            });
          }

          // Handle events
          if (event === 'started') {
            addLog('Code generation started', 'info');
          }

          if (event === 'update' && comprehensive_status) {
            const cleanStatus = stripAnsi(comprehensive_status);
            const type = categorizeLog(cleanStatus);
            addLog(cleanStatus, type);
          }

          if (event === 'error' && comprehensive_status) {
            const cleanStatus = stripAnsi(comprehensive_status);
            addLog(cleanStatus, 'error');
          }

          if (event === 'completed') {
            setProgress(100);
            setCurrentStage('completed');

            const cleanStatus = comprehensive_status ? stripAnsi(comprehensive_status) : 'Code generation complete!';
            addLog(cleanStatus, 'success');

            // Try to parse summary from completion message
            const summary = parseSummary(cleanStatus);
            if (summary) {
              setParsedSummary(summary);
            } else {
              // Create a basic summary from available data
              const fileCount = files_done?.length || files.length || 0;
              setParsedSummary({
                title: 'Code Generation Complete',
                sections: [{
                  title: 'Results',
                  bullets: [`Generated ${fileCount} files`],
                  stats: { 'Files Generated': fileCount.toString() }
                }],
                stats: { 'Files Generated': fileCount.toString() },
                raw: cleanStatus
              });
            }

            // Update final files
            if (Array.isArray(files_done) && files_done.length > 0) {
              setFiles(prev => {
                const s = new Set(prev);
                files_done.forEach(f => s.add(f));
                return Array.from(s);
              });
            }

            // Check if we should ask about debugging
            if (ask_debugging) {
              setStatus('ask_debugging');
              setAskDebugging(true);
              addChatMessage('Your project is ready! Would you like me to run the debugging process to check for any issues?', 'ai');
            } else {
              setStatus('completed');
              addChatMessage(`Your project is ready! I've generated ${files.length || files_done?.length || 0} files. You can download the complete package as a ZIP file.`, 'ai');
            }
          }
        }
      }
    } catch (err) {
      const errorMsg = `Error: ${String(err)}`;
      addLog(errorMsg, 'error');
      setStatus('error');
      addChatMessage('Sorry, an error occurred during code generation. Please check the logs or try again.', 'ai');
    } finally {
      if (status === 'working') {
        setStatus('idle');
      }
    }
  };

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

  const handleReset = () => {
    setMessages([
      { id: 1, type: 'system', text: 'Ready for new project' },
      { id: 2, type: 'ai', text: 'What would you like to build next?' }
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
    // Reset debug tracking state
    setDebugIteration(0);
    setBugsFound(0);
    setBugsFixed(0);
    setIsDebugMode(false);
    setDebugErrorCount(0);
    setActiveStages(WORKFLOW_STAGES);
  };

  // Handle debugging confirmation
  const handleDebuggingResponse = async (wantsDebug) => {
    if (!wantsDebug) {
      setAskDebugging(false);
      setStatus('completed');
      addLog('User opted to skip debugging', 'info');
      return;
    }

    // User wants to debug - reset debug tracking state
    setAskDebugging(false);
    setIsDebugging(true);
    setStatus('debugging');
    setProgress(0);
    setDebugIteration(0);
    setBugsFound(0);
    setBugsFixed(0);
    setDebugErrorCount(0);
    setIsDebugMode(true);
    setActiveStages(FULL_WORKFLOW_STAGES);
    setCurrentStage('debugging');
    addLog('Starting debugging process...', 'info');

    try {
      const res = await fetch(`${API_BASE_URL}/run-debug`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: jobIdFromBackend,
          requirements: messages.find(m => m.type === 'user')?.text || ''
        }),
      });

      if (!res.ok || !res.body) {
        throw new Error(`Debugging error: HTTP ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8', { fatal: false });
      let buffer = '';
      let debugRound = 0;

      addChatMessage('Running debugging process...', 'ai');

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        try {
          buffer += decoder.decode(value, { stream: true });
        } catch (e) {
          const fallbackDecoder = new TextDecoder('utf-8', { fatal: false });
          buffer += fallbackDecoder.decode(value, { stream: true });
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
            continue;
          }

          const { event, comprehensive_status, progress: debugProgress, files_done, response_type, bugs_detected, bugs_fixed, error_count } = payload;

          // Update debug tracking metrics from backend
          if (bugs_detected !== undefined) {
            setBugsFound(bugs_detected);
          }
          if (bugs_fixed !== undefined) {
            setBugsFixed(bugs_fixed);
          }
          if (error_count !== undefined) {
            setDebugErrorCount(error_count);
          }

          // Update debug stage based on incoming events
          if (event && (event.startsWith('debug_') || event === 'detect_bugs' || event === 'analyze_errors' || event === 'apply_fixes' || event === 'rebuild_docker' || event === 'validate_qa' || event === 'repackage')) {
            updateDebugStage(event, comprehensive_status, debugProgress ? Number(debugProgress) : 0);
          } else if (comprehensive_status) {
            // Analyze status message for debugging stage clues
            updateDebugStage(null, comprehensive_status, debugProgress ? Number(debugProgress) : 0);
          }

          if (debugProgress !== undefined && debugProgress !== null) {
            setProgress(Number(debugProgress));
          }

          if (comprehensive_status) {
            const cleanStatus = stripAnsi(comprehensive_status);
            const logType = categorizeLog(cleanStatus);
            addLog(cleanStatus, logType);
            addChatMessage(cleanStatus, 'ai');

            // Track bug detection from logs
            if (cleanStatus.toLowerCase().includes('error') || cleanStatus.toLowerCase().includes('failed')) {
              const errorMatches = cleanStatus.match(/error|failed|exception/gi);
              if (errorMatches) {
                setBugsFound(prev => prev + errorMatches.length);
              }
            }

            // Track bug fixes from logs
            if (cleanStatus.toLowerCase().includes('fixed') || cleanStatus.toLowerCase().includes('success')) {
              setBugsFixed(prev => prev + 1);
            }
          }

          if (files_done && Array.isArray(files_done)) {
            setFiles(prev => {
              const s = new Set(prev);
              files_done.forEach(f => s.add(f));
              return Array.from(s);
            });
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
      const errorMsg = `Debugging error: ${String(err)}`;
      addLog(errorMsg, 'error');
      setStatus('completed');
      setIsDebugging(false);
      setIsDebugMode(false);
      addChatMessage('Debugging encountered an error. You can try again or proceed with the current version.', 'ai');
    }
  };

  return (
    <div className="h-[calc(100vh)] flex flex-col bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <header className="h-14 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-5 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
            <Code2 size={18} className="text-white" />
          </div>
          <h1 className="text-lg font-semibold text-slate-700 dark:text-slate-100">
            Code Generator
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-3 py-1 rounded-full text-xs font-medium border ${
            status === 'working'
              ? 'bg-amber-50 text-amber-600 border-amber-200 animate-pulse'
              : status === 'completed'
                ? 'bg-emerald-50 text-emerald-600 border-emerald-200'
                : 'bg-blue-50 text-blue-600 border-blue-200'
          }`}>
            {status === 'working' ? 'Generating...' : status === 'completed' ? 'Complete' : 'Ready'}
          </span>
        </div>
      </header>

      {/* Main Content - Resizable Layout */}
      <div className="flex-1 flex overflow-hidden" ref={containerRef}>
        {/* LEFT COLUMN - Chat */}
        <div
          style={{ width: `${leftPanelWidth}%` }}
          className="flex flex-col border-r border-slate-200 dark:border-slate-800 min-w-[300px]"
        >
          {/* Chat Messages */}
          <div
            className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar"
          >
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

          {/* Debugging Confirmation Prompt */}
          {(askDebugging || status === 'ask_debugging') && !isDebugging && (
            <div className="p-4 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 shrink-0">
              <div className="flex flex-col items-center gap-3 py-2">
                <p className="text-sm text-slate-700 dark:text-slate-200 font-medium">
                  Do you want to start the debugging process now?
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={() => handleDebuggingResponse(true)}
                    className="px-6 py-2 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white rounded-lg text-sm font-medium hover:shadow-lg hover:shadow-emerald-500/25 transition-all flex items-center gap-2"
                  >
                    <Bug size={16} />
                    Yes, debug it
                  </button>
                  <button
                    onClick={() => handleDebuggingResponse(false)}
                    className="px-6 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 rounded-lg text-sm font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-all"
                  >
                    No, skip
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Debugging in Progress */}
          {isDebugging && (
            <div className="p-4 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 shrink-0">
              <div className="flex items-center justify-center gap-3 py-2">
                <Loader2 size={18} className="animate-spin text-amber-500" />
                <span className="text-sm text-amber-600 dark:text-amber-400 font-medium">Running debugging process...</span>
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="p-4 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 shrink-0">
            <form onSubmit={handleSend} className="relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Describe your project requirements..."
                disabled={status === 'working'}
                className="w-full pl-4 pr-12 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:border-blue-500 focus:dark:border-blue-500 text-sm text-slate-700 dark:text-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all disabled:opacity-50"
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

        {/* RESIZE HANDLE */}
        <div
          onMouseDown={handleMouseDown}
          className="w-1.5 hover:w-1.5 bg-slate-200 dark:bg-slate-800 hover:bg-blue-500 dark:hover:bg-cyan-500 cursor-col-resize flex items-center justify-center transition-all duration-200 z-30 group border-l border-r border-slate-200 dark:border-slate-700"
        >
          <div className="h-10 w-0.5 bg-slate-400 dark:bg-slate-600 group-hover:bg-white rounded-full" />
        </div>

        {/* RIGHT COLUMN - Details */}
        <div className="flex-1 min-w-[300px] flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
            {/* Progress Section */}
            <WorkflowProgress
              currentStage={currentStage}
              progress={displayProgress}
              stages={activeStages}
              isDebugMode={isDebugMode}
              debugIteration={debugIteration}
              bugsFound={bugsFound}
              bugsFixed={bugsFixed}
            />

            {/* Console Logs */}
            <ConsoleLog
              logs={logs}
              summary={parsedSummary}
              isCollapsed={consoleCollapsed}
              onToggleCollapse={() => setConsoleCollapsed(!consoleCollapsed)}
            />

            {/* File Explorer */}
            <FileExplorer
              files={files}
              isCollapsed={filesCollapsed}
              onToggleCollapse={() => setFilesCollapsed(!filesCollapsed)}
            />

            {/* Success Output */}
            {status === 'completed' && (
              <SuccessOutput
                jobId={jobIdFromBackend}
                fileCount={files.length}
                downloadUrl={jobIdFromBackend ? `${API_BASE_URL}/download/${jobIdFromBackend}` : null}
                onReset={handleReset}
              />
            )}
          </div>
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
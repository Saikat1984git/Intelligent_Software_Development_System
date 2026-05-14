import React, { useState, useMemo } from 'react';
import { Folder, FileCode, File, ChevronDown, ChevronRight } from 'lucide-react';

/* ============================================================
   FileExplorer
   Collapsible file tree panel from Codegen.jsx.

   Props:
     files           string[] — flat list of file paths
     isCollapsed     bool
     onToggleCollapse fn
   ============================================================ */

const getFileIcon = (filename) => {
  const ext = filename.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'js': case 'jsx': case 'ts': case 'tsx':
      return <FileCode size={14} className="text-yellow-500" />;
    case 'py':
      return <FileCode size={14} className="text-blue-500" />;
    case 'json':
      return <FileCode size={14} className="text-amber-500" />;
    case 'md':
      return <FileCode size={14} className="text-slate-500" />;
    case 'html': case 'css':
      return <FileCode size={14} className="text-orange-500" />;
    case 'yaml': case 'yml':
      return <FileCode size={14} className="text-red-500" />;
    case 'dockerfile': case 'docker':
      return <FileCode size={14} className="text-cyan-500" />;
    default:
      return <File size={14} className="text-slate-400" />;
  }
};

const buildTree = (files) => {
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
};

const TreeNode = ({ name, children, path, darkMode }) => {
  const [expanded, setExpanded] = useState(false);
  const isDir = children !== null;
  const depth = path ? path.split('/').length : 0;

  return (
    <div>
      <div
        className={`
          flex items-center gap-1.5 py-1 px-2 rounded text-xs cursor-pointer
          hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors
          text-slate-700 dark:text-slate-300
        `}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        onClick={() => isDir && setExpanded(e => !e)}
      >
        {isDir ? (
          <span className="shrink-0 text-slate-400 hover:text-slate-600">
            {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          </span>
        ) : (
          <span className="w-3" />
        )}
        {isDir
          ? <Folder size={14} className="text-amber-500" />
          : getFileIcon(name)
        }
        <span className="truncate">{name}</span>
      </div>

      {isDir && expanded && children && Object.entries(children).map(([childName, childChildren]) => (
        <TreeNode
          key={childName}
          name={childName}
          children={childChildren}
          path={path ? `${path}/${childName}` : childName}
        />
      ))}
    </div>
  );
};

const FileExplorer = ({ files = [], isCollapsed, onToggleCollapse }) => {
  const fileTree = useMemo(() => buildTree(files), [files]);

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
        <ChevronDown
          size={18}
          className={`text-slate-400 transition-transform ${isCollapsed ? '-rotate-90' : ''}`}
        />
      </button>

      {!isCollapsed && (
        <div className="border-t border-slate-200 dark:border-slate-700">
          <div className="h-64 overflow-y-auto p-2 custom-scrollbar">
            {files.length === 0 ? (
              <div className="text-slate-400 dark:text-slate-500 italic text-xs p-2">
                No files generated yet...
              </div>
            ) : (
              Object.entries(fileTree).map(([name, children]) => (
                <TreeNode key={name} name={name} children={children} path={name} />
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileExplorer;

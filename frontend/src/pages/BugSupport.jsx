import React from 'react';
import {
  Bug,
  Clock,
  HardHat,
  AlertTriangle
} from 'lucide-react';

const BugSupport = () => {
  return (
    <div className="h-[calc(100vh)] flex flex-col bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <header className="h-14 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-5 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
            <Bug size={18} className="text-white" />
          </div>
          <h1 className="text-lg font-semibold text-slate-700 dark:text-slate-100">
            Bug Support
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-3 py-1 rounded-full text-xs font-medium border bg-amber-50 text-amber-600 border-amber-200">
            Coming Soon
          </span>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="max-w-lg w-full text-center">
          {/* Icon and Title */}
          <div className="mb-8">
            <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br from-amber-100 to-orange-100 dark:from-amber-900/30 dark:to-orange-900/30 mb-6">
              <HardHat size={48} className="text-amber-500 dark:text-amber-400" />
            </div>
            <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mb-3">
              Developers are Working on It
            </h2>
            <p className="text-slate-600 dark:text-slate-400 text-lg">
              We're building something amazing for you!
            </p>
          </div>

          {/* Coming Soon Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 rounded-full">
            <Clock size={16} className="text-slate-500 dark:text-slate-400" />
            <span className="text-sm font-medium text-slate-600 dark:text-slate-300">
              Expected release: Q3 2026
            </span>
          </div>
        </div>
      </div>

      <style>{`
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

export default BugSupport;
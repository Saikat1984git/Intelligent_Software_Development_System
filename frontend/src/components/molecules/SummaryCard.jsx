import React from 'react';
import { CheckCircle, X } from 'lucide-react';

/* ============================================================
   SummaryCard
   Structured summary card shown in ConsoleLog panel.
   Extracted from Codegen.jsx.

   Props:
     summary   { title, sections, stats, raw }
     onDismiss fn | undefined
   ============================================================ */

const SummaryCard = ({ summary, onDismiss }) => {
  if (!summary) return null;

  const hasStats    = summary.stats    && Object.keys(summary.stats).length > 0;
  const hasSections = summary.sections && summary.sections.length > 0;
  const hasBullets  = hasSections && summary.sections.some(s => s.bullets?.length > 0);

  // Fallback: show raw text nicely
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
          <button
            onClick={onDismiss}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          >
            <X size={14} />
          </button>
        )}
      </div>

      <div className="p-3 space-y-3 max-h-48 overflow-y-auto">
        {/* Stats row */}
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
              {section.bullets?.map((bullet, bIdx) => (
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

export default SummaryCard;

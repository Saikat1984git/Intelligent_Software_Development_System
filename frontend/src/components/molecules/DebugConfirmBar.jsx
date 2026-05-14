import React from 'react';
import { Bug, Loader2 } from 'lucide-react';

/* ============================================================
   DebugConfirmBar
   The bottom bar shown in Codegen's left (chat) panel after
   generation completes. Has two states:

   1. Confirm state  — "Do you want to start debugging?"
                       Yes / No buttons
   2. Progress state — "Running debugging process..."

   Extracted verbatim from Codegen.jsx — zero logic changes.

   Props:
     showConfirm   bool — show the Yes/No prompt
     isDebugging   bool — show the in-progress spinner
     onConfirm     fn(wantsDebug: bool) — called by both buttons
   ============================================================ */

const DebugConfirmBar = ({ showConfirm, isDebugging, onConfirm }) => {
  // Neither state active — render nothing
  if (!showConfirm && !isDebugging) return null;

  return (
    <div className="p-4 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 shrink-0">

      {/* --- Confirm prompt --- */}
      {showConfirm && !isDebugging && (
        <div className="flex flex-col items-center gap-3 py-2">
          <p className="text-sm text-slate-700 dark:text-slate-200 font-medium">
            Do you want to start the debugging process now?
          </p>
          <div className="flex gap-3">
            <button
              onClick={() => onConfirm(true)}
              className="px-6 py-2 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white rounded-lg text-sm font-medium hover:shadow-lg hover:shadow-emerald-500/25 transition-all flex items-center gap-2"
            >
              <Bug size={16} />
              Yes, debug it
            </button>
            <button
              onClick={() => onConfirm(false)}
              className="px-6 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 rounded-lg text-sm font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-all"
            >
              No, skip
            </button>
          </div>
        </div>
      )}

      {/* --- In-progress spinner --- */}
      {isDebugging && (
        <div className="flex items-center justify-center gap-3 py-2">
          <Loader2 size={18} className="animate-spin text-amber-500" />
          <span className="text-sm text-amber-600 dark:text-amber-400 font-medium">
            Running debugging process...
          </span>
        </div>
      )}
    </div>
  );
};

export default DebugConfirmBar;

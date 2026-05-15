import React, { useState } from 'react';
import { Download, Copy, CheckCircle, RefreshCw, Sparkles } from 'lucide-react';

/* ============================================================
   SuccessOutput
   The green "Generation Complete" card shown at the bottom of
   Codegen's right panel after a successful generation.
   Extracted verbatim from Codegen.jsx — zero logic changes.

   Props:
     jobId        string | null
     fileCount    number
     downloadUrl  string | null
     onReset      fn — clears the page for a new project
   ============================================================ */

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

        {/* Icon */}
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
            {/* Download ZIP */}
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

            {/* Copy link */}
            <button
              onClick={copyUrl}
              className="inline-flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
            >
              {copied ? <CheckCircle size={16} /> : <Copy size={16} />}
              {copied ? 'Copied!' : 'Copy Link'}
            </button>

            {/* New project */}
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

export default SuccessOutput;

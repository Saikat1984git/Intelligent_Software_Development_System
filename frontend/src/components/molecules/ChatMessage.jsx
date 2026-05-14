import React from 'react';
import { Sparkles, CheckCircle } from 'lucide-react';

/* ============================================================
   ChatMessage
   Extracted from Codegen.jsx — handles user, ai, and system
   message types. Renders a ChatSummaryMessage inline when
   msg.summary is present.
   ============================================================ */

/* --- Structured summary inline card (inside AI bubble) --- */
export const ChatSummaryMessage = ({ summary }) => {
  if (!summary) return null;

  return (
    <div className="bg-gradient-to-br from-emerald-50 to-cyan-50 dark:from-emerald-900/20 dark:to-cyan-900/20 border border-emerald-200 dark:border-emerald-800 rounded-xl p-4 my-2">
      <div className="flex items-center gap-2 mb-3">
        <CheckCircle size={16} className="text-emerald-500" />
        <span className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">
          {summary.title || 'Generation Complete'}
        </span>
      </div>

      {/* Stats pills */}
      {summary.stats && Object.keys(summary.stats).length > 0 && (
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

      {/* Bullet sections */}
      {summary.sections?.map((section, idx) => (
        <div key={idx} className="mt-2">
          <h5 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase mb-1">
            {section.title}
          </h5>
          <ul className="space-y-0.5">
            {section.bullets?.slice(0, 5).map((bullet, bIdx) => (
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

/* --- Chat bubble --- */
const ChatMessage = ({ msg }) => {
  if (!msg) return null;

  const isUser   = msg.type === 'user';
  const isSystem = msg.type === 'system';
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
      <div className={`
        max-w-[85%] rounded-xl shadow-sm
        ${isUser
          ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white p-3.5'
          : hasSummary
            ? 'bg-transparent p-0'
            : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 p-3.5'
        }
      `}>
        {!isUser && !hasSummary && (
          <div className="flex items-center gap-2 mb-2">
            <Sparkles size={12} className="text-amber-500" />
            <span className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
              AI Assistant
            </span>
          </div>
        )}

        {hasSummary
          ? <ChatSummaryMessage summary={msg.summary} />
          : <div className="text-sm leading-relaxed">{msg.text}</div>
        }
      </div>
    </div>
  );
};

export default ChatMessage;

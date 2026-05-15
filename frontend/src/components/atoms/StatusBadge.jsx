import React from 'react';

/* ============================================================
   StatusBadge
   Color-coded pill for Priority and State columns in the
   incident table. Designed to match the ServiceNow screenshot.

   Props:
     type    'priority' | 'state' | 'severity'
     value   string — e.g. '4-Low', 'Transferred', 'Medium'
     size    'sm' | 'md' (default: 'sm')
   ============================================================ */

/* --- Priority color map --- */
const PRIORITY_STYLES = {
  '1-critical': 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800',
  '1':          'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800',
  'critical':   'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800',

  '2-high':     'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 border border-orange-200 dark:border-orange-800',
  '2':          'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 border border-orange-200 dark:border-orange-800',
  'high':       'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 border border-orange-200 dark:border-orange-800',

  '3-moderate': 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 border border-yellow-200 dark:border-yellow-800',
  '3':          'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 border border-yellow-200 dark:border-yellow-800',
  'moderate':   'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 border border-yellow-200 dark:border-yellow-800',
  'medium':     'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 border border-yellow-200 dark:border-yellow-800',

  '4-low':      'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700',
  '4':          'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700',
  'low':        'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700',
};

/* --- State color map --- */
const STATE_STYLES = {
  'open':        'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800',
  'in progress': 'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-400 border border-cyan-200 dark:border-cyan-800',
  'transferred': 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 border border-purple-200 dark:border-purple-800',
  'resolved':    'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800',
  'closed':      'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-500 border border-slate-200 dark:border-slate-700',
  'pending':     'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800',
  'cancelled':   'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800',
};

/* --- Severity color map (for AI analysis panel) --- */
const SEVERITY_STYLES = {
  'critical': 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800',
  'high':     'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 border border-orange-200 dark:border-orange-800',
  'medium':   'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 border border-yellow-200 dark:border-yellow-800',
  'low':      'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700',
};

const DEFAULT_STYLE = 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700';

const StatusBadge = ({ type = 'state', value = '', size = 'sm' }) => {
  if (!value) return null;

  const key = value.toLowerCase();

  let colorClass = DEFAULT_STYLE;
  if (type === 'priority') colorClass = PRIORITY_STYLES[key] || DEFAULT_STYLE;
  else if (type === 'state')    colorClass = STATE_STYLES[key]    || DEFAULT_STYLE;
  else if (type === 'severity') colorClass = SEVERITY_STYLES[key] || DEFAULT_STYLE;

  const sizeClass = size === 'md'
    ? 'px-2.5 py-1 text-xs'
    : 'px-2 py-0.5 text-xs';

  return (
    <span className={`inline-flex items-center font-medium rounded-full whitespace-nowrap ${sizeClass} ${colorClass}`}>
      {value}
    </span>
  );
};

export default StatusBadge;

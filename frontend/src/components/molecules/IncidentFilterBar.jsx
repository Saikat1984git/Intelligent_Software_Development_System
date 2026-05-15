import React, { useState } from 'react';
import { Search, Plus, Filter, ChevronDown, LayoutGrid, Table2, X } from 'lucide-react';

/* ============================================================
   IncidentFilterBar
   Two sections:
   1. Top bar  — search with field selector + view toggle + New
   2. Filter builder — per-row conditions with AND/OR logic,
      matching the ServiceNow-style screenshot

   Props:
     search           string
     onSearchChange   fn(value, field)
     searchField      string  — which field is being searched
     onSearchFieldChange fn(field)
     conditions       array of { id, field, operator, value, logic }
     onConditionsChange fn(conditions)
     viewMode         'table' | 'grid'
     onViewModeChange fn
     onNew            fn
     onRun            fn  — applies filters
   ============================================================ */

/* Fields available for search and filter */
export const SEARCHABLE_FIELDS = [
  { value: 'all', label: 'All fields' },
  { value: 'id', label: 'Number' },
  { value: 'affected_user', label: 'Affected User' },
  { value: 'config_item', label: 'Config Item' },
  { value: 'category', label: 'Category' },
  { value: 'priority', label: 'Priority' },
  { value: 'state', label: 'State' },
  { value: 'assignment_group', label: 'Assignment Group' },
  { value: 'assigned_to', label: 'Assigned To' },
  { value: 'queue', label: 'Queue' },
  { value: 'short_desc', label: 'Description' },
];

const FIELD_OPTIONS = {
  category: ['Application', 'Data', 'Performance', 'Infrastructure', 'Security'],
  priority: ['1-Critical', '2-High', '3-Moderate', '4-Low'],
  state: ['Open', 'In Progress', 'Transferred', 'Resolved', 'Closed', 'Pending'],
};

const OPERATORS = ['is', 'is not', 'contains', 'starts with'];

const selectCls = `appearance-none pl-2.5 pr-6 py-1.5 text-xs rounded-lg border
  border-slate-200 dark:border-slate-700
  bg-slate-50 dark:bg-slate-800
  text-slate-700 dark:text-slate-200
  focus:ring-1 focus:ring-blue-400 focus:border-blue-400 outline-none
  cursor-pointer transition-colors`;

const inputCls = `px-2.5 py-1.5 text-xs rounded-lg border
  border-slate-200 dark:border-slate-700
  bg-slate-50 dark:bg-slate-800
  text-slate-700 dark:text-slate-200
  placeholder-slate-400 dark:placeholder-slate-500
  focus:ring-1 focus:ring-blue-400 focus:border-blue-400 outline-none
  transition-colors`;

/* ── Single filter condition row ── */
const ConditionRow = ({ condition, index, total, onChange, onRemove, onAddAfter }) => {
  const hasPresets = !!FIELD_OPTIONS[condition.field];

  return (
    <div className="flex items-center gap-2 flex-wrap">

      {/* Field selector */}
      <div className="relative">
        <select
          value={condition.field}
          onChange={e => onChange({ ...condition, field: e.target.value, value: '' })}
          className={`${selectCls} min-w-[130px]`}
        >
          {SEARCHABLE_FIELDS.filter(f => f.value !== 'all').map(f => (
            <option key={f.value} value={f.value}>{f.label}</option>
          ))}
        </select>
        <ChevronDown size={11} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
      </div>

      {/* Operator */}
      <div className="relative">
        <select
          value={condition.operator}
          onChange={e => onChange({ ...condition, operator: e.target.value })}
          className={`${selectCls} min-w-[100px]`}
        >
          {OPERATORS.map(op => (
            <option key={op} value={op}>{op}</option>
          ))}
        </select>
        <ChevronDown size={11} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
      </div>

      {/* Value — dropdown if presets exist, text input otherwise */}
      {hasPresets ? (
        <div className="relative">
          <select
            value={condition.value}
            onChange={e => onChange({ ...condition, value: e.target.value })}
            className={`${selectCls} min-w-[130px]`}
          >
            <option value="">Select...</option>
            {FIELD_OPTIONS[condition.field].map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
          <ChevronDown size={11} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
        </div>
      ) : (
        <input
          type="text"
          value={condition.value}
          onChange={e => onChange({ ...condition, value: e.target.value })}
          placeholder="Value..."
          className={`${inputCls} min-w-[140px]`}
        />
      )}

      {/* AND / OR — logic for NEXT row */}
      <div className="flex items-center rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden text-xs font-medium">
        <button
          onClick={() => onChange({ ...condition, logic: 'AND' })}
          className={`px-2.5 py-1.5 transition-colors ${condition.logic === 'AND'
              ? 'bg-blue-500 text-white'
              : 'bg-slate-50 dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
        >
          AND
        </button>
        <button
          onClick={() => onChange({ ...condition, logic: 'OR' })}
          className={`px-2.5 py-1.5 transition-colors ${condition.logic === 'OR'
              ? 'bg-blue-500 text-white'
              : 'bg-slate-50 dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
            }`}
        >
          OR
        </button>
      </div>

      {/* Remove row */}
      <button
        onClick={onRemove}
        className="p-1.5 rounded-lg text-slate-400 hover:text-red-500
          hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
        title="Remove condition"
      >
        <X size={14} />
      </button>
    </div>
  );
};

/* ── Main component ── */
const IncidentFilterBar = ({
  search,
  onSearchChange,
  searchField = 'all',
  onSearchFieldChange,
  conditions = [],
  onConditionsChange,
  viewMode = 'table',
  onViewModeChange,
  onNew,
  onRun,
}) => {
  const [showBuilder, setShowBuilder] = useState(false);

  const addCondition = () => {
    onConditionsChange([
      ...conditions,
      {
        id: Date.now(),
        field: 'category',
        operator: 'is',
        value: '',
        logic: 'AND',  // logic joining THIS row to the NEXT
      },
    ]);
    setShowBuilder(true);
  };

  const updateCondition = (index, updated) => {
    const next = [...conditions];
    next[index] = updated;
    onConditionsChange(next);
  };

  const removeCondition = (index) => {
    const next = conditions.filter((_, i) => i !== index);
    onConditionsChange(next);
    if (next.length === 0) setShowBuilder(false);
  };

  const activeCount = conditions.filter(c => c.value).length;

  return (
    <div className="bg-white dark:bg-slate-900
      border-b border-slate-200 dark:border-slate-800 shrink-0">

      {/* ── Top bar ── */}
      <div className="flex items-center gap-2 px-4 py-2.5 flex-wrap gap-y-2">

        {/* Filter icon + builder toggle */}
        <button
          onClick={() => setShowBuilder(s => !s)}
          title="Toggle filter builder"
          className={`p-1.5 rounded-lg transition-colors ${showBuilder || activeCount > 0
              ? 'text-blue-500 bg-blue-50 dark:bg-blue-900/20'
              : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
        >
          <Filter size={15} />
        </button>

        {activeCount > 0 && (
          <span className="text-xs font-medium text-blue-600 dark:text-blue-400
            bg-blue-50 dark:bg-blue-900/20 px-2 py-0.5 rounded-full">
            {activeCount} filter{activeCount > 1 ? 's' : ''}
          </span>
        )}

        {/* Search field selector */}
        <div className="relative">
          <select
            value={searchField}
            onChange={e => onSearchFieldChange(e.target.value)}
            className={`${selectCls} min-w-[110px]`}
          >
            {SEARCHABLE_FIELDS.map(f => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
          <ChevronDown size={11} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
        </div>

        {/* Search input */}
        <div className="relative flex-1 min-w-[160px]">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          <input
            type="text"
            value={search}
            onChange={e => onSearchChange(e.target.value)}
            placeholder={
              searchField === 'all'
                ? 'Search all fields...'
                : `Search by ${SEARCHABLE_FIELDS.find(f => f.value === searchField)?.label}...`
            }
            className={`${inputCls} w-full pl-8 pr-3`}
          />
        </div>

        {/* Grid / Table toggle */}
        <div className="flex items-center rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
          <button
            onClick={() => onViewModeChange('table')}
            title="Table view"
            className={`p-1.5 transition-colors ${viewMode === 'table'
                ? 'bg-blue-500 text-white'
                : 'bg-slate-50 dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
              }`}
          >
            <Table2 size={14} />
          </button>
          <button
            onClick={() => onViewModeChange('grid')}
            title="Grid view"
            className={`p-1.5 transition-colors ${viewMode === 'grid'
                ? 'bg-blue-500 text-white'
                : 'bg-slate-50 dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
              }`}
          >
            <LayoutGrid size={14} />
          </button>
        </div>

        {/* New button */}
        <button
          onClick={onNew}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold
            bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-lg
            hover:from-blue-500 hover:to-blue-400 active:scale-95
            transition-all shadow-sm"
        >
          <Plus size={13} />
          New
        </button>
      </div>

      {/* ── Filter builder (collapsible) ── */}
      {showBuilder && (
        <div className="px-4 pb-3 border-t border-slate-100 dark:border-slate-800 pt-3">

          {/* Logic summary line */}
          {conditions.length > 0 && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-2.5">
              {conditions.every(c => c.logic === 'AND')
                ? 'All of these conditions must be met'
                : conditions.every(c => c.logic === 'OR')
                  ? 'Any of these conditions can be met'
                  : 'Conditions are evaluated in order with the selected AND/OR logic'
              }
            </p>
          )}

          {/* Condition rows */}
          <div className="flex flex-col gap-2">
            {conditions.map((cond, idx) => (
              <ConditionRow
                key={cond.id}
                condition={cond}
                index={idx}
                total={conditions.length}
                onChange={updated => updateCondition(idx, updated)}
                onRemove={() => removeCondition(idx)}
              />
            ))}
          </div>

          {/* Action row */}
          <div className="flex items-center gap-2 mt-3">
            <button
              onClick={addCondition}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium
                border border-slate-200 dark:border-slate-700
                bg-white dark:bg-slate-900
                text-slate-600 dark:text-slate-300
                hover:bg-slate-50 dark:hover:bg-slate-800
                rounded-lg transition-colors"
            >
              <Plus size={13} />
              Add condition
            </button>

            {conditions.length > 0 && (
              <>
                {/* Run button hidden for now — filtering is live/reactive */}

                <button
                  onClick={() => { onConditionsChange([]); setShowBuilder(false); }}
                  className="px-3 py-1.5 text-xs font-medium
                    text-slate-400 hover:text-red-500
                    dark:hover:text-red-400
                    transition-colors"
                >
                  Clear all
                </button>
              </>
            )}

            {conditions.length === 0 && (
              <span className="text-xs text-slate-400 dark:text-slate-500 italic">
                Add a condition to filter incidents
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default IncidentFilterBar;
import React from "react";
import { Bug, Clock, User, AlertCircle } from "lucide-react";
import StatusBadge from "../atoms/StatusBadge";

/* ============================================================
   IncidentTable
   One single <table> with:
   - table-layout: fixed  → columns keep explicit widths
   - thead sticky top-0   → header stays pinned while body scrolls
   - outer div overflow-auto → the ONE scrollable area
   The outer wrapper gets h-full from the parent so it fills
   the remaining space after the filter bar.
   ============================================================ */

const COL_WIDTHS = {
  Number: "110px",
  "Affected User": "120px",
  "Config Item": "110px",
  Category: "100px",
  Priority: "90px",
  State: "110px",
  "Assignment Group": "160px",
  "Escalated To": "110px",
  Queue: "140px",
  "Assigned To": "130px",
  Created: "145px",
  "SLA Due": "100px",
};

const COLUMNS = Object.keys(COL_WIDTHS);

const TableView = ({ incidents, selectedId, onSelect }) => (
  <div className="h-full overflow-auto custom-scrollbar">
    <table
      className="text-xs border-collapse"
      style={{ tableLayout: "fixed", width: "100%", minWidth: "1420px" }}
    >
      {/* Column width definitions */}
      <colgroup>
        {COLUMNS.map((col) => (
          <col key={col} style={{ width: COL_WIDTHS[col] }} />
        ))}
      </colgroup>

      {/* Sticky header — stays pinned, never scrolls */}
      <thead className="sticky top-0 z-10">
        <tr
          className="bg-slate-100 dark:bg-slate-800
          border-b border-slate-200 dark:border-slate-700"
        >
          {COLUMNS.map((col) => (
            <th
              key={col}
              className="px-3 py-2.5 text-left font-semibold whitespace-nowrap
                text-slate-600 dark:text-slate-300
                bg-slate-100 dark:bg-slate-800"
            >
              {col}
            </th>
          ))}
        </tr>
      </thead>

      {/* Scrollable body */}
      <tbody>
        {incidents.map((inc) => {
          const sel = selectedId === inc.id;
          const base = "cursor-pointer transition-colors";
          const on = "bg-blue-50 dark:bg-blue-900/20";
          const off = "hover:bg-slate-50 dark:hover:bg-slate-800/40";
          const border = "border-b border-slate-100 dark:border-slate-800/80";
          const left = sel
            ? "border-l-2 border-l-blue-500"
            : "border-l-2 border-l-transparent";

          return (
            <React.Fragment key={inc.id}>
              {/* Main data row */}
              <tr
                onClick={() => onSelect(inc)}
                className={`${base} ${border} ${left} ${sel ? on : off}`}
              >
                <td
                  className="px-3 py-2 font-medium truncate
                  text-blue-600 dark:text-blue-400"
                >
                  {inc.id}
                </td>
                <td className="px-3 py-2 truncate text-blue-600 dark:text-blue-400">
                  {inc.affected_user}
                </td>
                <td className="px-3 py-2 truncate text-blue-600 dark:text-blue-400">
                  {inc.config_item}
                </td>
                <td className="px-3 py-2 truncate text-slate-600 dark:text-slate-300">
                  {inc.category}
                </td>
                <td className="px-3 py-2">
                  <StatusBadge type="priority" value={inc.priority} />
                </td>
                <td className="px-3 py-2">
                  <StatusBadge type="state" value={inc.state} />
                </td>
                <td className="px-3 py-2 truncate text-blue-600 dark:text-blue-400">
                  {inc.assignment_group}
                </td>
                <td className="px-3 py-2 truncate text-slate-500 dark:text-slate-400">
                  {inc.escalated_to || (
                    <span className="text-slate-300 dark:text-slate-600">
                      (empty)
                    </span>
                  )}
                </td>
                <td className="px-3 py-2 truncate text-slate-600 dark:text-slate-300">
                  {inc.queue}
                </td>
                <td className="px-3 py-2 truncate text-blue-600 dark:text-blue-400">
                  {inc.assigned_to}
                </td>
                <td
                  className="px-3 py-2 font-mono truncate
                  text-slate-500 dark:text-slate-400"
                >
                  {inc.created}
                </td>
                <td className="px-3 py-2 truncate">
                  {inc.sla_due === "UNKNOWN" ? (
                    <span className="text-slate-400 dark:text-slate-500">
                      UNKNOWN
                    </span>
                  ) : (
                    <span className="text-red-500">{inc.sla_due}</span>
                  )}
                </td>
              </tr>

              {/* Short description sub-row */}
              <tr
                onClick={() => onSelect(inc)}
                className={`${base} ${left} ${sel ? on : off}
                  border-b border-slate-200 dark:border-slate-700/60`}
              >
                <td
                  colSpan={12}
                  className="px-3 pb-2 pt-0 text-xs italic
                    text-slate-400 dark:text-slate-500 truncate"
                >
                  {inc.short_desc}
                </td>
              </tr>
            </React.Fragment>
          );
        })}
      </tbody>
    </table>

    {incidents.length === 0 && <EmptyState />}
  </div>
);

/* ---- Grid view ---- */
const GridView = ({ incidents, selectedId, onSelect }) => (
  <div className="h-full overflow-y-auto custom-scrollbar p-3">
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {incidents.map((inc) => {
        const sel = selectedId === inc.id;
        return (
          <div
            key={inc.id}
            onClick={() => onSelect(inc)}
            className={`rounded-xl border p-4 cursor-pointer transition-all
              ${
                sel
                  ? "border-blue-400 dark:border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                  : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:border-blue-300 dark:hover:border-blue-600 hover:shadow-sm"
              }`}
          >
            <div className="flex items-start justify-between gap-2 mb-2">
              <span className="text-xs font-mono font-semibold text-blue-600 dark:text-blue-400">
                {inc.id}
              </span>
              <div className="flex gap-1.5 flex-wrap justify-end">
                <StatusBadge type="priority" value={inc.priority} />
                <StatusBadge type="state" value={inc.state} />
              </div>
            </div>
            <p
              className="text-xs font-medium text-slate-700 dark:text-slate-200
              leading-snug mb-3 line-clamp-2"
            >
              {inc.short_desc}
            </p>
            <div
              className="flex flex-wrap gap-x-3 gap-y-1 text-xs
              text-slate-500 dark:text-slate-400"
            >
              <span className="flex items-center gap-1">
                <User size={11} />
                {inc.affected_user}
              </span>
              <span className="flex items-center gap-1">
                <AlertCircle size={11} />
                {inc.config_item}
              </span>
              <span className="flex items-center gap-1">
                <Clock size={11} />
                {inc.created}
              </span>
            </div>
            <div
              className="mt-2 pt-2 border-t border-slate-100 dark:border-slate-800
              text-xs text-slate-400 dark:text-slate-500"
            >
              Assigned to{" "}
              <span className="text-blue-600 dark:text-blue-400 font-medium">
                {inc.assigned_to}
              </span>
              {" · "}
              {inc.assignment_group}
            </div>
          </div>
        );
      })}
    </div>
    {incidents.length === 0 && <EmptyState />}
  </div>
);

/* ---- Empty state ---- */
const EmptyState = () => (
  <div
    className="flex flex-col items-center justify-center h-48
    text-slate-400 dark:text-slate-500"
  >
    <Bug size={32} className="mb-3 opacity-40" />
    <p className="text-sm">No incidents match your filters</p>
  </div>
);

/* ---- Main export ---- */
const IncidentTable = ({
  incidents = [],
  selectedId,
  onSelect,
  viewMode = "table",
}) =>
  viewMode === "grid" ? (
    <GridView
      incidents={incidents}
      selectedId={selectedId}
      onSelect={onSelect}
    />
  ) : (
    <TableView
      incidents={incidents}
      selectedId={selectedId}
      onSelect={onSelect}
    />
  );

export default IncidentTable;

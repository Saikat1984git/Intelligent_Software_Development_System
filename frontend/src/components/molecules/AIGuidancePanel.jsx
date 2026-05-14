import React from "react";
import {
  Bug,
  Brain,
  Loader2,
  Cpu,
  ShieldAlert,
  CheckCircle,
  Users,
  FileText,
  ArrowRight,
  Send,
  Zap,
  BookOpen,
  Ticket,
  AlertTriangle,
  Terminal,
  Clock,
} from "lucide-react";
import WorkflowProgress, { BUGSUPPORT_STAGES } from "../atoms/WorkflowProgress";
import TerminalPane from "../atoms/TerminalPane";
import StatusBadge from "../atoms/StatusBadge";

/* ============================================================
   AIGuidancePanel

   ROOT: h-full flex flex-col overflow-hidden
   - Empty state: flex-1 centered — normal flow, no absolute
   - Content state: flex-1 overflow-y-auto — scrolls internally

   The parent in BugSupport is: flex-1 min-h-0 overflow-hidden
   That gives this component a bounded box to fill.
   ============================================================ */

const SOURCE_CONFIG = {
  past_ticket: { icon: Ticket, color: "text-blue-500", label: "Past ticket" },
  sop_document: {
    icon: FileText,
    color: "text-emerald-500",
    label: "SOP document",
  },
  known_error: {
    icon: AlertTriangle,
    color: "text-amber-500",
    label: "Known error",
  },
  app_log: {
    icon: Terminal,
    color: "text-purple-500",
    label: "App log pattern",
  },
};

const SimilarityBar = ({ value }) => {
  const pct = Math.round(value * 100);
  const color =
    pct >= 85 ? "bg-emerald-500" : pct >= 70 ? "bg-blue-500" : "bg-amber-500";
  return (
    <div className="flex items-center gap-1.5 shrink-0">
      <div className="w-16 h-1.5 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-slate-400 dark:text-slate-500 min-w-[28px]">
        {pct}%
      </span>
    </div>
  );
};

const KnowledgeSourcesCard = ({ sources }) => {
  if (!sources?.length) return null;
  return (
    <div
      className="bg-white dark:bg-slate-900 border border-slate-200
      dark:border-slate-700 rounded-xl p-4 shadow-sm shrink-0"
    >
      <h3
        className="text-sm font-semibold text-slate-700 dark:text-slate-200
        flex items-center gap-2 mb-3"
      >
        <BookOpen size={15} className="text-purple-500" />
        Knowledge sources used
        <span className="ml-auto text-xs font-normal text-slate-400 dark:text-slate-500">
          {sources.length} source{sources.length > 1 ? "s" : ""} found
        </span>
      </h3>
      <div className="space-y-2">
        {sources.map((src, idx) => {
          const cfg = SOURCE_CONFIG[src.type] || SOURCE_CONFIG.app_log;
          const Icon = cfg.icon;
          return (
            <div
              key={idx}
              className="flex gap-3 p-3 rounded-lg
              bg-slate-50 dark:bg-slate-800
              border border-slate-100 dark:border-slate-700"
            >
              <div className={`shrink-0 mt-0.5 ${cfg.color}`}>
                <Icon size={14} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <div className="min-w-0">
                    <span
                      className="text-xs font-medium text-slate-700
                      dark:text-slate-200 block truncate"
                    >
                      {src.title}
                    </span>
                    <span className={`text-xs ${cfg.color} opacity-80`}>
                      {cfg.label}
                    </span>
                  </div>
                  <SimilarityBar value={src.similarity} />
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mt-1">
                  {src.snippet}
                </p>
                {src.resolved_by && (
                  <p
                    className="text-xs text-emerald-600 dark:text-emerald-400
                    mt-1.5 flex items-center gap-1"
                  >
                    <CheckCircle size={11} />
                    {src.resolved_by}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

/* ══════════════════════════════════════════════════════════ */

const AIGuidancePanel = ({
  incident,
  isAnalysing,
  analysisStage,
  analysisProgress,
  logs = [],
  onAnalyse,
}) => {
  const analysis = incident?.ai_analysis;

  /* ── Root is always h-full flex flex-col ── */
  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* ══ EMPTY STATE — normal flow, NOT absolute ══ */}
      {!incident && (
        <div
          className="flex-1 flex flex-col items-center justify-center
          text-slate-400 dark:text-slate-500 p-8"
        >
          <div
            className="w-16 h-16 rounded-2xl bg-slate-100 dark:bg-slate-800
            flex items-center justify-center mb-4"
          >
            <Bug size={32} className="opacity-40" />
          </div>
          <p className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-1">
            No incident selected
          </p>
          <p className="text-xs text-center leading-relaxed">
            Click any row in the incident queue
            <br />
            to begin AI analysis
          </p>
        </div>
      )}

      {/* ══ CONTENT STATE — scrollable, also normal flow ══ */}
      {incident && (
        <div className="flex-1 overflow-y-auto custom-scrollbar p-4 flex flex-col gap-4">
          {/* Layer 1 — Incident summary */}
          <div
            className="bg-white dark:bg-slate-900 border border-slate-200
            dark:border-slate-700 rounded-xl p-4 shadow-sm shrink-0"
          >
            <div className="flex items-start gap-3 mb-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                  <span
                    className="text-xs font-mono font-semibold
                    text-blue-600 dark:text-blue-400"
                  >
                    {incident.id}
                  </span>
                  <StatusBadge type="priority" value={incident.priority} />
                  <StatusBadge type="state" value={incident.state} />
                </div>
                <p className="text-sm font-medium text-slate-700 dark:text-slate-200 leading-snug">
                  {incident.short_desc}
                </p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs mb-4">
              {[
                { label: "Affected User", value: incident.affected_user },
                { label: "Config Item", value: incident.config_item },
                { label: "Category", value: incident.category },
                { label: "Assignment", value: incident.assignment_group },
                { label: "Assigned To", value: incident.assigned_to },
                { label: "Created", value: incident.created },
              ].map(({ label, value }) => (
                <div key={label} className="flex gap-1.5">
                  <span className="text-slate-400 dark:text-slate-500 shrink-0">
                    {label}:
                  </span>
                  <span className="text-slate-700 dark:text-slate-200 font-medium truncate">
                    {value}
                  </span>
                </div>
              ))}
            </div>

            {!analysis && !isAnalysing && (
              <button
                onClick={() => onAnalyse(incident)}
                className="w-full py-2.5 px-4 rounded-xl flex items-center justify-center gap-2
                  font-semibold text-white text-sm shadow-lg shadow-blue-500/20
                  bg-gradient-to-r from-blue-600 to-blue-500
                  hover:-translate-y-0.5 hover:shadow-blue-500/30
                  active:translate-y-0 transition-all"
              >
                <Brain size={16} />
                Analyse with AI
              </button>
            )}
            {isAnalysing && (
              <div
                className="flex items-center justify-center gap-2 py-2
                text-sm text-blue-600 dark:text-blue-400"
              >
                <Loader2 size={16} className="animate-spin" />
                AI is analysing this incident...
              </div>
            )}
          </div>

          {/* Workflow progress */}
          {(isAnalysing || analysis) && (
            <div className="shrink-0">
              <WorkflowProgress
                currentStage={analysis ? "completed" : analysisStage}
                progress={analysis ? 100 : analysisProgress}
                stages={BUGSUPPORT_STAGES}
              />
            </div>
          )}

          {/* Analysis results */}
          {analysis && (
            <>
              {/* Layer 2 — Extracted information */}
              <div
                className="bg-white dark:bg-slate-900 border border-slate-200
                dark:border-slate-700 rounded-xl p-4 shadow-sm shrink-0"
              >
                <h3
                  className="text-sm font-semibold text-slate-700 dark:text-slate-200
                  flex items-center gap-2 mb-3"
                >
                  <Cpu size={15} className="text-blue-500" />
                  Extracted information
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { label: "Incident Type", value: analysis.incident_type },
                    { label: "Application", value: analysis.application },
                    { label: "Table", value: analysis.table || "—" },
                    {
                      label: "Severity",
                      value: analysis.severity,
                      isBadge: true,
                    },
                    {
                      label: "Probable Team",
                      value: analysis.probable_team,
                      colSpan: true,
                    },
                  ].map(({ label, value, isBadge, colSpan }) => (
                    <div
                      key={label}
                      className={`bg-slate-50 dark:bg-slate-800 rounded-lg px-3 py-2
                        ${colSpan ? "col-span-2" : ""}`}
                    >
                      <div className="text-xs text-slate-400 dark:text-slate-500 mb-0.5">
                        {label}
                      </div>
                      {isBadge ? (
                        <StatusBadge type="severity" value={value} size="md" />
                      ) : (
                        <div
                          className="text-xs font-medium text-slate-700
                            dark:text-slate-200"
                        >
                          {value}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Layer 3 — Knowledge sources */}
              <KnowledgeSourcesCard sources={analysis.knowledge_sources} />

              {/* Layer 4 — Problem & cause */}
              <div
                className="bg-white dark:bg-slate-900 border border-slate-200
                dark:border-slate-700 rounded-xl p-4 shadow-sm shrink-0"
              >
                <h3
                  className="text-sm font-semibold text-slate-700 dark:text-slate-200
                  flex items-center gap-2 mb-3"
                >
                  <ShieldAlert size={15} className="text-amber-500" />
                  Problem &amp; cause
                  {analysis.confidence && (
                    <span
                      className={`ml-auto text-xs font-medium px-2 py-0.5 rounded-full ${
                        analysis.confidence >= 0.85
                          ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400"
                          : analysis.confidence >= 0.65
                            ? "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400"
                            : "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400"
                      }`}
                    >
                      {Math.round(analysis.confidence * 100)}% confident
                    </span>
                  )}
                </h3>
                <div className="space-y-3">
                  <div>
                    <div
                      className="text-xs font-semibold text-slate-500 dark:text-slate-400
                      uppercase tracking-wider mb-1"
                    >
                      Problem identified
                    </div>
                    <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed">
                      {analysis.problem_summary}
                    </p>
                  </div>
                  <div className="border-t border-slate-100 dark:border-slate-800 pt-3">
                    <div
                      className="text-xs font-semibold text-slate-500 dark:text-slate-400
                      uppercase tracking-wider mb-1"
                    >
                      Probable cause
                    </div>
                    <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed">
                      {analysis.probable_cause}
                    </p>
                  </div>
                  <div className="flex gap-2 pt-1">
                    <span
                      className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                        analysis.can_auto_resolve
                          ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400"
                          : "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400"
                      }`}
                    >
                      {analysis.can_auto_resolve
                        ? "✓ Can auto-resolve"
                        : "✗ Manual action required"}
                    </span>
                    {analysis.needs_approval && (
                      <span
                        className="text-xs px-2.5 py-1 rounded-full font-medium
                        bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400"
                      >
                        Approval needed
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Layer 6 — Recommended actions */}
              <div
                className="bg-white dark:bg-slate-900 border border-slate-200
                dark:border-slate-700 rounded-xl p-4 shadow-sm shrink-0"
              >
                <h3
                  className="text-sm font-semibold text-slate-700 dark:text-slate-200
                  flex items-center gap-2 mb-3"
                >
                  <CheckCircle size={15} className="text-emerald-500" />
                  Recommended actions
                </h3>
                <ol className="space-y-2.5">
                  {analysis.recommended_actions.map((action, idx) => (
                    <li
                      key={idx}
                      className="flex items-start gap-3 text-sm
                      text-slate-700 dark:text-slate-200"
                    >
                      <span
                        className="flex-shrink-0 w-5 h-5 rounded-full
                        bg-blue-100 dark:bg-blue-900/30
                        text-blue-600 dark:text-blue-400
                        text-xs font-semibold flex items-center justify-center mt-0.5"
                      >
                        {idx + 1}
                      </span>
                      {action}
                    </li>
                  ))}
                </ol>
              </div>

              {/* Escalation */}
              <div
                className="bg-amber-50 dark:bg-amber-900/10 border border-amber-200
                dark:border-amber-800 rounded-xl p-4 shrink-0"
              >
                <div className="flex items-center gap-2 mb-1">
                  <Users
                    size={15}
                    className="text-amber-600 dark:text-amber-400"
                  />
                  <span className="text-sm font-semibold text-amber-700 dark:text-amber-300">
                    Escalation team
                  </span>
                </div>
                <p className="text-sm text-amber-700 dark:text-amber-300">
                  {analysis.escalation_team}
                </p>
              </div>

              {/* Resolution path */}
              {analysis.resolution_path && (
                <div
                  className="bg-slate-50 dark:bg-slate-800/50 border border-slate-200
                  dark:border-slate-700 rounded-xl p-4 shrink-0"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Clock
                      size={15}
                      className="text-slate-500 dark:text-slate-400"
                    />
                    <span className="text-sm font-semibold text-slate-600 dark:text-slate-300">
                      Expected resolution path
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                    {analysis.resolution_path}
                  </p>
                </div>
              )}

              {/* Layer 5 — Action buttons */}
              <div className="grid grid-cols-3 gap-2 shrink-0">
                {[
                  {
                    icon: <FileText size={18} className="text-blue-500" />,
                    label: "Create Child Ticket",
                  },
                  {
                    icon: <ArrowRight size={18} className="text-emerald-500" />,
                    label: "Assign to Team",
                  },
                  {
                    icon: <Send size={18} className="text-amber-500" />,
                    label: "Request Approval",
                  },
                ].map(({ icon, label }) => (
                  <button
                    key={label}
                    className="flex flex-col items-center gap-1.5 px-3 py-3 rounded-xl
                      border border-slate-200 dark:border-slate-700
                      bg-white dark:bg-slate-900
                      hover:bg-slate-50 dark:hover:bg-slate-800
                      text-slate-700 dark:text-slate-200
                      text-xs font-medium transition-all active:scale-95"
                  >
                    {icon}
                    {label}
                  </button>
                ))}
              </div>
            </>
          )}

          {/* Agent logs */}
          {(isAnalysing || logs.length > 0) && (
            <div
              className="shrink-0 flex flex-col"
              style={{ minHeight: "200px" }}
            >
              <h3
                className="text-sm font-semibold text-slate-600 dark:text-slate-300
                flex items-center gap-2 mb-2"
              >
                <Zap size={15} className="text-blue-500" />
                Agent logs
              </h3>
              <TerminalPane
                logs={logs}
                connectionStatus={isAnalysing ? "streaming" : "done"}
              />
            </div>
          )}

          <div className="shrink-0 h-4" />
        </div>
      )}
    </div>
  );
};

export default AIGuidancePanel;

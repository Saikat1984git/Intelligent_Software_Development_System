import React, { useState, useCallback, useMemo } from "react";
import { Bug, RefreshCw, Brain } from "lucide-react";

import IncidentFilterBar from "../components/molecules/IncidentFilterBar";
import IncidentTable from "../components/molecules/IncidentTable";
import AIGuidancePanel from "../components/molecules/AIGuidancePanel";
import useResizablePanel from "../hooks/useResizablePanel";
import { MOCK_INCIDENTS } from "../data/mockIncidents";

/* ============================================================
   BugSupport — thin orchestrator
   Filter logic:
   - search + searchField   → simple text search on selected field
   - conditions             → per-row filter builder with AND/OR
     Each condition has: field, operator, value, logic
     logic connects THIS row to the NEXT row (AND/OR)
     Last row's logic is ignored.
   ============================================================ */

/* Apply a single operator to a field value */
const applyOperator = (incValue, operator, condValue) => {
  const a = (incValue || "").toLowerCase();
  const b = (condValue || "").toLowerCase();
  switch (operator) {
    case "is":
      return a === b;
    case "is not":
      return a !== b;
    case "contains":
      return a.includes(b);
    case "starts with":
      return a.startsWith(b);
    default:
      return true;
  }
};

/* Evaluate all conditions against one incident */
const matchesConditions = (inc, conditions) => {
  const active = conditions.filter((c) => c.value.trim());
  if (!active.length) return true;

  // Evaluate each condition result
  const results = active.map((c) =>
    applyOperator(inc[c.field], c.operator, c.value),
  );

  // Chain results using the logic from each row (connects row N to row N+1)
  // e.g. [true, AND, false, OR, true] → ((true AND false) OR true) → true
  let result = results[0];
  for (let i = 1; i < results.length; i++) {
    const logic = active[i - 1].logic; // logic on previous row connects to this one
    if (logic === "AND") result = result && results[i];
    else result = result || results[i];
  }
  return result;
};

const BugSupport = () => {
  /* ── Search state ── */
  const [search, setSearch] = useState("");
  const [searchField, setSearchField] = useState("all");

  /* ── Filter builder state ── */
  const [conditions, setConditions] = useState([]);
  const [viewMode, setViewMode] = useState("table");

  /* ── Incident + AI state ── */
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [isAnalysing, setIsAnalysing] = useState(false);
  const [analysisStage, setAnalysisStage] = useState(null);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [logs, setLogs] = useState([]);

  const { leftPanelWidth, handleMouseDown, containerRef } = useResizablePanel(
    58,
    35,
    75,
  );

  /* ── Filtering ── */
  const filteredIncidents = useMemo(() => {
    return MOCK_INCIDENTS.filter((inc) => {
      // Search filter
      if (search.trim()) {
        const q = search.toLowerCase();
        if (searchField === "all") {
          const haystack = [
            inc.id,
            inc.affected_user,
            inc.config_item,
            inc.category,
            inc.priority,
            inc.state,
            inc.assignment_group,
            inc.assigned_to,
            inc.queue,
            inc.short_desc,
          ]
            .join(" ")
            .toLowerCase();
          if (!haystack.includes(q)) return false;
        } else {
          const fieldVal = (inc[searchField] || "").toLowerCase();
          if (!fieldVal.includes(q)) return false;
        }
      }

      // Condition builder filter
      return matchesConditions(inc, conditions);
    });
  }, [search, searchField, conditions]);

  /* ── Mock AI analysis ── */
  const handleAnalyse = useCallback((incident) => {
    setIsAnalysing(true);
    setLogs([]);
    setAnalysisStage("understanding");
    setAnalysisProgress(10);

    const steps = [
      {
        stage: "understanding",
        progress: 20,
        delay: 600,
        msg: "Classifying incident type and extracting entities...",
      },
      {
        stage: "understanding",
        progress: 35,
        delay: 1200,
        msg: `Identified: ${incident.category} issue in ${incident.config_item}`,
      },
      {
        stage: "retrieval",
        progress: 50,
        delay: 2000,
        msg: "Searching past incidents and SOP documents...",
      },
      {
        stage: "retrieval",
        progress: 62,
        delay: 2800,
        msg: "Found 3 similar past incidents.",
      },
      {
        stage: "decision",
        progress: 74,
        delay: 3600,
        msg: "Running decision engine — matching root cause patterns...",
      },
      {
        stage: "action",
        progress: 87,
        delay: 4400,
        msg: "Generating recommended actions...",
      },
      {
        stage: "completed",
        progress: 100,
        delay: 5200,
        msg: "Analysis complete. Guidance ready.",
      },
    ];

    steps.forEach(({ stage, progress, delay, msg }) => {
      setTimeout(() => {
        setAnalysisStage(stage);
        setAnalysisProgress(progress);
        setLogs((prev) => [
          ...prev,
          {
            id: Date.now() + Math.random(),
            content: msg,
            timestamp: new Date().toLocaleTimeString(),
            isError: false,
          },
        ]);
        if (stage === "completed") {
          setIsAnalysing(false);
          setSelectedIncident((prev) => ({
            ...prev,
            ai_analysis: {
              incident_type: `${incident.category} Issue`,
              application: incident.config_item,
              table: null,
              severity: incident.priority.startsWith("1")
                ? "Critical"
                : incident.priority.startsWith("2")
                  ? "High"
                  : incident.priority.startsWith("3")
                    ? "Medium"
                    : "Low",
              probable_team: incident.assignment_group,
              problem_summary: `The incident reported by ${incident.affected_user} relates to: ${incident.short_desc.substring(0, 80)}.`,
              probable_cause:
                "Based on similar past incidents and application logs, this appears to be a configuration or data validation issue requiring manual review.",
              recommended_actions: [
                `Review recent changes in ${incident.config_item} related to this incident.`,
                "Check application logs for errors around the reported timeframe.",
                "Verify user permissions and access levels are correctly configured.",
                "Cross-reference with similar resolved tickets in the knowledge base.",
                `Assign to ${incident.assignment_group} for further investigation if the issue persists.`,
              ],
              escalation_team: incident.assignment_group,
              can_auto_resolve: false,
              needs_approval: false,
            },
          }));
        }
      }, delay);
    });
  }, []);

  return (
    <div
      className="h-[calc(100vh)] flex flex-col overflow-hidden
      bg-slate-50 dark:bg-slate-950 font-sans
      text-slate-800 dark:text-slate-200 transition-colors duration-300"
    >
      {/* Header */}
      <header
        className="shrink-0 h-14 bg-white dark:bg-slate-900
        border-b border-slate-100 dark:border-slate-800
        flex items-center justify-between px-6 shadow-sm"
      >
        <h1 className="text-base font-semibold text-slate-700 dark:text-slate-100 flex items-center gap-2">
          <Bug className="text-blue-500" size={18} />
          Bug Support
          <span className="text-xs font-normal text-slate-400 dark:text-slate-500 ml-1">
            AI-Powered Incident Guidance
          </span>
        </h1>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400 dark:text-slate-500">
            {filteredIncidents.length} of {MOCK_INCIDENTS.length} incidents
          </span>
          <button
            title="Refresh"
            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <RefreshCw size={14} className="text-slate-400" />
          </button>
        </div>
      </header>

      {/* Split row */}
      <div className="flex-1 flex min-h-0" ref={containerRef}>
        {/* ── LEFT ── */}
        <div
          style={{ width: `${leftPanelWidth}%`, minWidth: "380px" }}
          className="flex flex-col min-h-0 min-w-0
            border-r border-slate-200 dark:border-slate-800"
        >
          <div className="shrink-0">
            <IncidentFilterBar
              search={search}
              onSearchChange={setSearch}
              searchField={searchField}
              onSearchFieldChange={setSearchField}
              conditions={conditions}
              onConditionsChange={setConditions}
              viewMode={viewMode}
              onViewModeChange={setViewMode}
              onNew={() => {}}
              onRun={() => {}} // filtering is live/reactive, Run is cosmetic for now
            />
          </div>

          <div className="flex-1 min-h-0 overflow-hidden">
            <IncidentTable
              incidents={filteredIncidents}
              selectedId={selectedIncident?.id}
              onSelect={setSelectedIncident}
              viewMode={viewMode}
            />
          </div>
        </div>

        {/* Resize handle */}
        <div
          onMouseDown={handleMouseDown}
          className="w-1.5 shrink-0 bg-slate-200 dark:bg-slate-800
            hover:bg-blue-500 dark:hover:bg-cyan-500
            cursor-col-resize flex items-center justify-center
            transition-all duration-200 z-30 group
            border-l border-r border-slate-200 dark:border-slate-700"
        >
          <div className="h-10 w-0.5 bg-slate-400 dark:bg-slate-600 group-hover:bg-white rounded-full" />
        </div>

        {/* ── RIGHT ── */}
        <div
          className="flex-1 flex flex-col min-h-0 min-w-0
          bg-slate-50 dark:bg-slate-950"
          style={{ minWidth: "300px" }}
        >
          <div
            className="shrink-0 h-10 bg-white dark:bg-slate-900
            border-b border-slate-200 dark:border-slate-800
            flex items-center px-4 gap-2"
          >
            <Brain size={14} className="text-blue-500" />
            <span className="text-xs font-semibold text-slate-600 dark:text-slate-300">
              AI Guidance Panel
            </span>
            {selectedIncident && (
              <span className="ml-auto text-xs font-mono text-blue-500 dark:text-blue-400">
                {selectedIncident.id}
              </span>
            )}
          </div>

          <div className="flex-1 min-h-0 overflow-hidden">
            <AIGuidancePanel
              incident={selectedIncident}
              isAnalysing={isAnalysing}
              analysisStage={analysisStage}
              analysisProgress={analysisProgress}
              logs={logs}
              onAnalyse={handleAnalyse}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default BugSupport;

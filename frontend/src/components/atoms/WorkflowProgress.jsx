import React from 'react';
import {
  CheckCircle2, Brain, FileEdit, Wand2, Save,
  Layout, Code, FileCode, Package, Bug,
  Wrench, Archive, CheckCircle,
} from 'lucide-react';

/* ============================================================
   PRESET STAGE SETS
   ============================================================ */

export const CODEEDIT_STAGES = [
  { id: 'analysis',    label: 'Project Analysis',  icon: Brain        },
  { id: 'selecting',   label: 'Selecting Files',   icon: FileEdit     },
  { id: 'rewriting',   label: 'Rewriting Code',    icon: Wand2        },
  { id: 'applying',    label: 'Applying Changes',  icon: Save         },
  { id: 'completed',   label: 'Completed',          icon: CheckCircle2 },
];

export const CODEGEN_STAGES = [
  { id: 'analysis',     label: 'Requirement Analysis', icon: Brain       },
  { id: 'architecture', label: 'Architecture Planning', icon: Layout      },
  { id: 'generation',   label: 'Code Generation',       icon: Code        },
  { id: 'files',        label: 'File Creation',         icon: FileCode    },
  { id: 'dependencies', label: 'Dependency Setup',      icon: Package     },
  { id: 'completed',    label: 'Completed',             icon: CheckCircle },
];

export const CODEGEN_FULL_STAGES = [
  { id: 'analysis',     label: 'Requirement Analysis', icon: Brain       },
  { id: 'architecture', label: 'Architecture Planning', icon: Layout      },
  { id: 'generation',   label: 'Code Generation',       icon: Code        },
  { id: 'files',        label: 'File Creation',         icon: FileCode    },
  { id: 'dependencies', label: 'Dependency Setup',      icon: Package     },
  { id: 'debugging',    label: 'Debugging & QA',        icon: Bug         },
  { id: 'fixing_bugs',  label: 'Fixing Bugs',           icon: Wrench      },
  { id: 'packaging',    label: 'Packaging',             icon: Archive     },
  { id: 'completed',    label: 'Completed',             icon: CheckCircle },
];

export const BUGSUPPORT_STAGES = [
  { id: 'understanding', label: 'Understanding',       icon: Brain        },
  { id: 'retrieval',     label: 'Knowledge Retrieval', icon: FileCode     },
  { id: 'decision',      label: 'Decision Engine',     icon: Wand2        },
  { id: 'action',        label: 'Action Layer',        icon: Save         },
  { id: 'completed',     label: 'Guidance Ready',      icon: CheckCircle2 },
];

/* ============================================================
   WorkflowProgress

   FIX — issue 2: when currentStage is null (page just loaded,
   no job running) ALL pills render neutral/idle — no blue
   colour, no pulse. Active styling only begins once a real
   stage id arrives from the page.
   ============================================================ */

const WorkflowProgress = ({
  currentStage   = null,
  progress       = 0,
  stages         = CODEGEN_STAGES,
  isDebugMode    = false,
  debugIteration = 0,
  bugsFound      = 0,
  bugsFixed      = 0,
}) => {
  // -1 = not started, nothing highlighted
  const currentIndex = currentStage
    ? stages.findIndex(s => s.id === currentStage)
    : -1;

  const isStarted = currentIndex !== -1;

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 shadow-sm">

      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">
            Workflow Progress
          </span>
          {isDebugMode && debugIteration > 0 && (
            <span className="px-2 py-0.5 text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded-full">
              Debug Round {debugIteration}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {isDebugMode && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-red-600 dark:text-red-400">🐛 {bugsFound}</span>
              <span className="text-emerald-600 dark:text-emerald-400">✓ {bugsFixed}</span>
            </div>
          )}
          <span className="text-xs font-medium text-slate-400 dark:text-slate-500">
            {isStarted ? `${Math.round(progress)}%` : 'Idle'}
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="relative h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden mb-4">
        <div
          className={`absolute inset-y-0 left-0 rounded-full transition-all duration-500 ${
            !isStarted
              ? ''
              : isDebugMode
                ? 'bg-gradient-to-r from-amber-500 to-orange-500'
                : 'bg-gradient-to-r from-blue-500 to-cyan-500'
          }`}
          style={{ width: isStarted ? `${progress}%` : '0%' }}
        />
      </div>

      {/* Stage pills */}
      <div className="flex flex-wrap gap-1">
        {stages.map((stage, idx) => {
          const Icon        = stage.icon;
          const isActive    = isStarted && idx === currentIndex;
          const isCompleted = isStarted && idx < currentIndex;

          return (
            <div
              key={stage.id}
              className={`
                flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium
                transition-all duration-300
                ${isCompleted
                  ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                  : isActive
                    ? isDebugMode
                      ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
                      : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500'
                }
              `}
            >
              <Icon size={12} className={isActive ? 'animate-pulse' : ''} />
              <span className="hidden sm:inline">{stage.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default WorkflowProgress;

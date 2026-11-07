"use client";

import { LessonSummary } from "@/lib/api";
import { formatDate } from "@/lib/utils";

const STATUS_CONFIG: Record<string, { dot: string; label: string }> = {
  complete: { dot: "bg-green-500", label: "Complete" },
  qc_failed: { dot: "bg-yellow-500", label: "QC Notice" },
  lesson_done: { dot: "bg-blue-400", label: "Drafted" },
  generating: { dot: "bg-indigo-500 animate-pulse", label: "Generating…" },
  research_failed: { dot: "bg-red-500", label: "Research Failed" },
  lesson_failed: { dot: "bg-red-500", label: "Draft Failed" },
};

interface Props {
  lessons: LessonSummary[];
  activeLessonId?: string;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export default function LessonList({
  lessons,
  activeLessonId,
  onSelect,
  onDelete,
}: Props) {
  if (lessons.length === 0) {
    return (
      <div className="text-center py-8 px-4 rounded-xl border border-dashed border-gray-200 text-xs text-gray-400">
        No lessons saved yet. Create a new lesson above.
      </div>
    );
  }

  return (
    <ul className="space-y-1.5">
      {lessons.map((l) => {
        const config = STATUS_CONFIG[l.status] || { dot: "bg-gray-400", label: l.status };
        const active = l.id === activeLessonId;
        return (
          <li key={l.id}>
            <div
              onClick={() => onSelect(l.id)}
              className={`w-full text-left rounded-xl p-3 border transition cursor-pointer group relative ${
                active
                  ? "border-indigo-300 bg-indigo-50/70 shadow-sm"
                  : "border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50/80 shadow-xs"
              }`}
            >
              <div className="flex items-start gap-2.5">
                <span
                  className={`mt-1.5 h-2 w-2 rounded-full flex-shrink-0 ${config.dot}`}
                  title={config.label}
                />
                <div className="flex-1 min-w-0">
                  <p
                    className={`text-xs font-bold truncate ${
                      active ? "text-indigo-950" : "text-gray-800"
                    }`}
                  >
                    {l.title}
                  </p>
                  <p className="text-[11px] text-gray-500 mt-0.5 line-clamp-1 leading-relaxed">
                    {l.objective}
                  </p>
                  <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
                    <span className="text-[10px] text-gray-400">
                      {formatDate(l.updated_at)}
                    </span>
                    {l.has_qc && (
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-green-50 text-green-700 font-medium border border-green-200">
                        Dual QC ✓
                      </span>
                    )}
                    {l.generation_mode === "demo" && (
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-50 text-amber-700 font-medium border border-amber-200">
                        Demo
                      </span>
                    )}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(l.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-600 text-xs p-1 rounded hover:bg-red-50 transition flex-shrink-0"
                  title="Delete lesson"
                >
                  ✕
                </button>
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

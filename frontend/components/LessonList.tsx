"use client";

import { LessonSummary } from "@/lib/api";
import { formatDate } from "@/lib/utils";

const STATUS_DOT: Record<string, string> = {
  complete: "bg-green-500",
  qc_failed: "bg-yellow-500",
  lesson_done: "bg-blue-400",
  generating: "bg-indigo-400 animate-pulse",
  research_failed: "bg-red-500",
  lesson_failed: "bg-red-500",
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
      <div className="text-center py-8 text-xs text-gray-400">
        No lessons yet. Generate one above.
      </div>
    );
  }

  return (
    <ul className="space-y-1.5">
      {lessons.map((l) => {
        const dot = STATUS_DOT[l.status] || "bg-gray-400";
        const active = l.id === activeLessonId;
        return (
          <li key={l.id}>
            <button
              onClick={() => onSelect(l.id)}
              className={`w-full text-left rounded-xl p-3 border transition group ${
                active
                  ? "border-indigo-200 bg-indigo-50"
                  : "border-gray-100 bg-white hover:border-gray-200 hover:bg-gray-50"
              }`}
            >
              <div className="flex items-start gap-2">
                <span className={`mt-1.5 h-2 w-2 rounded-full flex-shrink-0 ${dot}`} />
                <div className="flex-1 min-w-0">
                  <p
                    className={`text-xs font-semibold truncate ${
                      active ? "text-indigo-800" : "text-gray-800"
                    }`}
                  >
                    {l.title}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5 line-clamp-2 leading-relaxed">
                    {l.objective}
                  </p>
                  <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                    {l.has_qc && (
                      <span className="text-xs text-green-600 font-medium">QC✓</span>
                    )}
                    {l.generation_mode === "demo" && (
                      <span className="text-xs text-amber-500">demo</span>
                    )}
                    <span className="text-xs text-gray-300">
                      {formatDate(l.updated_at)}
                    </span>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(l.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 text-xs px-1 transition flex-shrink-0"
                  title="Delete lesson"
                >
                  ✕
                </button>
              </div>
            </button>
          </li>
        );
      })}
    </ul>
  );
}


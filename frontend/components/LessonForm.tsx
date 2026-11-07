"use client";

import { useState } from "react";
import { SAMPLE_LESSONS } from "@/lib/utils";

interface Props {
  onSubmit: (title: string, objective: string) => void;
  loading: boolean;
}

export default function LessonForm({ onSubmit, loading }: Props) {
  const [title, setTitle] = useState("");
  const [objective, setObjective] = useState("");
  const [errors, setErrors] = useState<{ title?: string; objective?: string }>({});

  function validate() {
    const e: typeof errors = {};
    const trimmedTitle = title.trim();
    const trimmedObjective = objective.trim();

    if (!trimmedTitle) {
      e.title = "Lesson title is required.";
    } else if (trimmedTitle.length < 5) {
      e.title = "Title must be at least 5 characters long.";
    }

    if (!trimmedObjective) {
      e.objective = "Learning objective is required.";
    } else if (trimmedObjective.length < 10) {
      e.objective = "Learning objective must be at least 10 characters long.";
    }

    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (validate()) {
      onSubmit(title.trim(), objective.trim());
    }
  }

  function loadSample(s: { title: string; objective: string }) {
    setTitle(s.title);
    setObjective(s.objective);
    setErrors({});
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-4 space-y-4">
      <div>
        <h2 className="text-sm font-bold text-gray-900">Create New Lesson</h2>
        <p className="text-xs text-gray-500 mt-0.5">
          Researches sources, drafts a 45-min lesson, and runs dual quality checks.
        </p>
      </div>

      {/* Quick Example Loaders */}
      <div>
        <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
          Quick Demonstration Examples
        </p>
        <div className="flex flex-col gap-1.5">
          {SAMPLE_LESSONS.map((s, idx) => (
            <button
              key={s.title}
              type="button"
              onClick={() => loadSample(s)}
              className="text-left text-xs p-2 rounded-xl border border-indigo-100 bg-indigo-50/60 hover:bg-indigo-100 text-indigo-900 transition flex items-start gap-1.5 group"
            >
              <span className="text-indigo-500 font-bold text-[11px] mt-0.5">#{idx + 1}</span>
              <div className="min-w-0">
                <p className="font-semibold truncate group-hover:text-indigo-800">{s.title}</p>
                <p className="text-[11px] text-gray-500 line-clamp-1">{s.objective}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3" noValidate>
        <div>
          <label className="block text-xs font-semibold text-gray-700 mb-1">
            Lesson Title <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => {
              setTitle(e.target.value);
              if (errors.title) setErrors((v) => ({ ...v, title: undefined }));
            }}
            placeholder="e.g. HTTP Requests and Responses"
            className={`w-full rounded-xl border px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm ${
              errors.title ? "border-red-400 bg-red-50/20" : "border-gray-300"
            }`}
            disabled={loading}
          />
          {errors.title && <p className="mt-1 text-[11px] text-red-600 font-medium">{errors.title}</p>}
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-700 mb-1">
            Learning Objective <span className="text-red-500">*</span>
          </label>
          <textarea
            value={objective}
            onChange={(e) => {
              setObjective(e.target.value);
              if (errors.objective) setErrors((v) => ({ ...v, objective: undefined }));
            }}
            placeholder="e.g. Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories."
            rows={3}
            className={`w-full rounded-xl border px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm resize-none ${
              errors.objective ? "border-red-400 bg-red-50/20" : "border-gray-300"
            }`}
            disabled={loading}
          />
          {errors.objective && (
            <p className="mt-1 text-[11px] text-red-600 font-medium">{errors.objective}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 rounded-xl bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-2 shadow-sm"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              <span>Generating Lesson…</span>
            </>
          ) : (
            <span>✨ Generate 45-Min Lesson</span>
          )}
        </button>
      </form>
    </div>
  );
}

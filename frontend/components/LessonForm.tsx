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
    if (!title.trim()) e.title = "Title is required.";
    else if (title.trim().length < 5) e.title = "Title must be at least 5 characters.";
    if (!objective.trim()) e.objective = "Learning objective is required.";
    else if (objective.trim().length < 5) e.objective = "Objective must be at least 5 characters.";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (validate()) onSubmit(title.trim(), objective.trim());
  }

  function loadSample(s: { title: string; objective: string }) {
    setTitle(s.title);
    setObjective(s.objective);
    setErrors({});
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
      <h2 className="text-base font-semibold text-gray-900 mb-1">New Lesson</h2>
      <p className="text-xs text-gray-500 mb-4">
        Enter a title and objective to generate a 45-min AI-powered lesson.
      </p>

      <div className="mb-4">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1.5">
          Quick examples
        </p>
        <div className="flex flex-col gap-1.5">
          {SAMPLE_LESSONS.map((s) => (
            <button
              key={s.title}
              onClick={() => loadSample(s)}
              className="text-xs px-2.5 py-1.5 rounded-lg border border-indigo-200 text-indigo-700 bg-indigo-50 hover:bg-indigo-100 transition text-left"
            >
              {s.title}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3" noValidate>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Lesson Title <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => {
              setTitle(e.target.value);
              setErrors((v) => ({ ...v, title: undefined }));
            }}
            placeholder="e.g. HTTP Requests and Responses"
            className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
              errors.title ? "border-red-400" : "border-gray-300"
            }`}
            disabled={loading}
          />
          {errors.title && <p className="mt-1 text-xs text-red-500">{errors.title}</p>}
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Learning Objective <span className="text-red-500">*</span>
          </label>
          <textarea
            value={objective}
            onChange={(e) => {
              setObjective(e.target.value);
              setErrors((v) => ({ ...v, objective: undefined }));
            }}
            placeholder="e.g. Explain GET and POST and distinguish 2xx, 4xx, 5xx status codes."
            rows={3}
            className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none ${
              errors.objective ? "border-red-400" : "border-gray-300"
            }`}
            disabled={loading}
          />
          {errors.objective && (
            <p className="mt-1 text-xs text-red-500">{errors.objective}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Generating…
            </>
          ) : (
            "✨ Generate Lesson"
          )}
        </button>
      </form>
    </div>
  );
}


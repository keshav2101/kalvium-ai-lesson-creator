"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Lesson } from "@/lib/api";

interface Props {
  lesson: Lesson;
  onSave: (content: string) => Promise<void>;
  onResetEdits?: () => Promise<void>;
}

export default function LessonEditor({ lesson, onSave, onResetEdits }: Props) {
  const activeContent = lesson.content_edited ?? lesson.content ?? "";
  const [draft, setDraft] = useState(activeContent);
  const [mode, setMode] = useState<"preview" | "edit">("preview");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [resetting, setResetting] = useState(false);

  // Sync draft when switching lessons or when activeContent updates externally
  useEffect(() => {
    setDraft(activeContent);
    setSaved(false);
  }, [lesson.id, activeContent]);

  const isDirty = draft !== activeContent;
  const isEdited = Boolean(lesson.content_edited);
  const isDemo = lesson.generation_mode === "demo";

  async function handleSave() {
    setSaving(true);
    setSaved(false);
    try {
      await onSave(draft);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } finally {
      setSaving(false);
    }
  }

  async function handleReset() {
    if (!onResetEdits) return;
    if (!confirm("Discard all manual edits and restore the original AI-generated draft?")) return;
    setResetting(true);
    try {
      await onResetEdits();
    } finally {
      setResetting(false);
    }
  }

  return (
    <div className="space-y-3">
      {/* Status Badges */}
      <div className="flex items-center gap-2 flex-wrap">
        {isDemo && (
          <span className="text-xs px-2.5 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-700 font-medium">
            ⚠️ Demo Content (No live AI key configured)
          </span>
        )}
        {isEdited ? (
          <span className="text-xs px-2.5 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 font-medium flex items-center gap-1">
            <span>✏️</span> Manually Edited by Instructor
          </span>
        ) : (
          <span className="text-xs px-2.5 py-1 rounded-full bg-gray-50 border border-gray-200 text-gray-600 font-medium">
            📄 Original Generated Draft
          </span>
        )}
        {isDirty && (
          <span className="text-xs px-2.5 py-1 rounded-full bg-yellow-50 border border-yellow-200 text-yellow-700 font-medium animate-pulse">
            Unsaved Changes
          </span>
        )}
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-2 flex-wrap no-print">
        <div className="flex rounded-lg border border-gray-200 overflow-hidden bg-white shadow-sm">
          <button
            type="button"
            onClick={() => setMode("preview")}
            className={`px-3.5 py-1.5 text-xs font-medium transition ${
              mode === "preview"
                ? "bg-indigo-600 text-white"
                : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            👁️ Preview
          </button>
          <button
            type="button"
            onClick={() => setMode("edit")}
            className={`px-3.5 py-1.5 text-xs font-medium transition ${
              mode === "edit"
                ? "bg-indigo-600 text-white"
                : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            ✏️ Edit Markdown
          </button>
        </div>

        {isEdited && onResetEdits && (
          <button
            type="button"
            onClick={handleReset}
            disabled={resetting}
            className="text-xs px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-red-50 hover:text-red-700 hover:border-red-200 transition"
            title="Restore original AI draft"
          >
            {resetting ? "Resetting…" : "↺ Revert to AI Draft"}
          </button>
        )}

        <div className="ml-auto flex items-center gap-2">
          {saved && <span className="text-xs text-green-600 font-medium">✓ Saved to disk</span>}
          <button
            type="button"
            onClick={handleSave}
            disabled={saving || !isDirty}
            className="px-4 py-1.5 rounded-lg bg-green-600 text-white text-xs font-medium hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed transition shadow-sm"
          >
            {saving ? "Saving…" : "Save Changes"}
          </button>
        </div>
      </div>

      {/* Content Area */}
      {mode === "edit" ? (
        <div className="space-y-1">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            className="w-full min-h-[550px] rounded-xl border border-gray-300 p-4 text-sm font-mono text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm leading-relaxed"
            placeholder="Edit lesson content in Markdown format…"
          />
          <p className="text-xs text-gray-400">
            Tip: Use standard Markdown headings (`##`, `###`), tables, and lists. Edits are preserved across refreshes.
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-gray-200 p-6 min-h-[450px] bg-white shadow-sm">
          <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-headings:font-bold prose-a:text-indigo-600 prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-gray-900 prose-pre:text-gray-100 prose-table:text-sm">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{draft}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Lesson } from "@/lib/api";

interface Props {
  lesson: Lesson;
  onSave: (content: string) => Promise<void>;
}

export default function LessonEditor({ lesson, onSave }: Props) {
  const activeContent = lesson.content_edited ?? lesson.content ?? "";
  const [draft, setDraft] = useState(activeContent);
  const [mode, setMode] = useState<"edit" | "preview">("preview");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Update draft when lesson changes (e.g. switching between lessons)
  const isDirty = draft !== activeContent;
  const isEdited = !!lesson.content_edited;
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

  return (
    <div className="space-y-3">
      {/* Status badges */}
      <div className="flex items-center gap-2 flex-wrap">
        {isDemo && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-amber-50 border border-amber-200 text-amber-700 font-medium">
            ⚠️ Demo Content
          </span>
        )}
        {isEdited && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 font-medium">
            ✏️ Manually Edited
          </span>
        )}
        {isDirty && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-50 border border-yellow-200 text-yellow-700 font-medium">
            Unsaved changes
          </span>
        )}
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-2 no-print">
        <div className="flex rounded-lg border border-gray-200 overflow-hidden">
          <button
            onClick={() => setMode("preview")}
            className={`px-3 py-1.5 text-xs font-medium transition ${
              mode === "preview"
                ? "bg-indigo-600 text-white"
                : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            Preview
          </button>
          <button
            onClick={() => setMode("edit")}
            className={`px-3 py-1.5 text-xs font-medium transition ${
              mode === "edit"
                ? "bg-indigo-600 text-white"
                : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            Edit Markdown
          </button>
        </div>
        <button
          onClick={handleSave}
          disabled={saving || !isDirty}
          className="ml-auto px-4 py-1.5 rounded-lg bg-green-600 text-white text-xs font-medium hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
        >
          {saving ? "Saving…" : saved ? "✓ Saved!" : "Save"}
        </button>
      </div>

      {/* Content */}
      {mode === "edit" ? (
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          className="w-full min-h-[500px] rounded-xl border border-gray-200 p-4 text-sm font-mono text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-y"
          placeholder="Lesson Markdown content…"
        />
      ) : (
        <div className="rounded-xl border border-gray-200 p-6 min-h-[400px] bg-white">
          <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-a:text-indigo-600 prose-code:bg-gray-100 prose-code:px-1 prose-code:rounded prose-pre:bg-gray-900 prose-pre:text-gray-100 prose-table:text-sm">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{draft}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}


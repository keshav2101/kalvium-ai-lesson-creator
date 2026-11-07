"use client";

import { Research, Source } from "@/lib/api";

function SourceCard({ source }: { source: Source }) {
  const typeColors: Record<string, string> = {
    "YouTube Video": "bg-red-50 text-red-700 border-red-200",
    "Documentation / Reference": "bg-blue-50 text-blue-700 border-blue-200",
    Book: "bg-purple-50 text-purple-700 border-purple-200",
    Website: "bg-green-50 text-green-700 border-green-200",
  };
  const badge = typeColors[source.type] || "bg-gray-50 text-gray-700 border-gray-200";

  return (
    <div className="p-4 rounded-xl border border-gray-100 bg-gray-50 hover:border-indigo-200 transition">
      <div className="flex items-start justify-between gap-2 mb-1">
        <a
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-medium text-indigo-700 hover:underline leading-snug"
        >
          {source.title}
        </a>
        <span
          className={`text-xs px-2 py-0.5 rounded-full border flex-shrink-0 ${badge}`}
        >
          {source.type}
        </span>
      </div>
      <p className="text-xs text-gray-500 leading-relaxed">{source.relevance_note}</p>
      <p className="mt-1.5 text-xs text-gray-400 truncate">{source.url}</p>
    </div>
  );
}

interface Props {
  research: Research;
}

export default function ResearchPanel({ research }: Props) {
  const isDemo = research.mode === "demo";

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <span
          className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
            isDemo
              ? "bg-amber-50 text-amber-700 border-amber-200"
              : "bg-green-50 text-green-700 border-green-200"
          }`}
        >
          {isDemo ? "⚠️ DEMO MODE" : "🌐 LIVE SEARCH"}
        </span>
        <span className="text-sm text-gray-500">
          {research.sources.length} sources
        </span>
      </div>

      {research.notice && (
        <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-800">
          {research.notice}
        </div>
      )}

      {research.errors.length > 0 && (
        <div className="p-3 rounded-lg bg-orange-50 border border-orange-200 text-xs text-orange-700 space-y-1">
          {research.errors.map((e, i) => (
            <p key={i}>⚠ {e}</p>
          ))}
        </div>
      )}

      <div className="space-y-3">
        {research.sources.map((s, i) => (
          <SourceCard key={i} source={s} />
        ))}
      </div>
    </div>
  );
}


"use client";

import { Research, Source } from "@/lib/api";

function SourceCard({ source }: { source: Source }) {
  const typeColors: Record<string, string> = {
    "YouTube Video": "bg-red-50 text-red-700 border-red-200",
    "Documentation / Reference": "bg-blue-50 text-blue-700 border-blue-200",
    Book: "bg-purple-50 text-purple-700 border-purple-200",
    Website: "bg-emerald-50 text-emerald-700 border-emerald-200",
  };
  const typeIcons: Record<string, string> = {
    "YouTube Video": "🎥",
    "Documentation / Reference": "📖",
    Book: "📚",
    Website: "🌐",
  };
  const badge = typeColors[source.type] || "bg-gray-50 text-gray-700 border-gray-200";
  const icon = typeIcons[source.type] || "🔗";

  return (
    <div className="p-4 rounded-xl border border-gray-200 bg-white hover:border-indigo-300 transition shadow-sm space-y-2">
      <div className="flex items-start justify-between gap-2">
        <a
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-semibold text-indigo-700 hover:text-indigo-900 hover:underline leading-snug flex items-center gap-1.5"
        >
          <span>{icon}</span>
          <span>{source.title}</span>
        </a>
        <span className={`text-[11px] px-2.5 py-0.5 rounded-full border font-medium flex-shrink-0 ${badge}`}>
          {source.type}
        </span>
      </div>
      <p className="text-xs text-gray-600 leading-relaxed">{source.relevance_note}</p>
      <div className="pt-1 border-t border-gray-100 flex items-center justify-between text-[11px] text-gray-400">
        <span className="truncate max-w-[80%]">{source.url}</span>
        <a
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-indigo-600 hover:underline flex-shrink-0"
        >
          Open source ↗
        </a>
      </div>
    </div>
  );
}

interface Props {
  research: Research;
  onRerunResearch?: () => void;
  rerunning?: boolean;
}

export default function ResearchPanel({ research, onRerunResearch, rerunning }: Props) {
  const isDemo = research.mode === "demo";

  // Category counts
  const categoryCounts = research.sources.reduce((acc, s) => {
    acc[s.type] = (acc[s.type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="space-y-4">
      {/* Header with Mode & Category breakdown */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
              isDemo
                ? "bg-amber-50 text-amber-700 border-amber-200"
                : "bg-green-50 text-green-700 border-green-200"
            }`}
          >
            {isDemo ? "⚠️ DEMO RESEARCH" : "🌐 LIVE WEB RESEARCH"}
          </span>
          <span className="text-xs text-gray-500 font-medium">
            {research.sources.length} authoritative sources
          </span>
          {Object.entries(categoryCounts).map(([type, count]) => (
            <span key={type} className="text-[11px] bg-gray-100 px-2 py-0.5 rounded-full text-gray-600">
              {type}: {count}
            </span>
          ))}
        </div>

        {onRerunResearch && (
          <button
            type="button"
            onClick={onRerunResearch}
            disabled={rerunning}
            className="text-xs px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 font-medium transition flex items-center gap-1 shadow-sm disabled:opacity-50"
          >
            <span>🔄</span>
            {rerunning ? "Searching…" : "Refresh Sources"}
          </button>
        )}
      </div>

      {research.notice && (
        <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800 leading-relaxed shadow-sm">
          {research.notice}
        </div>
      )}

      {research.errors.length > 0 && (
        <div className="p-3.5 rounded-xl bg-orange-50 border border-orange-200 text-xs text-orange-800 space-y-1">
          <p className="font-semibold text-orange-900 mb-1">Source Research Notices:</p>
          {research.errors.map((e, i) => (
            <p key={i}>• {e}</p>
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

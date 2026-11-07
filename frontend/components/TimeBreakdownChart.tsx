"use client";

import { TimeBreakdown } from "@/lib/api";

const COLORS = [
  "bg-indigo-500",
  "bg-blue-500",
  "bg-green-500",
  "bg-yellow-500",
  "bg-purple-500",
  "bg-pink-500",
  "bg-orange-500",
];

interface Props {
  breakdown: TimeBreakdown[];
  total: number;
}

export default function TimeBreakdownChart({ breakdown, total }: Props) {
  const overBudget = total > 45;
  return (
    <div className="rounded-xl border border-gray-100 p-4 bg-white">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-gray-700">⏱ Time Breakdown</h4>
        <span
          className={`text-xs px-2 py-0.5 rounded-full font-medium ${
            overBudget
              ? "bg-red-50 text-red-700 border border-red-200"
              : "bg-green-50 text-green-700 border border-green-200"
          }`}
        >
          {total} / 45 min
        </span>
      </div>

      <div className="flex h-3 rounded-full overflow-hidden mb-3 bg-gray-100">
        {breakdown.map((s, i) => (
          <div
            key={i}
            className={`${COLORS[i % COLORS.length]} transition-all`}
            style={{ width: `${Math.min((s.minutes / 45) * 100, 100)}%` }}
            title={`${s.section}: ${s.minutes} min`}
          />
        ))}
      </div>

      <div className="space-y-1">
        {breakdown.map((s, i) => (
          <div key={i} className="flex items-center gap-2 text-xs text-gray-600">
            <span
              className={`h-2 w-2 rounded-sm flex-shrink-0 ${COLORS[i % COLORS.length]}`}
            />
            <span className="flex-1 truncate">{s.section}</span>
            <span className="font-medium">{s.minutes} min</span>
          </div>
        ))}
      </div>
    </div>
  );
}


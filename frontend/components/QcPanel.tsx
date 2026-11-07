"use client";

import { useState } from "react";
import { Qc, QcReport, QcRecommendation } from "@/lib/api";
import { STATUS_COLORS, STATUS_ICON, SEVERITY_COLOR, PRIORITY_BADGE } from "@/lib/utils";

function RecommendationItem({
  rec,
  applied,
  onApply,
}: {
  rec: QcRecommendation;
  applied: boolean;
  onApply: (id: string) => void;
}) {
  return (
    <div
      className={`flex items-start gap-3 p-3 rounded-lg border transition ${
        applied ? "bg-green-50 border-green-200" : "bg-gray-50 border-gray-100"
      }`}
    >
      <span
        className={`text-xs px-1.5 py-0.5 rounded font-mono font-bold flex-shrink-0 ${
          PRIORITY_BADGE[rec.priority] || "bg-gray-100 text-gray-600"
        }`}
      >
        {rec.id}
      </span>
      <p className="text-xs text-gray-700 flex-1 leading-relaxed">{rec.text}</p>
      <button
        onClick={() => !applied && onApply(rec.id)}
        className={`text-xs px-2 py-1 rounded flex-shrink-0 font-medium transition ${
          applied
            ? "bg-green-200 text-green-800 cursor-default"
            : "bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200"
        }`}
      >
        {applied ? "✓ Applied" : "Mark Applied"}
      </button>
    </div>
  );
}

function QcReportPanel({
  report,
  appliedRecs,
  onApply,
}: {
  report: QcReport;
  appliedRecs: string[];
  onApply: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(true);
  const statusClass = STATUS_COLORS[report.status] || "text-gray-700 bg-gray-50 border-gray-200";
  const icon = STATUS_ICON[report.status] || "⚪";
  const isDemo = report.mode === "demo";

  return (
    <div className="rounded-xl border border-gray-100 overflow-hidden">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-4 bg-gray-50 hover:bg-gray-100 transition text-left"
      >
        <div className="flex items-center gap-3">
          <span className="text-lg">{icon}</span>
          <div>
            <p className="text-sm font-semibold text-gray-900">
              {report.report_type}
            </p>
            {isDemo && (
              <p className="text-xs text-amber-600">⚠️ Demo QC report</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`text-xs px-2.5 py-1 rounded-full border font-medium ${statusClass}`}
          >
            {report.status.replace(/_/g, " ")}
          </span>
          <span className="text-gray-400 text-sm">{expanded ? "▲" : "▼"}</span>
        </div>
      </button>

      {expanded && (
        <div className="px-5 py-4 space-y-4 bg-white">
          <p className="text-sm text-gray-700 leading-relaxed">{report.summary}</p>

          {report.findings.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Findings ({report.findings.length})
              </h4>
              <div className="space-y-2">
                {report.findings.map((f, i) => (
                  <div
                    key={i}
                    className="text-xs p-3 rounded-lg bg-gray-50 border border-gray-100"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`font-semibold uppercase ${
                          SEVERITY_COLOR[f.severity] || "text-gray-500"
                        }`}
                      >
                        {f.severity}
                      </span>
                      <span className="text-gray-400">·</span>
                      <span className="text-gray-500 italic">{f.location}</span>
                    </div>
                    <p className="text-gray-700">{f.issue}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {report.recommendations.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Recommendations ({report.recommendations.length})
              </h4>
              <div className="space-y-2">
                {report.recommendations.map((r) => (
                  <RecommendationItem
                    key={r.id}
                    rec={r}
                    applied={appliedRecs.includes(r.id)}
                    onApply={onApply}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface Props {
  qc: Qc;
  appliedRecs: string[];
  onApplyRec: (id: string) => void;
}

export default function QcPanel({ qc, appliedRecs, onApplyRec }: Props) {
  return (
    <div className="space-y-4">
      {qc.notice && (
        <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-800">
          {qc.notice}
        </div>
      )}
      {qc.errors && qc.errors.length > 0 && (
        <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700">
          {qc.errors.map((e, i) => (
            <p key={i}>⚠ {e}</p>
          ))}
        </div>
      )}
      {qc.research_qc && (
        <QcReportPanel
          report={qc.research_qc}
          appliedRecs={appliedRecs}
          onApply={onApplyRec}
        />
      )}
      {qc.instructional_qc && (
        <QcReportPanel
          report={qc.instructional_qc}
          appliedRecs={appliedRecs}
          onApply={onApplyRec}
        />
      )}
    </div>
  );
}


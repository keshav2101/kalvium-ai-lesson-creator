"use client";

import { useState } from "react";
import { Qc, QcReport, QcRecommendation } from "@/lib/api";
import { STATUS_COLORS, STATUS_ICON, SEVERITY_COLOR, PRIORITY_BADGE } from "@/lib/utils";

function RecommendationItem({
  rec,
  applied,
  onApply,
  onRevert,
  onMarkAddressed,
}: {
  rec: QcRecommendation;
  applied: boolean;
  onApply: (id: string) => void;
  onRevert: (id: string) => void;
  onMarkAddressed: (id: string) => void;
}) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div
      className={`p-3.5 rounded-xl border transition ${
        applied
          ? "bg-green-50/80 border-green-200"
          : "bg-white border-gray-200 hover:border-gray-300 shadow-sm"
      }`}
    >
      <div className="flex items-start gap-2.5">
        <span
          className={`text-xs px-2 py-0.5 rounded font-mono font-bold flex-shrink-0 ${
            PRIORITY_BADGE[rec.priority] || "bg-gray-100 text-gray-600"
          }`}
        >
          {rec.id}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-xs text-gray-800 font-medium leading-relaxed">{rec.text}</p>
          {rec.target_section && (
            <p className="text-[11px] text-gray-400 mt-1 flex items-center gap-1">
              <span>🎯 Applies to:</span>
              <span className="font-semibold text-gray-600">{rec.target_section}</span>
            </p>
          )}

          {rec.suggested_text && (
            <div className="mt-2">
              <button
                type="button"
                onClick={() => setShowDetails(!showDetails)}
                className="text-[11px] text-indigo-600 hover:underline font-medium flex items-center gap-1"
              >
                <span>{showDetails ? "▼ Hide Suggested Addition" : "▶ View Suggested Markdown Addition"}</span>
              </button>
              {showDetails && (
                <pre className="mt-1.5 p-2.5 rounded-lg bg-gray-50 border border-gray-200 text-[11px] font-mono text-gray-700 whitespace-pre-wrap overflow-x-auto">
                  {rec.suggested_text}
                </pre>
              )}
            </div>
          )}
        </div>

        <div className="flex flex-col sm:flex-row items-end gap-1.5 flex-shrink-0">
          {applied ? (
            <div className="flex items-center gap-1.5">
              <span className="text-xs px-2.5 py-1 rounded-md bg-green-100 text-green-800 font-semibold border border-green-300">
                ✓ Applied
              </span>
              <button
                type="button"
                onClick={() => onRevert(rec.id)}
                className="text-xs px-2 py-1 rounded-md text-red-600 hover:bg-red-50 border border-transparent hover:border-red-200 transition"
                title="Remove this addition from the lesson"
              >
                Undo
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-1.5">
              {rec.suggested_text && (
                <button
                  type="button"
                  onClick={() => onApply(rec.id)}
                  className="text-xs px-3 py-1.5 rounded-lg font-medium bg-indigo-600 text-white hover:bg-indigo-700 transition shadow-sm"
                  title="Surgically insert this recommendation into the targeted section"
                >
                  Apply to Lesson
                </button>
              )}
              <button
                type="button"
                onClick={() => onMarkAddressed(rec.id)}
                className="text-xs px-2.5 py-1.5 rounded-lg font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-200 transition"
                title="Mark this as manually completed without inserting automated text"
              >
                Mark Done
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function QcReportPanel({
  report,
  appliedRecs,
  onApply,
  onRevert,
  onMarkAddressed,
}: {
  report: QcReport;
  appliedRecs: string[];
  onApply: (id: string) => void;
  onRevert: (id: string) => void;
  onMarkAddressed: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(true);
  const statusClass = STATUS_COLORS[report.status] || "text-gray-700 bg-gray-50 border-gray-200";
  const icon = STATUS_ICON[report.status] || "⚪";
  const isDemo = report.mode === "demo";

  return (
    <div className="rounded-2xl border border-gray-200 overflow-hidden bg-white shadow-sm">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-4 bg-gray-50/70 hover:bg-gray-100/70 transition text-left border-b border-gray-100"
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">{icon}</span>
          <div>
            <p className="text-sm font-bold text-gray-900">{report.report_type}</p>
            {isDemo && (
              <p className="text-xs text-amber-600 font-medium">⚠️ Demo Quality Assessment (Internal consistency check)</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-xs px-2.5 py-1 rounded-full border font-semibold ${statusClass}`}>
            {report.status.replace(/_/g, " ")}
          </span>
          <span className="text-gray-400 text-xs">{expanded ? "▲ Hide" : "▼ Expand"}</span>
        </div>
      </button>

      {expanded && (
        <div className="p-5 space-y-5">
          <div className="p-3.5 rounded-xl bg-gray-50 border border-gray-100">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Audit Summary</h4>
            <p className="text-xs text-gray-700 leading-relaxed">{report.summary}</p>
          </div>

          {report.findings.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2.5 flex items-center gap-1.5">
                <span>🔎 Specific Findings</span>
                <span className="text-[11px] bg-gray-100 px-2 py-0.5 rounded-full text-gray-600">
                  {report.findings.length}
                </span>
              </h4>
              <div className="space-y-2">
                {report.findings.map((f, i) => (
                  <div key={i} className="text-xs p-3 rounded-xl bg-white border border-gray-200 shadow-sm">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`font-bold uppercase tracking-wider text-[10px] ${SEVERITY_COLOR[f.severity] || "text-gray-500"}`}>
                        [{f.severity}]
                      </span>
                      <span className="text-gray-300">·</span>
                      <span className="text-gray-500 font-medium italic">{f.location}</span>
                    </div>
                    <p className="text-gray-700 leading-relaxed">{f.issue}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {report.recommendations.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide flex items-center gap-1.5">
                  <span>💡 Actionable Recommendations</span>
                  <span className="text-[11px] bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full font-bold">
                    {report.recommendations.length}
                  </span>
                </h4>
                <span className="text-[11px] text-gray-400">Apply edits safely without overwriting other text</span>
              </div>
              <div className="space-y-2.5">
                {report.recommendations.map((r) => (
                  <RecommendationItem
                    key={r.id}
                    rec={r}
                    applied={appliedRecs.includes(r.id)}
                    onApply={onApply}
                    onRevert={onRevert}
                    onMarkAddressed={onMarkAddressed}
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
  onRevertRec: (id: string) => void;
  onMarkAddressed: (id: string) => void;
  onRerunQc?: () => void;
  rerunning?: boolean;
}

export default function QcPanel({
  qc,
  appliedRecs,
  onApplyRec,
  onRevertRec,
  onMarkAddressed,
  onRerunQc,
  rerunning,
}: Props) {
  return (
    <div className="space-y-5">
      {/* Header bar with Re-run QC action */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 className="text-sm font-bold text-gray-900">Independent Quality Control Reports</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Two separate evaluations: factual research consistency and instructional pedagogy.
          </p>
        </div>
        {onRerunQc && (
          <button
            type="button"
            onClick={onRerunQc}
            disabled={rerunning}
            className="text-xs px-3.5 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 font-medium transition flex items-center gap-1.5 shadow-sm disabled:opacity-50"
          >
            <span>🔄</span>
            {rerunning ? "Evaluating Draft…" : "Re-evaluate Current Draft"}
          </button>
        )}
      </div>

      {qc.notice && (
        <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800 leading-relaxed shadow-sm">
          {qc.notice}
        </div>
      )}

      {qc.errors && qc.errors.length > 0 && (
        <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 space-y-1">
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
          onRevert={onRevertRec}
          onMarkAddressed={onMarkAddressed}
        />
      )}

      {qc.instructional_qc && (
        <QcReportPanel
          report={qc.instructional_qc}
          appliedRecs={appliedRecs}
          onApply={onApplyRec}
          onRevert={onRevertRec}
          onMarkAddressed={onMarkAddressed}
        />
      )}
    </div>
  );
}

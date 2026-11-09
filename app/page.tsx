"use client";

import { useCallback, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api, Lesson, LessonSummary } from "@/lib/api";
import LessonForm from "@/components/LessonForm";
import LessonList from "@/components/LessonList";
import LessonEditor from "@/components/LessonEditor";
import ResearchPanel from "@/components/ResearchPanel";
import QcPanel from "@/components/QcPanel";
import TimeBreakdownChart from "@/components/TimeBreakdownChart";

type Tab = "lesson" | "research" | "qc";

function StatusBanner({
  type,
  children,
}: {
  type: "info" | "error" | "success" | "warn";
  children: React.ReactNode;
}) {
  const styles = {
    info: "bg-indigo-50 border-indigo-200 text-indigo-900",
    error: "bg-red-50 border-red-200 text-red-900",
    success: "bg-green-50 border-green-200 text-green-900",
    warn: "bg-amber-50 border-amber-200 text-amber-900",
  };
  return (
    <div className={`rounded-xl border p-4 text-xs ${styles[type]} shadow-xs leading-relaxed`}>
      {children}
    </div>
  );
}

export default function Home() {
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [activeLesson, setActiveLesson] = useState<Lesson | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("lesson");
  const [generating, setGenerating] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);
  const [lastSubmitted, setLastSubmitted] = useState<{ title: string; objective: string } | null>(null);
  const [genStep, setGenStep] = useState<string | null>(null);
  const [healthInfo, setHealthInfo] = useState<{
    gemini_configured: boolean;
    live_search_configured: boolean;
    mode: string;
  } | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  // Load lessons list
  const refreshList = useCallback(async () => {
    try {
      const list = await api.listLessons();
      setLessons(list);
    } catch {
      // silently ignore list refresh errors
    }
  }, []);

  // Health check
  useEffect(() => {
    api
      .health()
      .then((h) => {
        setHealthInfo(h);
        setBackendError(null);
      })
      .catch(() => {
        setBackendError(
          "Cannot connect to the backend server. Make sure FastAPI is running on port 8000."
        );
      });
    refreshList();
  }, [refreshList]);

  // Select lesson from sidebar
  async function selectLesson(id: string) {
    try {
      const lesson = await api.getLesson(id);
      setActiveLesson(lesson);
      setActiveTab("lesson");
      setGenError(null);
    } catch (e) {
      setGenError(String(e));
    }
  }

  // Delete lesson
  async function deleteLesson(id: string) {
    if (!confirm("Delete this lesson from local storage? This action cannot be undone.")) return;
    await api.deleteLesson(id);
    if (activeLesson?.id === id) setActiveLesson(null);
    refreshList();
  }

  // Generate new lesson
  async function handleGenerate(title: string, objective: string) {
    setGenerating(true);
    setGenError(null);
    setGenStep("research");
    setLastSubmitted({ title, objective });

    try {
      // Hint timers for progressive user feedback
      const timer1 = setTimeout(() => setGenStep("lesson"), 1200);
      const timer2 = setTimeout(() => setGenStep("qc"), 2800);

      const lesson = await api.generate(title, objective);
      clearTimeout(timer1);
      clearTimeout(timer2);
      setGenStep("done");
      setActiveLesson(lesson);
      setActiveTab("lesson");
      await refreshList();
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : typeof err === "object" && err !== null && "message" in err
          ? String((err as { message: unknown }).message)
          : String(err);
      setGenError(msg);
      await refreshList();
    } finally {
      setGenerating(false);
    }
  }

  // Retry generation for last submitted inputs
  async function handleRetryLastSubmitted() {
    if (!lastSubmitted) return;
    await handleGenerate(lastSubmitted.title, lastSubmitted.objective);
  }

  // Retry a step on the current active lesson
  async function handleRetryStep(step: "research" | "lesson" | "qc" | "all" = "all") {
    if (!activeLesson) return;
    setRetrying(true);
    try {
      const updated = await api.retryGenerate(activeLesson.id, step);
      setActiveLesson(updated);
      await refreshList();
    } catch (err: unknown) {
      alert("Retry failed: " + (err instanceof Error ? err.message : String(err)));
    } finally {
      setRetrying(false);
    }
  }

  // Save edited lesson content
  async function handleSaveContent(content: string) {
    if (!activeLesson) return;
    const updated = await api.updateLesson(activeLesson.id, {
      content_edited: content,
    });
    setActiveLesson(updated);
    refreshList();
  }

  // Reset manual edits back to generated draft
  async function handleResetEdits() {
    if (!activeLesson) return;
    const updated = await api.resetEdits(activeLesson.id);
    setActiveLesson(updated);
    refreshList();
  }

  // Apply a QC recommendation surgically
  async function handleApplyRec(recId: string) {
    if (!activeLesson) return;
    const updated = await api.applyRecommendation(activeLesson.id, recId);
    setActiveLesson(updated);
    refreshList();
  }

  // Revert an applied recommendation
  async function handleRevertRec(recId: string) {
    if (!activeLesson) return;
    const updated = await api.revertRecommendation(activeLesson.id, recId);
    setActiveLesson(updated);
    refreshList();
  }

  // Mark recommendation as addressed without automated insertion
  async function handleMarkAddressed(recId: string) {
    if (!activeLesson) return;
    const currentApplied = activeLesson.applied_recommendations || [];
    if (!currentApplied.includes(recId)) {
      const updated = await api.updateLesson(activeLesson.id, {
        applied_recommendations: [...currentApplied, recId],
      });
      setActiveLesson(updated);
    }
  }

  // Export lesson as single Markdown file
  async function handleExport() {
    if (!activeLesson) return;
    setExporting(true);
    try {
      const url = api.exportUrl(activeLesson.id);
      const response = await fetch(url);
      if (!response.ok) throw new Error("Export request failed");
      const blob = await response.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      const filename =
        activeLesson.title
          .toLowerCase()
          .replace(/\s+/g, "_")
          .replace(/[^a-z0-9_]/g, "")
          .slice(0, 50) + ".md";
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(a.href);
    } catch (e) {
      alert("Export failed: " + String(e));
    } finally {
      setExporting(false);
    }
  }

  // Print preview trigger
  function handlePrint() {
    window.print();
  }

  const tabs: { id: Tab; label: string; count?: number }[] = [
    { id: "lesson", label: "📄 Lesson Document" },
    {
      id: "research",
      label: "🔍 Research Sources",
      count: activeLesson?.research?.sources?.length,
    },
    { id: "qc", label: "✅ Quality Checks (Dual QC)" },
  ];

  const currentContent = activeLesson?.content_edited ?? activeLesson?.content ?? "";

  return (
    <div className="min-h-screen flex flex-col bg-gray-50/50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3.5 flex items-center justify-between no-print sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold text-base shadow-xs">
            🎓
          </div>
          <div>
            <h1 className="text-base font-bold text-gray-900 leading-tight">
              AI-Powered Lesson Creation Tool
            </h1>
            <p className="text-[11px] text-gray-500">
              Research · 45-Min Lesson Drafting · Dual QC Audit · Review & Export
            </p>
          </div>
        </div>

        {healthInfo && (
          <div className="flex items-center gap-2 text-xs">
            <span
              className={`px-2.5 py-1 rounded-full border text-[11px] font-semibold ${
                healthInfo.gemini_configured
                  ? "bg-green-50 text-green-700 border-green-200"
                  : "bg-amber-50 text-amber-700 border-amber-200"
              }`}
            >
              AI: {healthInfo.gemini_configured ? "Google Gemini 1.5" : "Demo Mode"}
            </span>
            <span
              className={`px-2.5 py-1 rounded-full border text-[11px] font-semibold ${
                healthInfo.live_search_configured
                  ? "bg-green-50 text-green-700 border-green-200"
                  : "bg-amber-50 text-amber-700 border-amber-200"
              }`}
            >
              Search: {healthInfo.live_search_configured ? "Live Google Search" : "Curated Sources"}
            </span>
          </div>
        )}
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-80 flex-shrink-0 border-r border-gray-200 bg-white flex flex-col overflow-hidden no-print">
          <div className="p-4 border-b border-gray-200 overflow-y-auto">
            {backendError ? (
              <StatusBanner type="error">{backendError}</StatusBanner>
            ) : (
              <LessonForm onSubmit={handleGenerate} loading={generating} />
            )}
          </div>

          {/* Progressive Generation Indicator */}
          {generating && (
            <div className="p-4 border-b border-gray-200 bg-indigo-50/40">
              <div className="text-[11px] font-bold text-indigo-900 uppercase tracking-wider mb-2.5 flex items-center justify-between">
                <span>Generating Workflow</span>
                <span className="text-[10px] text-indigo-600 font-normal">Step-by-step</span>
              </div>
              {["research", "lesson", "qc"].map((step, i) => {
                const stepOrder = ["research", "lesson", "qc"];
                const stepLabels = {
                  research: "1. Researching Sources",
                  lesson: "2. Drafting 45-Min Lesson",
                  qc: "3. Running Dual QC Audits",
                };
                const currentIdx = stepOrder.indexOf(genStep || "");
                const done = i < currentIdx || genStep === "done";
                const active = i === currentIdx && genStep !== "done";
                return (
                  <div key={step} className="flex items-center gap-2 py-1.5">
                    <span
                      className={`h-5 w-5 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0 ${
                        done
                          ? "bg-green-600 text-white"
                          : active
                          ? "bg-indigo-600 text-white animate-pulse"
                          : "bg-gray-200 text-gray-500"
                      }`}
                    >
                      {done ? "✓" : i + 1}
                    </span>
                    <span
                      className={`text-xs ${
                        active
                          ? "text-indigo-900 font-semibold"
                          : done
                          ? "text-gray-700"
                          : "text-gray-400"
                      }`}
                    >
                      {stepLabels[step as keyof typeof stepLabels]}
                    </span>
                  </div>
                );
              })}
            </div>
          )}

          {/* Generation Error Banner with Retry Option */}
          {genError && (
            <div className="p-4 border-b border-gray-200">
              <StatusBanner type="error">
                <p className="font-bold mb-1">Generation Failed</p>
                <p className="text-[11px] leading-relaxed mb-2.5">{genError}</p>
                {lastSubmitted && (
                  <button
                    type="button"
                    onClick={handleRetryLastSubmitted}
                    disabled={generating}
                    className="text-[11px] px-3 py-1.5 rounded-lg bg-red-600 text-white font-semibold hover:bg-red-700 transition"
                  >
                    🔄 Retry Generation
                  </button>
                )}
              </StatusBanner>
            </div>
          )}

          {/* Saved Lessons List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            <div className="flex items-center justify-between mb-1">
              <p className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                Saved Lessons ({lessons.length})
              </p>
              <button
                type="button"
                onClick={refreshList}
                className="text-[11px] text-indigo-600 hover:underline"
              >
                Refresh
              </button>
            </div>
            <LessonList
              lessons={lessons}
              activeLessonId={activeLesson?.id}
              onSelect={selectLesson}
              onDelete={deleteLesson}
            />
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto bg-gray-50/50">
          {!activeLesson && !generating ? (
            <div className="flex items-center justify-center h-full p-8">
              <div className="text-center max-w-md p-8 rounded-2xl bg-white border border-gray-200 shadow-xs space-y-3">
                <div className="text-5xl">📖</div>
                <h2 className="text-base font-bold text-gray-800">
                  Ready to Create or Review a Lesson
                </h2>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Select one of the sample demonstration lessons on the left, or enter a custom title and objective to generate a structured 45-minute lesson with research and QC checks.
                </p>
              </div>
            </div>
          ) : activeLesson ? (
            <div className="p-6 max-w-4xl mx-auto space-y-6">
              {/* Lesson Top Card */}
              <div className="p-5 rounded-2xl bg-white border border-gray-200 shadow-sm space-y-3 no-print">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-xl font-bold text-gray-900 leading-snug">
                      {activeLesson.title}
                    </h2>
                    <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                      <span className="font-semibold text-gray-700">Objective:</span> {activeLesson.objective}
                    </p>
                    <div className="flex items-center gap-2 mt-2.5 flex-wrap">
                      <span
                        className={`text-[11px] px-2.5 py-0.5 rounded-full border font-semibold ${
                          activeLesson.generation_mode === "live"
                            ? "bg-green-50 text-green-700 border-green-200"
                            : "bg-amber-50 text-amber-700 border-amber-200"
                        }`}
                      >
                        {activeLesson.generation_mode === "live"
                          ? "🤖 AI Generated"
                          : "⚠️ Demo Content"}
                      </span>
                      {activeLesson.content_edited ? (
                        <span className="text-[11px] px-2.5 py-0.5 rounded-full border font-semibold bg-blue-50 text-blue-700 border-blue-200">
                          ✏️ Manually Edited
                        </span>
                      ) : (
                        <span className="text-[11px] px-2.5 py-0.5 rounded-full border font-medium bg-gray-50 text-gray-600 border-gray-200">
                          📄 Original AI Draft
                        </span>
                      )}
                      <span
                        className={`text-[11px] px-2.5 py-0.5 rounded-full border font-medium ${
                          activeLesson.status === "complete"
                            ? "bg-green-50 text-green-700 border-green-200"
                            : "bg-gray-50 text-gray-600 border-gray-200"
                        }`}
                      >
                        Status: {activeLesson.status}
                      </span>
                      {activeLesson.applied_recommendations && activeLesson.applied_recommendations.length > 0 && (
                        <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium">
                          {activeLesson.applied_recommendations.length} QC Edits Applied
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex gap-2 flex-shrink-0">
                    <button
                      type="button"
                      onClick={handlePrint}
                      className="px-3.5 py-2 text-xs rounded-xl border border-gray-200 text-gray-700 bg-white hover:bg-gray-50 font-medium transition flex items-center gap-1.5 shadow-xs"
                      title="Print-friendly view / Save to PDF"
                    >
                      <span>🖨️</span>
                      <span>Print / PDF</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleExport}
                      disabled={exporting}
                      className="px-4 py-2 text-xs rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 font-semibold transition flex items-center gap-1.5 shadow-xs disabled:opacity-50"
                      title="Export lesson, references, and QC reports as a single Markdown file"
                    >
                      <span>⬇️</span>
                      <span>{exporting ? "Exporting…" : "Export Markdown"}</span>
                    </button>
                  </div>
                </div>

                {/* Step Failure & Retry Banner */}
                {activeLesson.errors && Object.keys(activeLesson.errors).length > 0 && (
                  <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-xs text-red-900 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold">⚠️ Step Notice: Previous step encountered an issue (last valid state preserved):</span>
                      <button
                        type="button"
                        onClick={() => handleRetryStep("all")}
                        disabled={retrying}
                        className="text-xs px-2.5 py-1 rounded-md bg-red-600 text-white font-semibold hover:bg-red-700 transition"
                      >
                        {retrying ? "Retrying…" : "🔄 Retry All"}
                      </button>
                    </div>
                    <ul className="space-y-1 text-[11px] list-disc list-inside">
                      {Object.entries(activeLesson.errors)
                        .filter(([k]) => !k.endsWith("_trace"))
                        .map(([k, v]) => (
                          <li key={k}>
                            <span className="font-mono font-bold">{k}:</span> {v}
                          </li>
                        ))}
                    </ul>
                  </div>
                )}

                {/* 45-Minute Time Breakdown Visualization */}
                {activeLesson.time_breakdown && activeLesson.time_breakdown.length > 0 && (
                  <div className="pt-2 border-t border-gray-100">
                    <TimeBreakdownChart
                      breakdown={activeLesson.time_breakdown}
                      total={activeLesson.total_minutes ?? 45}
                    />
                  </div>
                )}
              </div>

              {/* Navigation Tabs */}
              <div className="border-b border-gray-200 no-print">
                <div className="flex gap-2">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => setActiveTab(tab.id)}
                      className={`px-4 py-2.5 text-xs font-bold border-b-2 transition flex items-center gap-2 ${
                        activeTab === tab.id
                          ? "border-indigo-600 text-indigo-700 bg-white rounded-t-xl"
                          : "border-transparent text-gray-500 hover:text-gray-700"
                      }`}
                    >
                      <span>{tab.label}</span>
                      {tab.count !== undefined && (
                        <span className="text-[10px] bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full font-semibold">
                          {tab.count}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Screen Tab Panels */}
              <div className="no-print">
                {activeTab === "lesson" && (
                  <LessonEditor
                    key={activeLesson.id}
                    lesson={activeLesson}
                    onSave={handleSaveContent}
                    onResetEdits={handleResetEdits}
                  />
                )}

                {activeTab === "research" && activeLesson.research ? (
                  <ResearchPanel
                    research={activeLesson.research}
                    onRerunResearch={() => handleRetryStep("research")}
                    rerunning={retrying}
                  />
                ) : activeTab === "research" ? (
                  <StatusBanner type="warn">
                    No research sources recorded for this lesson.
                  </StatusBanner>
                ) : null}

                {activeTab === "qc" && activeLesson.qc ? (
                  <QcPanel
                    qc={activeLesson.qc}
                    appliedRecs={activeLesson.applied_recommendations ?? []}
                    onApplyRec={handleApplyRec}
                    onRevertRec={handleRevertRec}
                    onMarkAddressed={handleMarkAddressed}
                    onRerunQc={() => handleRetryStep("qc")}
                    rerunning={retrying}
                  />
                ) : activeTab === "qc" ? (
                  <StatusBanner type="warn">
                    No QC reports available.
                  </StatusBanner>
                ) : null}
              </div>

              {/* Print-Only Layout (Complete Lesson + Sources + Dual QC Reports) */}
              <div className="print-only space-y-8">
                <div className="border-b border-gray-300 pb-4">
                  <h1 className="text-2xl font-bold text-gray-900">{activeLesson.title}</h1>
                  <p className="text-sm text-gray-700 mt-1 font-medium">
                    Learning Objective: {activeLesson.objective}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Exported from AI-Powered Lesson Creation Tool | Mode: {activeLesson.generation_mode.toUpperCase()}
                  </p>
                </div>

                {/* Finalized Lesson Content */}
                <div>
                  <h2 className="text-lg font-bold text-gray-900 mb-3 border-b pb-1">Finalized Lesson Plan (45 Minutes)</h2>
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{currentContent}</ReactMarkdown>
                  </div>
                </div>

                {/* Research Sources Appendix */}
                {activeLesson.research && activeLesson.research.sources.length > 0 && (
                  <div className="page-break-before pt-6 border-t border-gray-300">
                    <h2 className="text-lg font-bold text-gray-900 mb-3 border-b pb-1">📚 Research Sources Appendix</h2>
                    {activeLesson.research.notice && (
                      <p className="text-xs text-gray-500 italic mb-3">{activeLesson.research.notice}</p>
                    )}
                    <ul className="space-y-2 text-xs">
                      {activeLesson.research.sources.map((s, i) => (
                        <li key={i} className="border p-2 rounded">
                          <p className="font-bold">{i + 1}. [{s.type}] {s.title}</p>
                          <p className="text-gray-600">{s.relevance_note}</p>
                          <p className="text-gray-400 font-mono text-[10px]">{s.url}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Dual QC Reports */}
                {activeLesson.qc && (
                  <div className="page-break-before pt-6 border-t border-gray-300 space-y-6">
                    <h2 className="text-lg font-bold text-gray-900 mb-2 border-b pb-1">🔍 Quality Control Reports</h2>

                    {activeLesson.qc.research_qc && (
                      <div className="border p-4 rounded text-xs space-y-2">
                        <h3 className="font-bold text-sm text-gray-900">
                          {activeLesson.qc.research_qc.report_type} — Status: {activeLesson.qc.research_qc.status}
                        </h3>
                        <p className="text-gray-700">{activeLesson.qc.research_qc.summary}</p>
                        {activeLesson.qc.research_qc.findings.length > 0 && (
                          <div>
                            <p className="font-semibold text-gray-800">Findings:</p>
                            <ul className="list-disc list-inside">
                              {activeLesson.qc.research_qc.findings.map((f, i) => (
                                <li key={i}>[{f.severity}] {f.location}: {f.issue}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}

                    {activeLesson.qc.instructional_qc && (
                      <div className="border p-4 rounded text-xs space-y-2">
                        <h3 className="font-bold text-sm text-gray-900">
                          {activeLesson.qc.instructional_qc.report_type} — Status: {activeLesson.qc.instructional_qc.status}
                        </h3>
                        <p className="text-gray-700">{activeLesson.qc.instructional_qc.summary}</p>
                        {activeLesson.qc.instructional_qc.findings.length > 0 && (
                          <div>
                            <p className="font-semibold text-gray-800">Findings:</p>
                            <ul className="list-disc list-inside">
                              {activeLesson.qc.instructional_qc.findings.map((f, i) => (
                                <li key={i}>[{f.severity}] {f.location}: {f.issue}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </main>
      </div>
    </div>
  );
}

"use client";

import { useCallback, useEffect, useState } from "react";
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
    info: "bg-indigo-50 border-indigo-200 text-indigo-800",
    error: "bg-red-50 border-red-200 text-red-800",
    success: "bg-green-50 border-green-200 text-green-800",
    warn: "bg-amber-50 border-amber-200 text-amber-800",
  };
  return (
    <div className={`rounded-xl border p-4 text-sm ${styles[type]}`}>
      {children}
    </div>
  );
}

export default function Home() {
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [activeLesson, setActiveLesson] = useState<Lesson | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("lesson");
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);
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
          "Cannot connect to the backend. Make sure the FastAPI server is running on port 8000."
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
    if (!confirm("Delete this lesson? This cannot be undone.")) return;
    await api.deleteLesson(id);
    if (activeLesson?.id === id) setActiveLesson(null);
    refreshList();
  }

  // Generate new lesson
  async function handleGenerate(title: string, objective: string) {
    setGenerating(true);
    setGenError(null);
    setGenStep("research");
    setActiveLesson(null);

    try {
      // Simulate step progress (the backend does it synchronously, we show steps as hints)
      const timer = setTimeout(() => setGenStep("lesson"), 3000);
      const timer2 = setTimeout(() => setGenStep("qc"), 10000);

      const lesson = await api.generate(title, objective);
      clearTimeout(timer);
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
      // Reload list in case partial lesson was saved
      await refreshList();
    } finally {
      setGenerating(false);
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

  // Apply a QC recommendation
  async function handleApplyRec(recId: string) {
    if (!activeLesson) return;
    const updated = await api.updateLesson(activeLesson.id, {
      applied_recommendations: [recId],
    });
    setActiveLesson(updated);
  }

  // Export lesson
  async function handleExport() {
    if (!activeLesson) return;
    setExporting(true);
    try {
      const url = api.exportUrl(activeLesson.id);
      const response = await fetch(url);
      if (!response.ok) throw new Error("Export failed");
      const blob = await response.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      const filename =
        activeLesson.title.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "").slice(0, 50) + ".md";
      a.download = filename;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (e) {
      alert("Export failed: " + String(e));
    } finally {
      setExporting(false);
    }
  }

  // Print preview
  function handlePrint() {
    window.print();
  }

  const tabs: { id: Tab; label: string; count?: number }[] = [
    { id: "lesson", label: "📄 Lesson" },
    {
      id: "research",
      label: "🔍 Research",
      count: activeLesson?.research?.sources?.length,
    },
    { id: "qc", label: "✅ Quality Checks" },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">
            🎓 Lesson Creation Tool
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            AI-powered · Research + Draft + QC + Export
          </p>
        </div>
        {healthInfo && (
          <div className="flex items-center gap-2 text-xs">
            <span
              className={`px-2 py-1 rounded-full border font-medium ${
                healthInfo.gemini_configured
                  ? "bg-green-50 text-green-700 border-green-200"
                  : "bg-amber-50 text-amber-700 border-amber-200"
              }`}
            >
              AI: {healthInfo.gemini_configured ? "Live" : "Demo"}
            </span>
            <span
              className={`px-2 py-1 rounded-full border font-medium ${
                healthInfo.live_search_configured
                  ? "bg-green-50 text-green-700 border-green-200"
                  : "bg-amber-50 text-amber-700 border-amber-200"
              }`}
            >
              Search: {healthInfo.live_search_configured ? "Live" : "Demo"}
            </span>
          </div>
        )}
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-72 flex-shrink-0 border-r border-gray-100 bg-white flex flex-col overflow-hidden">
          <div className="p-4 border-b border-gray-100 overflow-y-auto">
            {backendError ? (
              <StatusBanner type="error">{backendError}</StatusBanner>
            ) : (
              <LessonForm onSubmit={handleGenerate} loading={generating} />
            )}
          </div>

          {/* Generation progress */}
          {generating && (
            <div className="p-4 border-b border-gray-100">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Generating…
              </div>
              {["research", "lesson", "qc"].map((step, i) => {
                const stepOrder = ["research", "lesson", "qc"];
                const currentIdx = stepOrder.indexOf(genStep || "");
                const done = i < currentIdx || genStep === "done";
                const active = i === currentIdx && genStep !== "done";
                return (
                  <div key={step} className="flex items-center gap-2 py-1">
                    <span
                      className={`h-5 w-5 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                        done
                          ? "bg-green-500 text-white"
                          : active
                          ? "bg-indigo-500 text-white animate-pulse"
                          : "bg-gray-100 text-gray-400"
                      }`}
                    >
                      {done ? "✓" : i + 1}
                    </span>
                    <span
                      className={`text-xs ${active ? "text-indigo-700 font-medium" : done ? "text-gray-600" : "text-gray-300"}`}
                    >
                      {step.charAt(0).toUpperCase() + step.slice(1)}
                    </span>
                    {active && (
                      <svg className="animate-spin h-3 w-3 text-indigo-500 ml-auto" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                      </svg>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {genError && (
            <div className="p-4 border-b border-gray-100">
              <StatusBanner type="error">
                <p className="font-medium mb-1">Generation failed</p>
                <p className="text-xs">{genError}</p>
              </StatusBanner>
            </div>
          )}

          {/* Saved lessons */}
          <div className="flex-1 overflow-y-auto p-4">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Saved Lessons ({lessons.length})
            </p>
            <LessonList
              lessons={lessons}
              activeLessonId={activeLesson?.id}
              onSelect={selectLesson}
              onDelete={deleteLesson}
            />
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto">
          {!activeLesson && !generating ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-sm">
                <div className="text-5xl mb-4">📚</div>
                <h2 className="text-lg font-semibold text-gray-700 mb-2">
                  No lesson selected
                </h2>
                <p className="text-sm text-gray-400">
                  Generate a new lesson using the form on the left, or select a
                  saved lesson from the list.
                </p>
              </div>
            </div>
          ) : activeLesson ? (
            <div className="p-6 max-w-4xl mx-auto space-y-6">
              {/* Lesson header */}
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {activeLesson.title}
                  </h2>
                  <p className="text-sm text-gray-500 mt-1">
                    {activeLesson.objective}
                  </p>
                  <div className="flex items-center gap-2 mt-2 flex-wrap">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full border font-medium ${
                        activeLesson.generation_mode === "live"
                          ? "bg-green-50 text-green-700 border-green-200"
                          : "bg-amber-50 text-amber-700 border-amber-200"
                      }`}
                    >
                      {activeLesson.generation_mode === "live"
                        ? "🤖 AI Generated"
                        : "⚠️ Demo Content"}
                    </span>
                    {activeLesson.content_edited && (
                      <span className="text-xs px-2 py-0.5 rounded-full border font-medium bg-blue-50 text-blue-700 border-blue-200">
                        ✏️ Manually Edited
                      </span>
                    )}
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full border ${
                        activeLesson.status === "complete"
                          ? "bg-green-50 text-green-700 border-green-200"
                          : "bg-gray-50 text-gray-600 border-gray-200"
                      }`}
                    >
                      {activeLesson.status}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2 no-print flex-shrink-0">
                  <button
                    onClick={handlePrint}
                    className="px-3 py-2 text-sm rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition"
                    title="Print preview"
                  >
                    🖨️ Print
                  </button>
                  <button
                    onClick={handleExport}
                    disabled={exporting}
                    className="px-4 py-2 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition font-medium"
                  >
                    {exporting ? "Exporting…" : "⬇️ Export Markdown"}
                  </button>
                </div>
              </div>

              {/* Error banner for failed steps */}
              {activeLesson.errors && Object.keys(activeLesson.errors).length > 0 && (
                <StatusBanner type="error">
                  <p className="font-medium mb-1">Some steps had errors (last successful state preserved):</p>
                  <ul className="text-xs space-y-1 mt-1">
                    {Object.entries(activeLesson.errors)
                      .filter(([k]) => !k.endsWith("_trace"))
                      .map(([k, v]) => (
                        <li key={k}>
                          <span className="font-mono font-semibold">{k}:</span> {v}
                        </li>
                      ))}
                  </ul>
                </StatusBanner>
              )}

              {/* Time breakdown */}
              {activeLesson.time_breakdown && activeLesson.time_breakdown.length > 0 && (
                <TimeBreakdownChart
                  breakdown={activeLesson.time_breakdown}
                  total={activeLesson.total_minutes ?? 45}
                />
              )}

              {/* Tabs */}
              <div className="border-b border-gray-200 no-print">
                <div className="flex gap-1">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`px-4 py-2.5 text-sm font-medium border-b-2 transition ${
                        activeTab === tab.id
                          ? "border-indigo-600 text-indigo-700"
                          : "border-transparent text-gray-500 hover:text-gray-700"
                      }`}
                    >
                      {tab.label}
                      {tab.count !== undefined && (
                        <span className="ml-1.5 text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full">
                          {tab.count}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tab content */}
              <div>
                {activeTab === "lesson" && (
                  <LessonEditor lesson={activeLesson} onSave={handleSaveContent} />
                )}

                {activeTab === "research" && activeLesson.research ? (
                  <ResearchPanel research={activeLesson.research} />
                ) : activeTab === "research" ? (
                  <StatusBanner type="warn">No research data available for this lesson.</StatusBanner>
                ) : null}

                {activeTab === "qc" && activeLesson.qc ? (
                  <QcPanel
                    qc={activeLesson.qc}
                    appliedRecs={activeLesson.applied_recommendations ?? []}
                    onApplyRec={handleApplyRec}
                  />
                ) : activeTab === "qc" ? (
                  <StatusBanner type="warn">
                    No QC reports available. The QC step may have failed — check the errors above.
                  </StatusBanner>
                ) : null}
              </div>
            </div>
          ) : null}
        </main>
      </div>
    </div>
  );
}


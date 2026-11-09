// API client — calls FastAPI backend (supports localhost and production origin)
export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL !== undefined
    ? process.env.NEXT_PUBLIC_API_URL
    : typeof window !== "undefined" && !["localhost", "127.0.0.1"].includes(window.location.hostname)
    ? ""
    : "http://localhost:8000";

export interface Source {
  title: string;
  type: string;
  url: string;
  relevance_note: string;
}

export interface Research {
  mode: "live" | "demo";
  sources: Source[];
  errors: string[];
  notice?: string;
}

export interface TimeBreakdown {
  section: string;
  minutes: number;
}

export interface QcFinding {
  issue: string;
  severity: "low" | "medium" | "high";
  location: string;
}

export interface QcRecommendation {
  id: string;
  text: string;
  priority: "low" | "medium" | "high";
  target_section?: string;
  suggested_text?: string;
}

export interface QcReport {
  report_type: string;
  status: "PASS" | "PASS_WITH_CONCERNS" | "NEEDS_REVISION" | "ERROR";
  summary: string;
  findings: QcFinding[];
  recommendations: QcRecommendation[];
  mode: "live" | "demo" | "error";
}

export interface Qc {
  research_qc?: QcReport;
  instructional_qc?: QcReport;
  errors?: string[];
  notice?: string;
}

export interface Lesson {
  id: string;
  title: string;
  objective: string;
  status: string;
  generation_mode: string;
  content?: string;
  content_edited?: string;
  research?: Research;
  time_breakdown?: TimeBreakdown[];
  total_minutes?: number;
  qc?: Qc;
  errors?: Record<string, string>;
  created_at?: string;
  updated_at?: string;
  applied_recommendations?: string[];
}

export interface LessonSummary {
  id: string;
  title: string;
  objective: string;
  status: string;
  generation_mode: string;
  created_at?: string;
  updated_at?: string;
  has_qc: boolean;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let errorDetail: unknown;
    try {
      errorDetail = await res.json();
    } catch {
      errorDetail = await res.text();
    }

    let msg = "An unexpected error occurred.";
    if (typeof errorDetail === "string") {
      msg = errorDetail;
    } else if (typeof errorDetail === "object" && errorDetail !== null) {
      const errObj = errorDetail as Record<string, unknown>;
      // Check FastAPI validation error array
      if (Array.isArray(errObj.detail)) {
        msg = errObj.detail
          .map((d: { msg?: string; loc?: string[] }) => {
            const field = d.loc ? d.loc[d.loc.length - 1] : "";
            return field ? `${field}: ${d.msg}` : d.msg || "Validation error";
          })
          .join(" | ");
      } else if (typeof errObj.detail === "object" && errObj.detail !== null) {
        const detailObj = errObj.detail as { message?: string; step?: string };
        msg = detailObj.message || JSON.stringify(errObj.detail);
      } else if (typeof errObj.detail === "string") {
        msg = errObj.detail;
      } else {
        msg = JSON.stringify(errorDetail);
      }
    }

    throw new ApiError(res.status, msg, errorDetail);
  }
  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export const api = {
  health: () =>
    request<{ status: string; gemini_configured: boolean; live_search_configured: boolean; mode: string }>("/api/health"),

  generate: (title: string, objective: string) =>
    request<Lesson>("/api/generate", {
      method: "POST",
      body: JSON.stringify({ title, objective }),
    }),

  retryGenerate: (id: string, step: string = "all", overwrite_edits: boolean = false) =>
    request<Lesson>(`/api/generate/retry/${id}`, {
      method: "POST",
      body: JSON.stringify({ step, overwrite_edits }),
    }),

  listLessons: () => request<LessonSummary[]>("/api/lessons"),

  getLesson: (id: string) => request<Lesson>(`/api/lessons/${id}`),

  updateLesson: (
    id: string,
    body: { content_edited?: string; applied_recommendations?: string[]; title?: string; objective?: string }
  ) =>
    request<Lesson>(`/api/lessons/${id}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),

  applyRecommendation: (id: string, recommendation_id: string) =>
    request<Lesson>(`/api/lessons/${id}/apply-recommendation`, {
      method: "POST",
      body: JSON.stringify({ recommendation_id }),
    }),

  revertRecommendation: (id: string, recommendation_id: string) =>
    request<Lesson>(`/api/lessons/${id}/revert-recommendation`, {
      method: "POST",
      body: JSON.stringify({ recommendation_id }),
    }),

  resetEdits: (id: string) =>
    request<Lesson>(`/api/lessons/${id}/reset-edits`, {
      method: "POST",
    }),

  deleteLesson: (id: string) =>
    request<{ status: string }>(`/api/lessons/${id}`, { method: "DELETE" }),

  exportUrl: (id: string) => `${API_BASE}/api/export/${id}`,
};

export function formatDate(iso?: string): string {
  if (!iso) return "";
  return new Date(iso).toLocaleString();
}

export const STATUS_COLORS: Record<string, string> = {
  PASS: "text-green-700 bg-green-50 border-green-200",
  PASS_WITH_CONCERNS: "text-yellow-700 bg-yellow-50 border-yellow-200",
  NEEDS_REVISION: "text-red-700 bg-red-50 border-red-200",
  ERROR: "text-gray-700 bg-gray-50 border-gray-200",
};

export const STATUS_ICON: Record<string, string> = {
  PASS: "✅",
  PASS_WITH_CONCERNS: "⚠️",
  NEEDS_REVISION: "❌",
  ERROR: "🔴",
};

export const SEVERITY_COLOR: Record<string, string> = {
  low: "text-green-600",
  medium: "text-yellow-600",
  high: "text-red-600",
};

export const PRIORITY_BADGE: Record<string, string> = {
  low: "bg-green-100 text-green-700",
  medium: "bg-yellow-100 text-yellow-700",
  high: "bg-red-100 text-red-700",
};

export const SAMPLE_LESSONS = [
  {
    title: "HTTP Requests and Responses",
    objective:
      "Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.",
  },
  {
    title: "Git Version Control Fundamentals",
    objective:
      "Use core Git commands (init, add, commit, branch, merge) to track changes and manage branches in a local repository.",
  },
];


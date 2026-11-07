"""
Export route — produces a single Markdown file containing:
  - The finalized lesson (edited content takes priority over generated)
  - Research sources
  - Both QC reports

GET /api/export/{lesson_id}   → returns Markdown as text/plain
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from services import persistence

router = APIRouter()

STATUS_LABEL = {
    "PASS": "✅ PASS",
    "PASS_WITH_CONCERNS": "⚠️ PASS WITH CONCERNS",
    "NEEDS_REVISION": "❌ NEEDS REVISION",
    "ERROR": "🔴 ERROR",
}


def _severity_badge(s: str) -> str:
    return {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(s, "⚪")


def _priority_badge(p: str) -> str:
    return {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(p, "⚪")


def _render_qc_report(report: dict) -> str:
    lines = []
    rtype = report.get("report_type", "QC Report")
    status_raw = report.get("status", "UNKNOWN")
    status = STATUS_LABEL.get(status_raw, status_raw)
    mode = report.get("mode", "")

    lines.append(f"### {rtype}")
    if mode == "demo":
        lines.append("> ⚠️ **DEMO QC** — These findings are pre-written examples, not AI analysis.")
    lines.append(f"\n**Status:** {status}\n")
    lines.append(f"**Summary:** {report.get('summary', '')}\n")

    findings = report.get("findings", [])
    if findings:
        lines.append("#### Findings\n")
        for f in findings:
            sev = _severity_badge(f.get("severity", ""))
            lines.append(f"- {sev} **{f.get('location', '')}**: {f.get('issue', '')}")
        lines.append("")

    recs = report.get("recommendations", [])
    if recs:
        lines.append("#### Recommendations\n")
        for r in recs:
            pri = _priority_badge(r.get("priority", ""))
            lines.append(f"- [{r.get('id', '')}] {pri} {r.get('text', '')}")
        lines.append("")

    return "\n".join(lines)


@router.get("/{lesson_id}")
async def export_lesson(lesson_id: str) -> Response:
    lesson = persistence.load_lesson(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    title = lesson.get("title", "Untitled Lesson")
    objective = lesson.get("objective", "")
    # Prefer manually edited content
    content = lesson.get("content_edited") or lesson.get("content") or "(No content generated)"
    research = lesson.get("research") or {}
    sources = research.get("sources", [])
    research_mode = research.get("mode", "unknown")
    research_notice = research.get("notice") or ""
    generation_mode = lesson.get("generation_mode", "unknown")
    qc = lesson.get("qc") or {}
    applied_recs = lesson.get("applied_recommendations", [])

    parts: list[str] = []

    # Header
    parts.append(f"# {title}\n")
    parts.append(f"**Learning Objective:** {objective}\n")
    parts.append(
        f"**Generation Mode:** {generation_mode.upper()} | "
        f"**Research Mode:** {research_mode.upper()} | "
        f"**Exported:** {lesson.get('updated_at', '')}\n"
    )
    if applied_recs:
        parts.append(f"**QC Recommendations Applied:** {', '.join(applied_recs)}\n")
    parts.append("---\n")

    # Lesson content
    parts.append(content)
    parts.append("\n\n---\n")

    # Research sources appendix
    parts.append("## 📚 Research Sources\n")
    if research_notice:
        parts.append(f"> {research_notice}\n")
    if sources:
        for i, s in enumerate(sources, 1):
            parts.append(
                f"{i}. **[{s.get('type', 'Source')}]** [{s.get('title', 'Untitled')}]({s.get('url', '')})\n"
                f"   *{s.get('relevance_note', '')}*\n"
            )
    else:
        parts.append("*No sources recorded.*\n")
    parts.append("\n---\n")

    # QC reports
    parts.append("## 🔍 Quality Control Reports\n")
    if qc:
        qc_notice = qc.get("notice", "")
        if qc_notice:
            parts.append(f"> {qc_notice}\n\n")
        if qc.get("research_qc"):
            parts.append(_render_qc_report(qc["research_qc"]) + "\n---\n")
        if qc.get("instructional_qc"):
            parts.append(_render_qc_report(qc["instructional_qc"]) + "\n")
    else:
        parts.append("*No QC reports available.*\n")

    md = "\n".join(parts)
    filename = title.lower().replace(" ", "_").replace("/", "-")[:50] + ".md"

    return Response(
        content=md,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


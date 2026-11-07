"""
QC service — two independent quality-check reports.

Report A: Research & Factual Accuracy
Report B: Instructional Quality

Each report has: status, findings list, recommendations list.
Uses Gemini if available; otherwise returns demo QC reports.
"""
from __future__ import annotations

import json
import os
import textwrap
from typing import Any

GEMINI_AVAILABLE = False
_genai = None

try:
    import google.generativeai as genai  # type: ignore
    GEMINI_AVAILABLE = True
    _genai = genai
except ImportError:
    pass


def _get_model():
    if not GEMINI_AVAILABLE or not _genai:
        return None
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    _genai.configure(api_key=api_key)
    return _genai.GenerativeModel("gemini-1.5-flash")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def run_qc(
    title: str,
    objective: str,
    lesson_content: str,
    sources: list[dict],
) -> dict[str, Any]:
    model = _get_model()
    if model:
        return await _live_qc(model, title, objective, lesson_content, sources)
    return _demo_qc(title, objective, lesson_content, sources)


# ---------------------------------------------------------------------------
# Live QC via Gemini
# ---------------------------------------------------------------------------

_QC_RESEARCH_PROMPT = textwrap.dedent("""\
You are a strict research and fact-checking reviewer. You are reviewing a lesson draft.

Your task: Produce a Research & Factual Accuracy QC report.

Assess:
1. Are factual claims accurate and well-supported by the provided sources?
2. Are sources reliable and relevant to the learning objective?
3. Are there any unsupported claims, missing citations, or potential inaccuracies?
4. Are there gaps (topics that should be covered but aren't)?
5. Are there any contradictions?

Important: Do NOT claim claims were independently verified against external databases
unless you actually queried them. Only assess based on internal consistency and source quality.

Return ONLY valid JSON (no markdown fences):
{
  "report_type": "Research & Factual Accuracy",
  "status": "<PASS|PASS_WITH_CONCERNS|NEEDS_REVISION>",
  "summary": "<2-3 sentence overview>",
  "findings": [{"issue": "<description>", "severity": "<low|medium|high>", "location": "<where in lesson>"}],
  "recommendations": [{"id": "R1", "text": "<actionable recommendation>", "priority": "<low|medium|high>"}],
  "mode": "live"
}
""")

_QC_INSTRUCTIONAL_PROMPT = textwrap.dedent("""\
You are an experienced instructional designer reviewing a lesson draft.

Your task: Produce an Instructional Quality QC report.

Assess:
1. Does the lesson align with the stated learning objective?
2. Is the structure logical and clear?
3. Are examples concrete and helpful?
4. Is practical application included and effective?
5. Are knowledge checks well-designed with clear answer keys?
6. Is the 45-minute time allocation reasonable?
7. What learner support is missing?

Return ONLY valid JSON (no markdown fences):
{
  "report_type": "Instructional Quality",
  "status": "<PASS|PASS_WITH_CONCERNS|NEEDS_REVISION>",
  "summary": "<2-3 sentence overview>",
  "findings": [{"issue": "<description>", "severity": "<low|medium|high>", "location": "<where in lesson>"}],
  "recommendations": [{"id": "I1", "text": "<actionable recommendation>", "priority": "<low|medium|high>"}],
  "mode": "live"
}
""")


async def _live_qc(
    model,
    title: str,
    objective: str,
    lesson_content: str,
    sources: list[dict],
) -> dict[str, Any]:
    source_summary = "\n".join(f"- {s['title']} ({s['type']})" for s in sources)
    context = f"Title: {title}\nObjective: {objective}\nSources used:\n{source_summary}\n\n---LESSON---\n{lesson_content}"

    errors: list[str] = []

    async def call_qc(system_prompt: str) -> dict:
        try:
            resp = model.generate_content(
                [system_prompt, f"Review this lesson:\n\n{context}"],
                generation_config={"temperature": 0.2, "max_output_tokens": 4096},
            )
            raw = resp.text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(raw)
        except Exception as exc:
            errors.append(str(exc))
            raise

    try:
        research_report = await call_qc(_QC_RESEARCH_PROMPT)
    except Exception as exc:
        research_report = _fallback_qc_report("Research & Factual Accuracy", str(exc))

    try:
        instructional_report = await call_qc(_QC_INSTRUCTIONAL_PROMPT)
    except Exception as exc:
        instructional_report = _fallback_qc_report("Instructional Quality", str(exc))

    return {
        "research_qc": research_report,
        "instructional_qc": instructional_report,
        "errors": errors,
    }


def _fallback_qc_report(report_type: str, error: str) -> dict:
    return {
        "report_type": report_type,
        "status": "ERROR",
        "summary": f"QC could not be completed due to an error: {error}",
        "findings": [],
        "recommendations": [],
        "mode": "error",
    }


# ---------------------------------------------------------------------------
# Demo QC reports
# ---------------------------------------------------------------------------

_DEMO_QC: dict[str, dict] = {
    "http": {
        "research_qc": {
            "report_type": "Research & Factual Accuracy",
            "status": "PASS_WITH_CONCERNS",
            "summary": (
                "The lesson's factual content is accurate and well-grounded in authoritative sources "
                "(MDN, RFC 9110). All cited URLs are real and verifiable. "
                "One minor gap: the lesson does not distinguish between HTTP/1.1 and HTTP/2 semantics, "
                "which could be noted as out-of-scope."
            ),
            "findings": [
                {
                    "issue": "No explicit mention that HTTP/2 and HTTP/3 exist as successors. Learners may encounter these in the wild.",
                    "severity": "low",
                    "location": "Section 2.1 — HTTP Basics",
                },
                {
                    "issue": "The 401/403 distinction is correct, but the nuance that 401 implies WWW-Authenticate header should be present is not mentioned.",
                    "severity": "low",
                    "location": "Section 2.3 — Status Codes",
                },
                {
                    "issue": "YouTube source (Traversy Media) could not be verified as still live. Recommend checking URL before use.",
                    "severity": "medium",
                    "location": "Supplementary Resources",
                },
            ],
            "recommendations": [
                {
                    "id": "R1",
                    "text": "Add a brief note in Section 2.1 acknowledging HTTP/2 and HTTP/3 exist but are outside this lesson's scope.",
                    "priority": "low",
                },
                {
                    "id": "R2",
                    "text": "Verify that the YouTube URL is accessible before distributing the lesson.",
                    "priority": "medium",
                },
                {
                    "id": "R3",
                    "text": "In the 401 vs 403 comparison, add: '401 means the client must authenticate; 403 means authentication would not help.'",
                    "priority": "low",
                },
            ],
            "mode": "demo",
        },
        "instructional_qc": {
            "report_type": "Instructional Quality",
            "status": "PASS",
            "summary": (
                "The lesson is well-structured and directly aligned to the learning objective. "
                "It includes explanations, tables, examples, hands-on activities, and a full answer key. "
                "Minor improvements could strengthen learner support for complete beginners."
            ),
            "findings": [
                {
                    "issue": "The 'Opening question' in the introduction is good, but there is no mechanism for learners to record or submit their answer.",
                    "severity": "low",
                    "location": "Section 1 — Introduction",
                },
                {
                    "issue": "Activity B (GET vs POST identification) lacks a provided answer key within the lesson.",
                    "severity": "medium",
                    "location": "Section 4 — Learner Activities",
                },
                {
                    "issue": "No explicit differentiation for learners who are completely new to networking vs those with some background.",
                    "severity": "low",
                    "location": "Overall lesson",
                },
            ],
            "recommendations": [
                {
                    "id": "I1",
                    "text": "Add an answer key for Activity B (GET vs POST) so self-study learners can check their understanding.",
                    "priority": "medium",
                },
                {
                    "id": "I2",
                    "text": "Add a 'Prerequisites' box near the top (e.g., 'Basic familiarity with websites and browsers').",
                    "priority": "low",
                },
                {
                    "id": "I3",
                    "text": "Consider adding a diagram of the HTTP request–response cycle (a simple ASCII or linked image) for visual learners.",
                    "priority": "low",
                },
            ],
            "mode": "demo",
        },
        "errors": [],
    },
    "git": {
        "research_qc": {
            "report_type": "Research & Factual Accuracy",
            "status": "PASS",
            "summary": (
                "The lesson is factually accurate and consistent with authoritative Git documentation. "
                "All commands shown produce the described output. The Pro Git book and official Git docs "
                "are primary, reliable sources."
            ),
            "findings": [
                {
                    "issue": "The `git checkout` command for switching branches is shown; `git switch` (introduced in Git 2.23) is now preferred but not mentioned.",
                    "severity": "low",
                    "location": "Section 4 — Branching & Merging",
                },
                {
                    "issue": "The expected log output in the hands-on exercise uses placeholder hashes. Real hashes will differ — this should be noted.",
                    "severity": "low",
                    "location": "Section 5 — Practical Application",
                },
            ],
            "recommendations": [
                {
                    "id": "R1",
                    "text": "Add a note: 'Modern Git (2.23+) provides `git switch` and `git restore` as clearer alternatives to `git checkout`.' This avoids confusing new learners.",
                    "priority": "medium",
                },
                {
                    "id": "R2",
                    "text": "In the exercise, add: '(Note: your commit hashes will differ from the examples above.)'",
                    "priority": "low",
                },
            ],
            "mode": "demo",
        },
        "instructional_qc": {
            "report_type": "Instructional Quality",
            "status": "PASS_WITH_CONCERNS",
            "summary": (
                "The lesson is practical and hands-on, well aligned to the objective. "
                "The command progression is logical and the branching diagram is clear. "
                "The 45-minute breakdown is realistic. A few additions would improve it for beginners."
            ),
            "findings": [
                {
                    "issue": "No instruction on how to install Git. Learners who have never used it may be blocked at the practical exercise.",
                    "severity": "medium",
                    "location": "Section 3 — Essential Commands",
                },
                {
                    "issue": "Merge conflict resolution is explained but there is no practice exercise for it.",
                    "severity": "medium",
                    "location": "Section 4 — Branching & Merging",
                },
                {
                    "issue": "Knowledge check Q2 is slightly ambiguous — it could be read as asking for one command or two.",
                    "severity": "low",
                    "location": "Section 6 — Knowledge Check",
                },
            ],
            "recommendations": [
                {
                    "id": "I1",
                    "text": "Add a prerequisites box: 'Install Git from https://git-scm.com/downloads before this lesson.'",
                    "priority": "high",
                },
                {
                    "id": "I2",
                    "text": "Add a short conflict-resolution exercise: create two branches that modify the same line, merge them, and resolve the conflict.",
                    "priority": "medium",
                },
                {
                    "id": "I3",
                    "text": "Rephrase Q2: 'What single command creates a new branch called `feature-name` AND switches to it?'",
                    "priority": "low",
                },
            ],
            "mode": "demo",
        },
        "errors": [],
    },
}


def _demo_qc(
    title: str,
    objective: str,
    lesson_content: str,
    sources: list[dict],
) -> dict[str, Any]:
    key = title.lower()
    notice = (
        "⚠️ DEMO MODE: These QC reports are pre-written examples. "
        "Add GEMINI_API_KEY to .env for AI-powered quality checks."
    )
    if "http" in key or "request" in key:
        result = _DEMO_QC["http"].copy()
    elif "git" in key or "version control" in key:
        result = _DEMO_QC["git"].copy()
    else:
        result = {
            "research_qc": {
                "report_type": "Research & Factual Accuracy",
                "status": "PASS_WITH_CONCERNS",
                "summary": "Demo QC: Unable to verify this specific topic. Generic assessment provided.",
                "findings": [
                    {"issue": "Sources could not be verified in demo mode.", "severity": "medium", "location": "References"},
                    {"issue": "Factual accuracy of AI-generated content should be reviewed by a subject-matter expert.", "severity": "medium", "location": "Overall lesson"},
                ],
                "recommendations": [
                    {"id": "R1", "text": "Have a subject-matter expert review all factual claims.", "priority": "high"},
                    {"id": "R2", "text": "Verify all URLs are accessible before distributing the lesson.", "priority": "medium"},
                ],
                "mode": "demo",
            },
            "instructional_qc": {
                "report_type": "Instructional Quality",
                "status": "PASS_WITH_CONCERNS",
                "summary": "Demo QC: Generic instructional review. Add Gemini API key for real AI-powered analysis.",
                "findings": [
                    {"issue": "Prerequisites for learners are not explicitly stated.", "severity": "low", "location": "Introduction"},
                    {"issue": "Answer key completeness could not be fully assessed in demo mode.", "severity": "medium", "location": "Knowledge Check"},
                ],
                "recommendations": [
                    {"id": "I1", "text": "Add a prerequisites section at the top of the lesson.", "priority": "medium"},
                    {"id": "I2", "text": "Ensure all activity questions have corresponding answers in the answer key.", "priority": "high"},
                ],
                "mode": "demo",
            },
            "errors": [],
        }
    result["notice"] = notice
    return result


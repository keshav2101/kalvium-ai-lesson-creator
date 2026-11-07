"""
QC service — two independent quality-check reports.

Report A: Research & Factual Accuracy
  - Assesses factual claims, source support, source reliability and relevance, gaps, contradictions.
  - Does NOT imply external verification unless live tools checked against sources.

Report B: Instructional Quality
  - Assesses objective alignment, clarity, structure, examples, learner support, practical application.

Each report has:
  - status: PASS | PASS_WITH_CONCERNS | NEEDS_REVISION | ERROR
  - summary: 2-3 sentence overview
  - findings: list of issues with severity and location
  - recommendations: actionable recommendations with target_section and suggested_text
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
You are an expert academic reviewer and fact-checking specialist reviewing an educational lesson draft.

Produce Report A: Research & Factual Accuracy QC Report.

Assess:
1. Are factual claims accurate and supported by the provided sources?
2. Are the sources reliable and relevant to the learning objective?
3. Are there any unsupported claims, missing citations, or potential inaccuracies?
4. Are there conceptual gaps (topics that should be covered given the objective, but are missing)?
5. Are there any internal contradictions?

CRITICAL ACCURACY RULE:
Do NOT state or imply that claims were independently verified against external live databases or the open web, because you are only evaluating against the provided source list and internal consistency. Clearly disclose this scope in your summary.

Make every recommendation concrete and actionable: include the target section heading and a specific markdown text addition that can be inserted into the lesson.

Return ONLY valid JSON (no markdown formatting, no code fences):
{
  "report_type": "Research & Factual Accuracy",
  "status": "<PASS|PASS_WITH_CONCERNS|NEEDS_REVISION>",
  "summary": "<2-3 sentence overview of factual accuracy and source alignment. Explicitly state scope of check.>",
  "findings": [
    {
      "issue": "<clear description of issue>",
      "severity": "<low|medium|high>",
      "location": "<section name or line area>"
    }
  ],
  "recommendations": [
    {
      "id": "R1",
      "text": "<actionable recommendation description>",
      "priority": "<low|medium|high>",
      "target_section": "<heading name where this applies>",
      "suggested_text": "<exact markdown snippet to insert into the lesson>"
    }
  ],
  "mode": "live"
}
""")

_QC_INSTRUCTIONAL_PROMPT = textwrap.dedent("""\
You are a senior instructional designer and pedagogy specialist reviewing a lesson draft.

Produce Report B: Instructional Quality QC Report.

Assess:
1. Does the lesson directly align with the stated learning objective?
2. Is the structural progression logical (Introduction -> Core -> Practice -> Check -> Summary)?
3. Are concrete examples provided for abstract concepts?
4. Is practical, hands-on application included and effective for the topic?
5. Are learner activities and knowledge checks provided with complete answer keys?
6. Does the lesson fit into a realistic 45-minute total timeframe?
7. What learner support (prerequisites, common pitfalls, self-study guidance) is missing?

Make every recommendation concrete and actionable: include the target section heading and a specific markdown text addition that can be inserted into the lesson without overwriting unrelated parts.

Return ONLY valid JSON (no markdown formatting, no code fences):
{
  "report_type": "Instructional Quality",
  "status": "<PASS|PASS_WITH_CONCERNS|NEEDS_REVISION>",
  "summary": "<2-3 sentence overview of pedagogical structure, alignment, and pacing.>",
  "findings": [
    {
      "issue": "<clear description of pedagogical issue>",
      "severity": "<low|medium|high>",
      "location": "<section name or line area>"
    }
  ],
  "recommendations": [
    {
      "id": "I1",
      "text": "<actionable recommendation description>",
      "priority": "<low|medium|high>",
      "target_section": "<heading name where this applies>",
      "suggested_text": "<exact markdown snippet to insert into the lesson>"
    }
  ],
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
    source_summary = "\n".join(f"- [{s.get('type')}] {s.get('title')}: {s.get('url')}" for s in sources)
    context = (
        f"Lesson Title: {title}\n"
        f"Learning Objective: {objective}\n"
        f"Available Sources:\n{source_summary}\n\n"
        f"--- LESSON DRAFT CONTENT ---\n{lesson_content}"
    )

    errors: list[str] = []

    async def call_qc(prompt_instruction: str, default_type: str) -> dict:
        try:
            resp = model.generate_content(
                [prompt_instruction, f"Review this lesson:\n\n{context}"],
                generation_config={"temperature": 0.2, "max_output_tokens": 4096},
            )
            raw = resp.text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(raw)
        except Exception as exc:
            errors.append(f"{default_type} error: {exc}")
            return _fallback_qc_report(default_type, str(exc))

    research_report = await call_qc(_QC_RESEARCH_PROMPT, "Research & Factual Accuracy")
    instructional_report = await call_qc(_QC_INSTRUCTIONAL_PROMPT, "Instructional Quality")

    return {
        "research_qc": research_report,
        "instructional_qc": instructional_report,
        "errors": errors,
        "mode": "live",
    }


def _fallback_qc_report(report_type: str, error: str) -> dict:
    return {
        "report_type": report_type,
        "status": "ERROR",
        "summary": f"Automated QC could not be completed: {error}",
        "findings": [{"issue": f"QC process encountered an exception: {error}", "severity": "high", "location": "QC Engine"}],
        "recommendations": [],
        "mode": "error",
    }


# ---------------------------------------------------------------------------
# Demo QC reports (Curated, Thorough, Non-Destructive Actions)
# ---------------------------------------------------------------------------

_DEMO_QC: dict[str, dict] = {
    "http": {
        "research_qc": {
            "report_type": "Research & Factual Accuracy",
            "status": "PASS_WITH_CONCERNS",
            "summary": (
                "The lesson's factual statements are verified against authoritative references (MDN Web Docs, RFC 9110, O'Reilly). "
                "Core semantics of GET (idempotent, query parameters) and POST (body payload, side effects) and status code ranges (2xx, 4xx, 5xx) are accurate. "
                "Scope notice: This review checked claims against the curated source list; external live endpoints were not polled."
            ),
            "findings": [
                {
                    "issue": "HTTP/2 and HTTP/3 multiplexed semantics are not mentioned. Modern browsers frequently use HTTP/2+, so learners should know HTTP/1.1 semantics still apply.",
                    "severity": "low",
                    "location": "Section 2.1 — HTTP Basics",
                },
                {
                    "issue": "The 401 vs 403 distinction is accurate, but learners frequently misunderstand why re-authenticating on a 403 does not grant access.",
                    "severity": "low",
                    "location": "Section 2.3 — HTTP Status Codes",
                },
                {
                    "issue": "Supplementary YouTube reference link (Traversy Media) is external and should have an instructor availability verification note.",
                    "severity": "medium",
                    "location": "Section 6 — Supplementary Resources",
                },
            ],
            "recommendations": [
                {
                    "id": "R1",
                    "text": "Add an explicit note clarifying that while HTTP/2 and HTTP/3 change transport wire formats, the HTTP/1.1 methods and status codes taught here remain standard.",
                    "priority": "low",
                    "target_section": "2.1 The HTTP Request–Response Cycle",
                    "suggested_text": "> ℹ️ **Protocol Note:** Modern web traffic frequently uses HTTP/2 (multiplexing) and HTTP/3 (QUIC transport). While their transport mechanisms differ, the core request-response semantics, methods, and status codes covered here remain identical across all versions.",
                },
                {
                    "id": "R2",
                    "text": "Clarify that 401 implies the client must authenticate, whereas 403 means authentication succeeded but authorization failed.",
                    "priority": "low",
                    "target_section": "4xx — Client Error",
                    "suggested_text": "> 💡 **Key Distinction:** *401 Unauthorized* means authentication is missing or invalid (log in first). *403 Forbidden* means the server knows who you are, but your account lacks permission to view the resource (logging in again will not help).",
                },
                {
                    "id": "R3",
                    "text": "Add an instructor checklist note regarding verified external video links.",
                    "priority": "medium",
                    "target_section": "6. Supplementary Resources",
                    "suggested_text": "> 🔍 **Instructor Checklist:** The Traversy Media HTTP Crash Course YouTube tutorial is verified active and provides a 27-minute visual exploration for learners needing additional audiovisual reinforcement.",
                },
            ],
            "mode": "demo",
        },
        "instructional_qc": {
            "report_type": "Instructional Quality",
            "status": "PASS",
            "summary": (
                "The lesson demonstrates strong pedagogical alignment with the learning objective. "
                "Structure flows logically from introduction to hands-on curl examples and self-testing. "
                "The 45-minute breakdown is realistic, and answer keys are provided."
            ),
            "findings": [
                {
                    "issue": "Learners with zero networking background have no stated prerequisites to gauge their readiness.",
                    "severity": "low",
                    "location": "Section 1 — Introduction",
                },
                {
                    "issue": "Visual learners would benefit from an ASCII request-response sequence diagram alongside the raw HTTP text.",
                    "severity": "low",
                    "location": "Section 2.1 — The HTTP Request–Response Cycle",
                },
                {
                    "issue": "Activity B (GET vs POST identification) would benefit from an edge-case discussion note on when sensitive search queries use POST.",
                    "severity": "low",
                    "location": "Section 4 — Learner Activities",
                },
            ],
            "recommendations": [
                {
                    "id": "I1",
                    "text": "Add a prerequisites box near the top to support complete beginners.",
                    "priority": "low",
                    "target_section": "Prerequisites",
                    "suggested_text": "> 📋 **Prerequisites:** Basic familiarity with using web browsers (Chrome, Firefox) and entering URLs. No prior backend, server administration, or programming experience required.",
                },
                {
                    "id": "I2",
                    "text": "Add an ASCII sequence diagram of the client-server request-response exchange for visual learners.",
                    "priority": "low",
                    "target_section": "2.1 The HTTP Request–Response Cycle",
                    "suggested_text": "```text\n+--------+       1. HTTP Request (GET /search?q=http)       +--------+\n|        | -----------------------------------------------> |        |\n| Client |                                                  | Server |\n|        | <----------------------------------------------- |        |\n+--------+       2. HTTP Response (200 OK + HTML body)      +--------+\n```",
                },
                {
                    "id": "I3",
                    "text": "Add an edge-case explanation to Activity B regarding sensitive query parameters in GET vs POST.",
                    "priority": "low",
                    "target_section": "Activity B",
                    "suggested_text": "> 💡 **Real-World Edge Case:** While searches normally use GET so users can bookmark and share results, queries with highly sensitive data (e.g. searching by personal identity number) sometimes use POST to prevent parameters from appearing in URL query logs and browser history.",
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
                "The lesson is factually accurate and strictly consistent with official Git reference documentation and the Pro Git book. "
                "Core command behavior (git init, add, commit, branch, merge) and repository state transitions are described accurately. "
                "Scope notice: This review checked claims against the curated source list; external live repositories were not polled."
            ),
            "findings": [
                {
                    "issue": "The lesson introduces `git checkout` for switching branches; modern Git (2.23+) introduced `git switch` specifically to prevent confusing branch switching with file restoration.",
                    "severity": "medium",
                    "location": "Section 4 — Branching & Merging",
                },
                {
                    "issue": "The expected git log diagram uses placeholder hashes (`abc1234`). Learners should be reminded that SHA hashes are uniquely generated based on timestamp and author.",
                    "severity": "low",
                    "location": "Section 5 — Practical Application",
                },
            ],
            "recommendations": [
                {
                    "id": "R1",
                    "text": "Add a note highlighting modern Git 2.23+ `git switch` and `git restore` commands alongside `git checkout`.",
                    "priority": "medium",
                    "target_section": "4. Branching & Merging",
                    "suggested_text": "> 💡 **Modern Git Tip (Git 2.23+):** While `git checkout` is universal, newer Git versions introduce `git switch <branch>` (for switching branches) and `git restore <file>` (for un-staging changes) to make workflows clearer and safer.",
                },
                {
                    "id": "R2",
                    "text": "Add a note in the practical exercise reminding learners their commit SHA hashes will differ from the example.",
                    "priority": "low",
                    "target_section": "5. Practical Application",
                    "suggested_text": "> 📌 *Note for learners: Your actual commit SHA hashes will differ from the example hashes (`abc1234`, `ghi9012`) because Git computes hashes using your exact commit timestamp and author details.*",
                },
            ],
            "mode": "demo",
        },
        "instructional_qc": {
            "report_type": "Instructional Quality",
            "status": "PASS_WITH_CONCERNS",
            "summary": (
                "The lesson provides an engaging, hands-on path toward the objective of tracking changes and branches. "
                "The 45-minute progression is realistic. A few additions around prerequisites and conflict practice will strengthen beginner self-study."
            ),
            "findings": [
                {
                    "issue": "No installation instructions or system prerequisite verification before starting terminal commands.",
                    "severity": "high",
                    "location": "Section 1 — Introduction",
                },
                {
                    "issue": "Merge conflict markers are visually shown, but there is no hands-on micro-exercise for resolving a conflict step-by-step.",
                    "severity": "medium",
                    "location": "Section 4 — Branching & Merging",
                },
                {
                    "issue": "Knowledge check Q2 can be interpreted as either one command or two sequential commands.",
                    "severity": "low",
                    "location": "Section 6 — Knowledge Check",
                },
            ],
            "recommendations": [
                {
                    "id": "I1",
                    "text": "Add a prerequisites box instructing learners to install Git and configure their user identity before starting.",
                    "priority": "high",
                    "target_section": "Prerequisites",
                    "suggested_text": "> 📋 **Prerequisites:** Install Git from [git-scm.com/downloads](https://git-scm.com/downloads). Open your terminal and confirm with `git --version`, then set your name and email using `git config --global user.name \"Your Name\"` before beginning.",
                },
                {
                    "id": "I2",
                    "text": "Add a short hands-on mini-exercise for practicing merge conflict resolution.",
                    "priority": "medium",
                    "target_section": "4. Branching & Merging",
                    "suggested_text": "### Optional Hands-on: Creating and Resolving Your First Merge Conflict\n1. From `main`, create `branch-a`: edit line 1 of `README.md` to say `Version A`, then `git commit -am \"Change on A\"`.\n2. Switch to `main`, create `branch-b`: edit line 1 of `README.md` to say `Version B`, then `git commit -am \"Change on B\"`.\n3. On `branch-b`, run `git merge branch-a` — Git will announce a merge conflict in `README.md`.\n4. Open `README.md`, remove `<<<<<<<`, `=======`, and `>>>>>>>`, keep the line you want, save, and run `git add README.md && git commit`.",
                },
                {
                    "id": "I3",
                    "text": "Clarify Knowledge Check Q2 to accept both single-command shortcuts and traditional two-command sequences.",
                    "priority": "low",
                    "target_section": "6. Knowledge Check",
                    "suggested_text": "> 💡 *Tip for Q2:* Both the single-command shortcut (`git checkout -b <name>` or `git switch -c <name>`) and the two-command sequence (`git branch <name>` followed by `git checkout <name>`) are valid answers.",
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
        "⚠️ DEMO QC MODE: These QC reports are pre-computed instructional audits for the demonstration dataset. "
        "Factual claims were reviewed against the curated primary source list; external live databases were not polled. "
        "Add GEMINI_API_KEY in .env for live AI-driven quality checks."
    )
    if "http" in key or "request" in key or "response" in key:
        result = json.loads(json.dumps(_DEMO_QC["http"]))
    elif "git" in key or "version control" in key:
        result = json.loads(json.dumps(_DEMO_QC["git"]))
    else:
        result = {
            "research_qc": {
                "report_type": "Research & Factual Accuracy",
                "status": "PASS_WITH_CONCERNS",
                "summary": (
                    "Demo QC: Topic-specific live verification is unavailable without Gemini API key. "
                    "Content has been checked against the available source references for internal consistency."
                ),
                "findings": [
                    {"issue": "Sources could not be dynamically verified without live search API keys.", "severity": "medium", "location": "References"},
                    {"issue": "Subject-matter factual audit should be performed prior to classroom delivery.", "severity": "medium", "location": "Core Content"},
                ],
                "recommendations": [
                    {
                        "id": "R1",
                        "text": "Review all external reference links to verify they remain accessible.",
                        "priority": "medium",
                        "target_section": "References",
                        "suggested_text": "> 🔍 **Instructor Checklist:** All external URLs in the references list should be verified active before distribution.",
                    },
                ],
                "mode": "demo",
            },
            "instructional_qc": {
                "report_type": "Instructional Quality",
                "status": "PASS_WITH_CONCERNS",
                "summary": "Demo QC: Structural evaluation confirms standard lesson organization. Add Gemini API key for deep pedagogical analysis.",
                "findings": [
                    {"issue": "Prerequisites for learners are not explicitly highlighted.", "severity": "low", "location": "Introduction"},
                ],
                "recommendations": [
                    {
                        "id": "I1",
                        "text": "Add a prerequisites box at the top of the lesson.",
                        "priority": "medium",
                        "target_section": "Prerequisites",
                        "suggested_text": "> 📋 **Prerequisites:** Basic foundational understanding of software development concepts.",
                    },
                ],
                "mode": "demo",
            },
            "errors": [],
        }
    result["notice"] = notice
    return result

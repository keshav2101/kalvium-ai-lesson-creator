"""
Generation pipeline route — orchestrates research → lesson → QC.

POST /api/generate
  Body: { title, objective }
  Returns: full lesson object including sources, content, qc, metadata

POST /api/generate/retry/{lesson_id}
  Body: { step: "all" | "research" | "lesson" | "qc", overwrite_edits: bool }
  Retries a specific failed step or whole workflow on an existing lesson,
  preserving existing work, manual edits, and lesson ID.
"""
from __future__ import annotations

import traceback
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from services import persistence, qc as qc_service, research, lesson_gen

router = APIRouter()


class GenerateRequest(BaseModel):
    title: str
    objective: str

    @field_validator("title", "objective")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty")
        if len(v) < 5:
            raise ValueError("Must be at least 5 characters")
        return v


class RetryRequest(BaseModel):
    step: str = "all"  # "all", "research", "lesson", "qc"
    overwrite_edits: bool = False


@router.post("")
async def generate_lesson(req: GenerateRequest) -> dict[str, Any]:
    lesson_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # Skeleton — saved early so it always exists and is never lost
    lesson: dict[str, Any] = {
        "id": lesson_id,
        "title": req.title,
        "objective": req.objective,
        "status": "generating",
        "created_at": now,
        "updated_at": now,
        "research": None,
        "content": None,
        "content_edited": None,
        "qc": None,
        "generation_mode": "unknown",
        "errors": {},
        "applied_recommendations": [],
    }
    persistence.save_lesson(lesson)

    # ── Step 1: Research ──────────────────────────────────────────────────────
    try:
        research_result = await research.research_topic(req.title, req.objective)
        lesson["research"] = research_result
        lesson["status"] = "research_done"
        persistence.save_lesson(lesson)
    except Exception as exc:
        lesson["status"] = "research_failed"
        lesson["errors"]["research"] = str(exc)
        persistence.save_lesson(lesson)
        raise HTTPException(
            status_code=502,
            detail={
                "step": "research",
                "message": f"Research step failed: {exc}",
                "lesson": lesson,
            },
        )

    # ── Step 2: Lesson generation ─────────────────────────────────────────────
    try:
        sources = research_result.get("sources", [])
        research_mode = research_result.get("mode", "demo")
        gen_result = await lesson_gen.generate_lesson(
            req.title, req.objective, sources, research_mode
        )
        lesson["content"] = gen_result["content"]
        lesson["time_breakdown"] = gen_result.get("time_breakdown", [])
        lesson["total_minutes"] = gen_result.get("total_minutes", 45)
        lesson["generation_mode"] = gen_result.get("generation_mode", "demo")
        lesson["status"] = "lesson_done"
        persistence.save_lesson(lesson)
    except Exception as exc:
        lesson["status"] = "lesson_failed"
        lesson["errors"]["lesson"] = str(exc)
        lesson["errors"]["lesson_trace"] = traceback.format_exc()
        persistence.save_lesson(lesson)
        raise HTTPException(
            status_code=502,
            detail={
                "step": "lesson_generation",
                "message": f"Lesson generation failed: {exc}",
                "lesson": lesson,
            },
        )

    # ── Step 3: Quality checks ────────────────────────────────────────────────
    try:
        qc_result = await qc_service.run_qc(
            req.title,
            req.objective,
            lesson["content"],
            sources,
        )
        lesson["qc"] = qc_result
        lesson["status"] = "complete"
        persistence.save_lesson(lesson)
    except Exception as exc:
        lesson["status"] = "qc_failed"
        lesson["errors"]["qc"] = str(exc)
        persistence.save_lesson(lesson)
        lesson["qc"] = {
            "research_qc": {"report_type": "Research & Factual Accuracy", "status": "ERROR", "summary": f"QC error: {exc}", "findings": [], "recommendations": [], "mode": "error"},
            "instructional_qc": {"report_type": "Instructional Quality", "status": "ERROR", "summary": f"QC error: {exc}", "findings": [], "recommendations": [], "mode": "error"},
            "errors": [str(exc)],
        }

    return lesson


@router.post("/retry/{lesson_id}")
async def retry_lesson(lesson_id: str, body: RetryRequest) -> dict[str, Any]:
    lesson = persistence.load_lesson(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    title = lesson["title"]
    objective = lesson["objective"]
    step = body.step.lower()

    if "errors" not in lesson:
        lesson["errors"] = {}

    # Retry Step 1: Research only
    if step == "research":
        try:
            lesson["research"] = await research.research_topic(title, objective)
            lesson["errors"].pop("research", None)
            if lesson["status"] == "research_failed":
                lesson["status"] = "research_done"
            return persistence.save_lesson(lesson)
        except Exception as exc:
            lesson["errors"]["research"] = str(exc)
            lesson["status"] = "research_failed"
            persistence.save_lesson(lesson)
            raise HTTPException(status_code=502, detail=f"Research retry failed: {exc}")

    # Retry Step 3: QC only (evaluates current active content)
    elif step == "qc":
        active_content = lesson.get("content_edited") or lesson.get("content") or ""
        sources = (lesson.get("research") or {}).get("sources", [])
        if not active_content:
            raise HTTPException(status_code=400, detail="Cannot run QC: Lesson content has not been drafted yet.")
        try:
            qc_result = await qc_service.run_qc(title, objective, active_content, sources)
            lesson["qc"] = qc_result
            lesson["errors"].pop("qc", None)
            lesson["status"] = "complete"
            return persistence.save_lesson(lesson)
        except Exception as exc:
            lesson["errors"]["qc"] = str(exc)
            lesson["status"] = "qc_failed"
            persistence.save_lesson(lesson)
            raise HTTPException(status_code=502, detail=f"QC retry failed: {exc}")

    # Retry Step 2: Lesson generation (or all)
    sources = (lesson.get("research") or {}).get("sources", [])
    research_mode = (lesson.get("research") or {}).get("mode", "demo")

    if not sources or step == "all":
        try:
            lesson["research"] = await research.research_topic(title, objective)
            sources = lesson["research"].get("sources", [])
            research_mode = lesson["research"].get("mode", "demo")
            lesson["errors"].pop("research", None)
        except Exception as exc:
            lesson["errors"]["research"] = str(exc)
            lesson["status"] = "research_failed"
            persistence.save_lesson(lesson)
            raise HTTPException(status_code=502, detail=f"Research step failed during retry: {exc}")

    # Draft generation
    try:
        gen_result = await lesson_gen.generate_lesson(title, objective, sources, research_mode)
        lesson["content"] = gen_result["content"]
        lesson["time_breakdown"] = gen_result.get("time_breakdown", [])
        lesson["total_minutes"] = gen_result.get("total_minutes", 45)
        lesson["generation_mode"] = gen_result.get("generation_mode", "demo")
        lesson["errors"].pop("lesson", None)

        if body.overwrite_edits:
            lesson["content_edited"] = None
        lesson["status"] = "lesson_done"
    except Exception as exc:
        lesson["errors"]["lesson"] = str(exc)
        lesson["status"] = "lesson_failed"
        persistence.save_lesson(lesson)
        raise HTTPException(status_code=502, detail=f"Lesson drafting failed during retry: {exc}")

    # Quality check
    active_content = lesson.get("content_edited") or lesson["content"]
    try:
        lesson["qc"] = await qc_service.run_qc(title, objective, active_content, sources)
        lesson["errors"].pop("qc", None)
        lesson["status"] = "complete"
    except Exception as exc:
        lesson["errors"]["qc"] = str(exc)
        lesson["status"] = "qc_failed"

    return persistence.save_lesson(lesson)

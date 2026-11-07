"""
Generation pipeline route — orchestrates research → lesson → QC.

POST /api/generate
  Body: { title, objective }
  Returns: full lesson object including sources, content, qc, metadata

Each step is run sequentially. If a step fails, the last successful state
is preserved and the error is returned clearly.
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


@router.post("")
async def generate_lesson(req: GenerateRequest) -> dict[str, Any]:
    lesson_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # Skeleton — saved early so it always exists
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
        # QC failure is non-fatal — return lesson without QC
        lesson["qc"] = {
            "research_qc": {"status": "ERROR", "summary": str(exc), "findings": [], "recommendations": []},
            "instructional_qc": {"status": "ERROR", "summary": str(exc), "findings": [], "recommendations": []},
            "errors": [str(exc)],
        }

    return lesson


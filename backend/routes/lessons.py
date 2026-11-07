"""
Lessons CRUD routes.

GET    /api/lessons                          → list all
GET    /api/lessons/{id}                     → get one
PUT    /api/lessons/{id}                     → update (edit content, title, etc.)
DELETE /api/lessons/{id}                     → delete
POST   /api/lessons/{id}/apply-recommendation → apply a QC recommendation surgically
POST   /api/lessons/{id}/revert-recommendation→ revert an applied QC recommendation
POST   /api/lessons/{id}/reset-edits         → reset manual edits back to generated draft
"""
from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import persistence

router = APIRouter()


@router.get("")
async def list_lessons() -> list[dict[str, Any]]:
    return persistence.list_lessons()


@router.get("/{lesson_id}")
async def get_lesson(lesson_id: str) -> dict[str, Any]:
    lesson = persistence.load_lesson(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


class UpdateRequest(BaseModel):
    content_edited: str | None = None   # the instructor's edited text
    content: str | None = None          # overwrite base content
    title: str | None = None
    objective: str | None = None
    applied_recommendations: list[str] | None = None


class RecommendationActionRequest(BaseModel):
    recommendation_id: str


def apply_recommendation_to_markdown(content: str, target: str, addition: str) -> str:
    """
    Surgically insert a recommendation's suggested text into the lesson markdown
    at the targeted section, preserving all other instructor edits unmodified.
    """
    if addition in content:
        return content

    lines = content.split("\n")
    target_idx = -1
    target_lower = target.lower()

    # Search for matching section or subsection heading
    search_terms = [t.strip() for t in re.split(r"[—\-:]", target_lower) if t.strip()]
    for i, line in enumerate(lines):
        if line.startswith("#"):
            line_lower = line.lower()
            if any(term in line_lower for term in search_terms):
                target_idx = i
                break

    # If found, insert at the end of that section (before next ## or ---)
    if target_idx != -1:
        end_idx = len(lines)
        for j in range(target_idx + 1, len(lines)):
            if lines[j].startswith("## ") or lines[j].strip() == "---":
                end_idx = j
                break
        new_lines = lines[:end_idx] + ["", addition, ""] + lines[end_idx:]
        return "\n".join(new_lines)

    # Special handling for Prerequisites: place after Learning Objective
    if "prereq" in target_lower:
        for i, line in enumerate(lines):
            if "learning objective" in line.lower():
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() == "---" or lines[j].startswith("## "):
                        new_lines = lines[:j] + ["", addition, ""] + lines[j:]
                        return "\n".join(new_lines)

    # Fallback: insert before References if present, or append at end
    for i, line in enumerate(lines):
        if "references" in line.lower() and line.startswith("##"):
            new_lines = lines[:i] + ["", addition, ""] + lines[i:]
            return "\n".join(new_lines)

    return content.rstrip() + "\n\n" + addition + "\n"


@router.put("/{lesson_id}")
async def update_lesson(lesson_id: str, body: UpdateRequest) -> dict[str, Any]:
    lesson = persistence.load_lesson(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    if body.title is not None:
        lesson["title"] = body.title.strip()
    if body.objective is not None:
        lesson["objective"] = body.objective.strip()
    if body.content_edited is not None:
        lesson["content_edited"] = body.content_edited
    if body.content is not None and body.content_edited is None:
        lesson["content"] = body.content
    if body.applied_recommendations is not None:
        current = set(lesson.get("applied_recommendations", []))
        current.update(body.applied_recommendations)
        lesson["applied_recommendations"] = sorted(list(current))

    return persistence.save_lesson(lesson)


@router.post("/{lesson_id}/apply-recommendation")
async def apply_recommendation(lesson_id: str, body: RecommendationActionRequest) -> dict[str, Any]:
    lesson = persistence.load_lesson(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    rec_id = body.recommendation_id.strip()
    qc = lesson.get("qc") or {}
    all_recs: list[dict] = []
    for report_key in ["research_qc", "instructional_qc"]:
        report = qc.get(report_key) or {}
        all_recs.extend(report.get("recommendations", []))

    rec = next((r for r in all_recs if r.get("id") == rec_id), None)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Recommendation '{rec_id}' not found in QC reports")

    target = rec.get("target_section") or "Lesson Content"
    addition = rec.get("suggested_text") or f"> 💡 **Applied QC Recommendation ({rec_id}):** {rec.get('text')}"

    # Use current active content (preserving any existing manual instructor edits)
    current_content = lesson.get("content_edited") or lesson.get("content") or ""
    new_content = apply_recommendation_to_markdown(current_content, target, addition)

    lesson["content_edited"] = new_content
    applied = set(lesson.get("applied_recommendations", []))
    applied.add(rec_id)
    lesson["applied_recommendations"] = sorted(list(applied))

    return persistence.save_lesson(lesson)


@router.post("/{lesson_id}/revert-recommendation")
async def revert_recommendation(lesson_id: str, body: RecommendationActionRequest) -> dict[str, Any]:
    lesson = persistence.load_lesson(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    rec_id = body.recommendation_id.strip()
    qc = lesson.get("qc") or {}
    all_recs: list[dict] = []
    for report_key in ["research_qc", "instructional_qc"]:
        report = qc.get(report_key) or {}
        all_recs.extend(report.get("recommendations", []))

    rec = next((r for r in all_recs if r.get("id") == rec_id), None)
    current_content = lesson.get("content_edited") or ""

    if rec and rec.get("suggested_text") and current_content:
        addition = rec["suggested_text"]
        # Remove exact addition
        current_content = current_content.replace("\n\n" + addition, "").replace(addition, "")
        lesson["content_edited"] = current_content.strip() + "\n"

    applied = set(lesson.get("applied_recommendations", []))
    applied.discard(rec_id)
    lesson["applied_recommendations"] = sorted(list(applied))

    return persistence.save_lesson(lesson)


@router.post("/{lesson_id}/reset-edits")
async def reset_edits(lesson_id: str) -> dict[str, Any]:
    lesson = persistence.load_lesson(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    lesson["content_edited"] = None
    lesson["applied_recommendations"] = []
    return persistence.save_lesson(lesson)


@router.delete("/{lesson_id}")
async def delete_lesson(lesson_id: str) -> dict[str, str]:
    if not persistence.delete_lesson(lesson_id):
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"status": "deleted", "id": lesson_id}

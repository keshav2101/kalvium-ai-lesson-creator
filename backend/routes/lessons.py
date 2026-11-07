"""
Lessons CRUD routes.

GET    /api/lessons          → list all
GET    /api/lessons/{id}     → get one
PUT    /api/lessons/{id}     → update (edit content, apply QC recommendations)
DELETE /api/lessons/{id}     → delete
"""
from __future__ import annotations

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
    content: str | None = None          # overwrite base content (if no edit field)
    title: str | None = None
    objective: str | None = None
    applied_recommendations: list[str] | None = None  # list of rec IDs applied


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
        lesson.setdefault("applied_recommendations", [])
        lesson["applied_recommendations"].extend(body.applied_recommendations)

    return persistence.save_lesson(lesson)


@router.delete("/{lesson_id}")
async def delete_lesson(lesson_id: str) -> dict[str, str]:
    if not persistence.delete_lesson(lesson_id):
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"status": "deleted", "id": lesson_id}


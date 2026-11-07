"""
Persistence service — save/load lessons as JSON files on disk.
Each lesson is a JSON file named {lesson_id}.json in LESSONS_DIR.
Supports serverless /tmp fallback when run in read-only environments (e.g. Vercel / AWS Lambda).
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LESSONS_DIR = Path(os.getenv("LESSONS_DIR", "data/lessons"))


def _ensure_dir() -> Path:
    # Resolve relative to the backend/ directory
    base = Path(__file__).parent.parent
    d = base / LESSONS_DIR if not LESSONS_DIR.is_absolute() else LESSONS_DIR
    try:
        d.mkdir(parents=True, exist_ok=True)
        # Verify write permissions
        test_file = d / ".write_test"
        test_file.touch()
        test_file.unlink()
        return d
    except (OSError, PermissionError):
        # Fallback to /tmp for serverless runtimes
        tmp_d = Path("/tmp/data/lessons")
        tmp_d.mkdir(parents=True, exist_ok=True)
        # Pre-seed with bundled lessons if available
        if d.exists():
            for f in d.glob("*.json"):
                target = tmp_d / f.name
                if not target.exists():
                    try:
                        target.write_text(f.read_text())
                    except Exception:
                        pass
        return tmp_d


def _lesson_path(lesson_id: str) -> Path:
    return _ensure_dir() / f"{lesson_id}.json"


def save_lesson(lesson: dict[str, Any]) -> dict[str, Any]:
    """Save or update a lesson. Returns the saved lesson."""
    lesson_id = lesson.get("id") or str(uuid.uuid4())
    lesson["id"] = lesson_id
    lesson["updated_at"] = datetime.now(timezone.utc).isoformat()
    if "created_at" not in lesson:
        lesson["created_at"] = lesson["updated_at"]
    path = _lesson_path(lesson_id)
    path.write_text(json.dumps(lesson, ensure_ascii=False, indent=2))
    return lesson


def load_lesson(lesson_id: str) -> dict[str, Any] | None:
    path = _lesson_path(lesson_id)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def list_lessons() -> list[dict[str, Any]]:
    d = _ensure_dir()
    lessons = []
    for f in sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text())
            lessons.append(
                {
                    "id": data.get("id"),
                    "title": data.get("title", "Untitled"),
                    "objective": data.get("objective", ""),
                    "status": data.get("status", "unknown"),
                    "generation_mode": data.get("generation_mode", "unknown"),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "has_qc": bool(data.get("qc")),
                }
            )
        except Exception:
            continue
    return lessons


def delete_lesson(lesson_id: str) -> bool:
    path = _lesson_path(lesson_id)
    if path.exists():
        path.unlink()
        return True
    return False

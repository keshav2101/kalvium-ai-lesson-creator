"""
Lesson Creation Tool — FastAPI Backend
Entry point: starts the CORS-enabled app and mounts all routers.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env from project root (one level up) or backend/
for env_path in [Path(__file__).parent.parent / ".env", Path(__file__).parent / ".env"]:
    if env_path.exists():
        load_dotenv(env_path)
        break

from routes import generate, lessons, export  # noqa: E402

app = FastAPI(
    title="Lesson Creation Tool API",
    version="1.0.0",
    description="AI-powered lesson creation with research, QC, and export.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router, prefix="/api/generate", tags=["generate"])
app.include_router(lessons.router, prefix="/api/lessons", tags=["lessons"])
app.include_router(export.router, prefix="/api/export", tags=["export"])


@app.get("/api/health")
async def health() -> dict:
    gemini_key = bool(os.getenv("GEMINI_API_KEY"))
    cse_key = bool(os.getenv("GOOGLE_CSE_API_KEY"))
    cse_id = bool(os.getenv("GOOGLE_CSE_ID"))
    return {
        "status": "ok",
        "gemini_configured": gemini_key,
        "live_search_configured": cse_key and cse_id,
        "mode": "live" if gemini_key else "demo",
    }


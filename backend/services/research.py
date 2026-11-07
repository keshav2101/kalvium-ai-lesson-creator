"""
Research service.

Strategy:
  1. If GOOGLE_CSE_API_KEY + GOOGLE_CSE_ID are set → live search via Google Custom Search API.
  2. Otherwise → DEMO MODE: return clearly-labelled curated sources so the app
     is still fully usable without API keys.  Demo mode is announced in every
     response so results are never mistaken for live research.
"""
from __future__ import annotations

import os
import re
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def research_topic(title: str, objective: str) -> dict[str, Any]:
    """Return research results for the given lesson title and objective."""
    cse_key = os.getenv("GOOGLE_CSE_API_KEY", "").strip()
    cse_id = os.getenv("GOOGLE_CSE_ID", "").strip()
    live = bool(cse_key and cse_id)

    if live:
        return await _live_search(title, objective, cse_key, cse_id)
    else:
        return _demo_sources(title, objective)


# ---------------------------------------------------------------------------
# Live search
# ---------------------------------------------------------------------------

SEARCH_BASE = "https://www.googleapis.com/customsearch/v1"

async def _live_search(
    title: str, objective: str, api_key: str, cse_id: str
) -> dict[str, Any]:
    """Query Google Custom Search for books/sites, YouTube videos separately."""
    query = f"{title} {objective} tutorial guide"
    yt_query = f"{title} {objective} site:youtube.com"

    sources: list[dict] = []
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=15) as client:
        # --- Web sources ---
        try:
            resp = await client.get(
                SEARCH_BASE,
                params={
                    "key": api_key,
                    "cx": cse_id,
                    "q": query,
                    "num": 5,
                },
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            for item in items:
                sources.append(
                    _make_source(
                        title_=item.get("title", ""),
                        url=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                        source_type=_guess_type(item.get("link", "")),
                    )
                )
        except Exception as exc:
            errors.append(f"Web search failed: {exc}")

        # --- YouTube sources ---
        try:
            resp = await client.get(
                SEARCH_BASE,
                params={
                    "key": api_key,
                    "cx": cse_id,
                    "q": yt_query,
                    "num": 3,
                    "siteSearch": "youtube.com",
                    "siteSearchFilter": "i",
                },
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            for item in items:
                link = item.get("link", "")
                if "youtube.com/watch" in link or "youtu.be" in link:
                    sources.append(
                        _make_source(
                            title_=item.get("title", ""),
                            url=link,
                            snippet=item.get("snippet", ""),
                            source_type="YouTube Video",
                        )
                    )
        except Exception as exc:
            errors.append(f"YouTube search failed: {exc}. YouTube sources unavailable.")

    return {
        "mode": "live",
        "sources": sources,
        "errors": errors,
        "notice": None,
    }


def _guess_type(url: str) -> str:
    if "youtube.com" in url or "youtu.be" in url:
        return "YouTube Video"
    if any(d in url for d in ["docs.", "developer.", "mdn.", "w3schools.", "wikipedia."]):
        return "Documentation / Reference"
    if any(d in url for d in ["book.", "oreilly.", "manning.", "packt.", "amazon."]):
        return "Book"
    return "Website"


def _make_source(title_: str, url: str, snippet: str, source_type: str) -> dict:
    return {
        "title": title_,
        "type": source_type,
        "url": url,
        "relevance_note": snippet[:200] if snippet else "Relevant resource for the lesson topic.",
    }


# ---------------------------------------------------------------------------
# Demo / fallback sources
# ---------------------------------------------------------------------------

_DEMO_DATA: dict[str, list[dict]] = {
    "http requests": [
        {
            "title": "HTTP | MDN Web Docs",
            "type": "Documentation / Reference",
            "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP",
            "relevance_note": "Comprehensive, authoritative reference for HTTP concepts including methods and status codes. Maintained by Mozilla.",
        },
        {
            "title": "HTTP Methods – MDN",
            "type": "Documentation / Reference",
            "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods",
            "relevance_note": "Official definitions of GET, POST, and all other HTTP methods with usage guidance.",
        },
        {
            "title": "HTTP Status Codes – MDN",
            "type": "Documentation / Reference",
            "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Status",
            "relevance_note": "Authoritative list of all HTTP status codes including 2xx, 4xx, and 5xx categories.",
        },
        {
            "title": "HTTP Crash Course – Traversy Media (YouTube)",
            "type": "YouTube Video",
            "url": "https://www.youtube.com/watch?v=iYM2zFP3Zn0",
            "relevance_note": "Practical video covering HTTP fundamentals, request/response cycle, methods, and status codes.",
        },
        {
            "title": "RFC 9110: HTTP Semantics",
            "type": "Website",
            "url": "https://www.rfc-editor.org/rfc/rfc9110",
            "relevance_note": "The authoritative IETF specification defining HTTP/1.1 semantics and status codes.",
        },
        {
            "title": "HTTP – Wikipedia",
            "type": "Website",
            "url": "https://en.wikipedia.org/wiki/HTTP",
            "relevance_note": "Good overview of HTTP history, design, and key concepts for background context.",
        },
    ],
    "git version control": [
        {
            "title": "Pro Git Book (free online) – Scott Chacon & Ben Straub",
            "type": "Book",
            "url": "https://git-scm.com/book/en/v2",
            "relevance_note": "The definitive free reference for Git, covering everything from basics to advanced internals.",
        },
        {
            "title": "Git Documentation – git-scm.com",
            "type": "Documentation / Reference",
            "url": "https://git-scm.com/docs",
            "relevance_note": "Official Git command reference with examples; authoritative source for all git commands.",
        },
        {
            "title": "GitHub Git Guides",
            "type": "Website",
            "url": "https://github.com/git-guides",
            "relevance_note": "Practical, beginner-friendly guides for common Git workflows from GitHub.",
        },
        {
            "title": "Git and GitHub for Beginners – freeCodeCamp (YouTube)",
            "type": "YouTube Video",
            "url": "https://www.youtube.com/watch?v=RGOj5yH7evk",
            "relevance_note": "Popular beginner tutorial covering git init, commit, branch, merge, and GitHub remotes. Over 4 million views.",
        },
        {
            "title": "Learn Git Branching (interactive)",
            "type": "Website",
            "url": "https://learngitbranching.js.org/",
            "relevance_note": "Visual, interactive sandbox for practising branching and merging — excellent for self-study activities.",
        },
    ],
}

_GENERIC_DEMO = [
    {
        "title": "Wikipedia — {topic}",
        "type": "Website",
        "url": "https://en.wikipedia.org/wiki/{slug}",
        "relevance_note": "Encyclopedia overview providing background context and links to primary sources.",
    },
    {
        "title": "MDN Web Docs",
        "type": "Documentation / Reference",
        "url": "https://developer.mozilla.org/",
        "relevance_note": "High-quality technical documentation relevant to web and software topics.",
    },
    {
        "title": "Khan Academy",
        "type": "Website",
        "url": "https://www.khanacademy.org/",
        "relevance_note": "Free educational content with structured exercises — useful for learner activities.",
    },
]


def _demo_sources(title: str, objective: str) -> dict[str, Any]:
    key_text = f"{title} {objective}".lower()

    # Try known demo datasets first
    for key, sources in _DEMO_DATA.items():
        if any(word in key_text for word in key.split()):
            return {
                "mode": "demo",
                "sources": sources,
                "errors": [],
                "notice": (
                    "⚠️ DEMO MODE: Google Custom Search keys are not configured. "
                    "These sources are curated examples selected for the lesson topic — "
                    "they are real, verifiable sources but were NOT retrieved by a live search."
                ),
            }

    # Generic fallback
    slug = re.sub(r"\s+", "_", title.strip())
    generic = [
        {
            **s,
            "title": s["title"].replace("{topic}", title),
            "url": s["url"].replace("{slug}", slug),
        }
        for s in _GENERIC_DEMO
    ]
    return {
        "mode": "demo",
        "sources": generic,
        "errors": ["No pre-curated sources for this topic. Showing generic educational references."],
        "notice": (
            "⚠️ DEMO MODE: Google Custom Search keys are not configured. "
            "These are generic educational references — not topic-specific live results. "
            "Add GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID in .env for live research."
        ),
    }


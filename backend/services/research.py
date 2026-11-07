"""
Research service.

Strategy:
  1. If GOOGLE_CSE_API_KEY + GOOGLE_CSE_ID are set → live search via Google Custom Search API.
  2. Otherwise → DEMO MODE: return clearly-labelled curated sources so the app
     is still fully usable without API keys. Demo mode is announced in every
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
    """Query Google Custom Search for books, authoritative websites, and YouTube videos."""
    query = f"{title} {objective} official documentation tutorial"
    book_query = f"{title} book O'Reilly Manning Packt"
    yt_query = f"{title} {objective} site:youtube.com"

    sources: list[dict] = []
    errors: list[str] = []
    categories_found = {"Documentation / Reference": 0, "Book": 0, "YouTube Video": 0, "Website": 0}

    async with httpx.AsyncClient(timeout=15) as client:
        # --- Web documentation sources ---
        try:
            resp = await client.get(
                SEARCH_BASE,
                params={
                    "key": api_key,
                    "cx": cse_id,
                    "q": query,
                    "num": 4,
                },
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            for item in items:
                stype = _guess_type(item.get("link", ""))
                categories_found[stype] = categories_found.get(stype, 0) + 1
                sources.append(
                    _make_source(
                        title_=item.get("title", ""),
                        url=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                        source_type=stype,
                    )
                )
        except Exception as exc:
            errors.append(f"Web documentation search failed: {exc}")

        # --- Book sources ---
        try:
            resp = await client.get(
                SEARCH_BASE,
                params={
                    "key": api_key,
                    "cx": cse_id,
                    "q": book_query,
                    "num": 3,
                },
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            book_added = False
            for item in items:
                link = item.get("link", "")
                if any(k in link.lower() for k in ["book", "oreilly", "manning", "packt", "springer", "amazon"]):
                    sources.append(
                        _make_source(
                            title_=item.get("title", ""),
                            url=link,
                            snippet=item.get("snippet", ""),
                            source_type="Book",
                        )
                    )
                    categories_found["Book"] = categories_found.get("Book", 0) + 1
                    book_added = True
            if not book_added:
                errors.append("Book sources: No authoritative book volumes returned by search; continuing with web and video sources.")
        except Exception as exc:
            errors.append(f"Book search failed: {exc}. Continuing with available sources.")

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
            yt_added = False
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
                    categories_found["YouTube Video"] = categories_found.get("YouTube Video", 0) + 1
                    yt_added = True
            if not yt_added:
                errors.append("YouTube video sources: No verified video links returned by search; continuing with text sources.")
        except Exception as exc:
            errors.append(f"YouTube search failed: {exc}. YouTube sources unavailable.")

    return {
        "mode": "live",
        "sources": sources,
        "errors": errors,
        "notice": None,
    }


def _guess_type(url: str) -> str:
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "YouTube Video"
    if any(d in url_lower for d in ["book", "oreilly.", "manning.", "packt.", "springer."]):
        return "Book"
    if any(d in url_lower for d in ["docs.", "developer.", "mdn.", "w3schools.", "rfc-editor.", "git-scm."]):
        return "Documentation / Reference"
    return "Website"


def _make_source(title_: str, url: str, snippet: str, source_type: str) -> dict:
    return {
        "title": title_,
        "type": source_type,
        "url": url,
        "relevance_note": snippet[:220].strip() if snippet else "Relevant authoritative resource for the lesson topic.",
    }


# ---------------------------------------------------------------------------
# Demo / fallback sources (Curated, Real, Verifiable Resources)
# ---------------------------------------------------------------------------

_DEMO_DATA: dict[str, list[dict]] = {
    "http requests": [
        {
            "title": "HTTP: The Definitive Guide – David Gourley & Brian Totty",
            "type": "Book",
            "url": "https://www.oreilly.com/library/view/http-the-definitive/1565925092/",
            "relevance_note": "Comprehensive O'Reilly reference book covering HTTP architecture, request-response transactions, methods (GET/POST), and 2xx/4xx/5xx status codes.",
        },
        {
            "title": "HTTP | MDN Web Docs",
            "type": "Documentation / Reference",
            "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP",
            "relevance_note": "Authoritative MDN technical documentation on Hypertext Transfer Protocol fundamentals and client-server communication.",
        },
        {
            "title": "HTTP Methods – MDN Web Docs",
            "type": "Documentation / Reference",
            "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods",
            "relevance_note": "Official specifications for GET, POST, and other HTTP methods, defining idempotency and payload body semantics.",
        },
        {
            "title": "HTTP Status Codes – MDN Web Docs",
            "type": "Documentation / Reference",
            "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Status",
            "relevance_note": "Authoritative directory of HTTP response status codes categorized by 1xx, 2xx, 3xx, 4xx, and 5xx series.",
        },
        {
            "title": "RFC 9110: HTTP Semantics (IETF Standards Track)",
            "type": "Website",
            "url": "https://www.rfc-editor.org/rfc/rfc9110",
            "relevance_note": "The primary Internet Engineering Task Force (IETF) specification defining modern HTTP semantics and response status categories.",
        },
        {
            "title": "HTTP Crash Course & Exploration – Traversy Media",
            "type": "YouTube Video",
            "url": "https://www.youtube.com/watch?v=iYM2zFP3Zn0",
            "relevance_note": "Practical video walkthrough demonstrating request-response cycles, inspecting headers, GET vs POST payloads, and status codes in action.",
        },
    ],
    "git version control": [
        {
            "title": "Pro Git (Official Free Book) – Scott Chacon & Ben Straub",
            "type": "Book",
            "url": "https://git-scm.com/book/en/v2",
            "relevance_note": "The official open-source Git book detailing repository initialization, snapshots, branching models, and merging workflows.",
        },
        {
            "title": "Git Reference Manual – git-scm.com",
            "type": "Documentation / Reference",
            "url": "https://git-scm.com/docs",
            "relevance_note": "Authoritative command reference documentation for git init, git add, git commit, git branch, and git merge.",
        },
        {
            "title": "GitHub Git Guides",
            "type": "Website",
            "url": "https://github.com/git-guides",
            "relevance_note": "Practical visual tutorials and conceptual explanations for everyday distributed version control workflows.",
        },
        {
            "title": "Learn Git Branching (Interactive Sandbox)",
            "type": "Website",
            "url": "https://learngitbranching.js.org/",
            "relevance_note": "Interactive terminal and visual commit tree simulation designed for mastering branch management and merges.",
        },
        {
            "title": "Git and GitHub for Beginners – Crash Course (freeCodeCamp)",
            "type": "YouTube Video",
            "url": "https://www.youtube.com/watch?v=RGOj5yH7evk",
            "relevance_note": "Comprehensive beginner video tutorial covering local repository setup, staging, commits, branches, and merging with clear terminal demonstrations.",
        },
    ],
}

_GENERIC_DEMO = [
    {
        "title": "Wikipedia: {topic}",
        "type": "Website",
        "url": "https://en.wikipedia.org/wiki/{slug}",
        "relevance_note": "Encyclopedia overview providing background context and citations to primary literature.",
    },
    {
        "title": "MDN Web Docs Documentation",
        "type": "Documentation / Reference",
        "url": "https://developer.mozilla.org/",
        "relevance_note": "Authoritative technical documentation and standards for software engineering and web technologies.",
    },
    {
        "title": "Khan Academy Educational Library",
        "type": "Website",
        "url": "https://www.khanacademy.org/",
        "relevance_note": "Structured learning modules with conceptual breakdowns and practice exercises.",
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
                    "⚠️ DEMO RESEARCH MODE: Google Custom Search API keys are not configured in .env. "
                    "These sources are curated real-world references (Book, Documentation, Website, YouTube) "
                    "specifically selected for this topic. They are real and verifiable, but were not gathered via a live search query."
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
        "errors": ["No pre-curated demo dataset for this topic. Showing generic authoritative references."],
        "notice": (
            "⚠️ DEMO RESEARCH MODE: Google Custom Search keys are not configured. "
            "Showing generic educational references. Add GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID in .env for live web research."
        ),
    }

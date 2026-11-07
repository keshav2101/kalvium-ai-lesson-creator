"""
Lesson generation service.

Uses Google Gemini to draft a structured 45-minute lesson from:
  - title, objective
  - research sources collected by research.py

Falls back to rich demo lessons if no Gemini key is configured.
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

async def generate_lesson(
    title: str,
    objective: str,
    sources: list[dict],
    research_mode: str,
) -> dict[str, Any]:
    model = _get_model()
    if model:
        return await _live_generate(model, title, objective, sources, research_mode)
    return _demo_lesson(title, objective, sources, research_mode)


# ---------------------------------------------------------------------------
# Live generation
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = textwrap.dedent("""\
You are an expert instructional designer. Your task is to create a high-quality,
structured lesson in Markdown format.

Rules:
1. The total lesson time must be exactly 45 minutes. Include a time breakdown table.
2. Structure: Learning Objective → Time Breakdown → Introduction → Core Content
   (with subsections) → Practical Application → Learner Activities → Knowledge Check
   (with answer key) → Summary → References.
3. Include explanations, concrete examples, and practical applications.
4. Knowledge check: at least 3 questions with a full answer key.
5. Cite sources inline (e.g. [MDN]) and list all references at the end using the
   provided sources. Do NOT invent sources, URLs, or quotations.
6. If a source is a YouTube video, mention it in the supplementary resources section.
7. Write for both self-study and instructor-led delivery.
8. Return ONLY valid JSON — no markdown fences, no commentary outside the JSON.

JSON schema:
{
  "content": "<full lesson in Markdown>",
  "time_breakdown": [{"section": "<name>", "minutes": <int>}],
  "total_minutes": <int>,
  "generation_mode": "live"
}
""")


async def _live_generate(
    model,
    title: str,
    objective: str,
    sources: list[dict],
    research_mode: str,
) -> dict[str, Any]:
    source_list = "\n".join(
        f"- [{s['type']}] {s['title']} — {s['url']}\n  Note: {s['relevance_note']}"
        for s in sources
    )

    user_prompt = textwrap.dedent(f"""\
    Lesson title: {title}
    Learning objective: {objective}
    Research mode: {research_mode}

    Available sources (use these; do not invent others):
    {source_list}

    Create a complete 45-minute lesson following the system rules.
    """)

    try:
        response = model.generate_content(
            [_SYSTEM_PROMPT, user_prompt],
            generation_config={
                "temperature": 0.4,
                "max_output_tokens": 8192,
            },
        )
        raw = response.text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            raw = raw.rsplit("```", 1)[0]
        data = json.loads(raw)
        data["generation_mode"] = "live"
        return data
    except Exception as exc:
        raise RuntimeError(f"Gemini lesson generation failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Demo lesson content strings (defined before the dict that uses them)
# ---------------------------------------------------------------------------

_HTTP_LESSON_CONTENT = textwrap.dedent("""\
# HTTP Requests and Responses

> **⚠️ DEMO MODE** — Generated with built-in sample content because no Gemini API key is configured.
> Add `GEMINI_API_KEY` to `.env` for AI-generated lessons.

## Learning Objective
Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx HTTP response status categories.

---

## ⏱️ Time Breakdown

| Section | Time |
|---|---|
| Introduction | 5 min |
| Core Content: HTTP Basics | 10 min |
| Core Content: Methods (GET & POST) | 10 min |
| Core Content: Status Codes | 8 min |
| Practical Application | 5 min |
| Knowledge Check | 5 min |
| Summary & Wrap-up | 2 min |
| **Total** | **45 min** |

---

## 1. Introduction (5 min)

Every time you open a website, your browser has a conversation with a server. That conversation follows a strict protocol: **HTTP** (Hypertext Transfer Protocol). Understanding how HTTP works is foundational to web development, API design, and debugging.

**Opening question for learners:** *What do you think happens between your browser and Google's servers when you search for something?*

---

## 2. Core Content

### 2.1 The HTTP Request–Response Cycle (10 min)

HTTP is a **request–response protocol**:
1. A **client** (browser, mobile app, curl) sends a **request** to a server.
2. The **server** processes the request and returns a **response**.

**Anatomy of an HTTP Request:**
```
GET /search?q=http HTTP/1.1
Host: developer.mozilla.org
Accept: text/html
```

| Part | Example | Purpose |
|---|---|---|
| Method | `GET` | What action to perform |
| Path | `/search?q=http` | Which resource |
| HTTP Version | `HTTP/1.1` | Protocol version |
| Headers | `Host:`, `Accept:` | Metadata for the server |
| Body | (empty for GET) | Data payload (used by POST) |

**Anatomy of an HTTP Response:**
```
HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 4821

<!DOCTYPE html>...
```

> 📖 **Source:** [HTTP Overview — MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview)

---

### 2.2 GET vs POST Methods (10 min)

HTTP defines several **methods** (also called verbs). The two most common are GET and POST.

#### GET
- **Purpose:** Retrieve a resource. No side effects — the server state does not change.
- **Data location:** Parameters are appended to the URL as a **query string**.
- **Idempotent:** Yes — repeating the same GET produces the same result.
- **Example:**
  ```
  GET /users?id=42 HTTP/1.1
  Host: api.example.com
  ```

#### POST
- **Purpose:** Send data to the server to create or update a resource.
- **Data location:** Data is in the **request body** (not visible in the URL).
- **Idempotent:** No — repeating the same POST may create duplicates.
- **Example:**
  ```
  POST /users HTTP/1.1
  Host: api.example.com
  Content-Type: application/json

  {"name": "Alice", "email": "alice@example.com"}
  ```

**GET vs POST comparison:**

| Feature | GET | POST |
|---|---|---|
| Data location | URL query string | Request body |
| Visibility | Visible in URL/logs | Hidden in body |
| Bookmarkable | Yes | No |
| Idempotent | Yes | No |
| Use case | Read/search | Create/submit |
| Body | None | Required |

> 📖 **Source:** [HTTP Methods — MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods)

---

### 2.3 HTTP Status Codes (8 min)

Every HTTP response includes a **3-digit status code** that tells the client what happened.

#### 2xx — Success
The request was received, understood, and accepted.

| Code | Name | Meaning |
|---|---|---|
| 200 | OK | Standard success. Response body contains the result. |
| 201 | Created | Resource successfully created (e.g., after a POST). |
| 204 | No Content | Success, but no body to return (e.g., after a DELETE). |

#### 4xx — Client Error
The client made an error in the request.

| Code | Name | Meaning |
|---|---|---|
| 400 | Bad Request | Server couldn't understand the request (malformed syntax). |
| 401 | Unauthorized | Authentication required or failed. |
| 403 | Forbidden | Authenticated but not permitted to access the resource. |
| 404 | Not Found | Resource doesn't exist at the given URL. |
| 422 | Unprocessable Entity | Request is well-formed but contains invalid data. |

#### 5xx — Server Error
The server failed to fulfil a valid request.

| Code | Name | Meaning |
|---|---|---|
| 500 | Internal Server Error | Generic catch-all; something went wrong on the server. |
| 502 | Bad Gateway | Upstream server sent an invalid response. |
| 503 | Service Unavailable | Server is overloaded or down for maintenance. |

> 📖 **Source:** [HTTP Status Codes — MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
> 📖 **Source:** [RFC 9110 — IETF](https://www.rfc-editor.org/rfc/rfc9110)

**Memory tip:** Think of the first digit: **2** = done, **4** = your fault, **5** = our fault.

---

## 3. Practical Application (5 min)

### Try it yourself — curl
Open a terminal and run:
```bash
# GET request — fetch a JSON placeholder
curl -v https://jsonplaceholder.typicode.com/posts/1

# POST request — create a new post
curl -X POST https://jsonplaceholder.typicode.com/posts \\
  -H "Content-Type: application/json" \\
  -d '{"title":"My Post","body":"Hello","userId":1}'
```

Inspect the **status code** and **response headers** in the output (lines starting with `<`).

### Browser DevTools
1. Open Chrome/Firefox DevTools → **Network** tab.
2. Navigate to any website.
3. Click a request → inspect **Headers** (method, URL) and **Response** (status code, body).

---

## 4. Learner Activities (included in core time)

**Activity A — Classification exercise:**
Label each scenario with the correct status code:
1. You type a URL that doesn't exist. → ___
2. You submit a login form with correct credentials and are logged in. → ___
3. The database server crashes while handling your request. → ___
4. You try to access an admin page without logging in. → ___
5. You create a new account successfully. → ___

*(Answers in Knowledge Check below)*

**Activity B — Identify GET vs POST:**
For each action, say whether GET or POST is more appropriate and why:
1. Searching for products on an e-commerce site.
2. Submitting a contact form.
3. Loading a user's profile page.
4. Uploading a file.

**Activity B Answers:**
1. GET — read-only search with no side effects; parameters go in the URL.
2. POST — sends user data to the server; not idempotent.
3. GET — retrieves existing data; safe and cacheable.
4. POST — sends file data in request body; modifies server state.

---

## 5. Knowledge Check (5 min)

**Question 1:** What is the key difference between a GET and POST request?

**Question 2:** A user visits a page and sees `403 Forbidden`. What does this mean, and how is it different from `401 Unauthorized`?

**Question 3:** An API returns `201 Created` after a form submission. What does this tell you about what happened?

**Question 4 (Activity A answers):**
1. `404 Not Found`
2. `200 OK`
3. `500 Internal Server Error`
4. `401 Unauthorized` (or `403 Forbidden` if already logged in but lacks permission)
5. `201 Created`

---

### ✅ Answer Key

**Q1:** GET retrieves data without modifying server state; parameters go in the URL. POST sends data in the request body to create or modify a resource; it may change server state and is not idempotent.

**Q2:** `403 Forbidden` means the server knows who you are (authenticated) but refuses access. `401 Unauthorized` means authentication is missing or failed — you haven't proved your identity yet.

**Q3:** The server successfully created a new resource as a result of the request. The response body typically contains the created resource or its location.

---

## 6. Supplementary Resources

- 🎥 **HTTP Crash Course — Traversy Media:** https://www.youtube.com/watch?v=iYM2zFP3Zn0
  *(27 min video — excellent visual walkthrough of requests, responses, methods, and status codes)*

---

## 7. Summary (2 min)

| Concept | Key point |
|---|---|
| HTTP | Request–response protocol for client–server communication |
| GET | Retrieve data; parameters in URL; idempotent |
| POST | Send data; parameters in body; not idempotent |
| 2xx | Success (200 OK, 201 Created, 204 No Content) |
| 4xx | Client error (400, 401, 403, 404, 422) |
| 5xx | Server error (500, 502, 503) |

---

## 8. References

1. HTTP: The Definitive Guide — David Gourley & Brian Totty (O'Reilly): https://www.oreilly.com/library/view/http-the-definitive/1565925092/
2. MDN Web Docs — HTTP Overview: https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview
3. MDN Web Docs — HTTP Methods: https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods
4. MDN Web Docs — HTTP Status Codes: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
5. RFC 9110 — HTTP Semantics (IETF): https://www.rfc-editor.org/rfc/rfc9110
6. Traversy Media — HTTP Crash Course (YouTube): https://www.youtube.com/watch?v=iYM2zFP3Zn0
7. Wikipedia — HTTP: https://en.wikipedia.org/wiki/HTTP
""")

_GIT_LESSON_CONTENT = textwrap.dedent("""\
# Git Version Control Fundamentals

> **⚠️ DEMO MODE** — Generated with built-in sample content because no Gemini API key is configured.
> Add `GEMINI_API_KEY` to `.env` for AI-generated lessons.

## Learning Objective
Use core Git commands (init, add, commit, branch, merge) to track changes and manage branches in a local repository.

---

## ⏱️ Time Breakdown

| Section | Time |
|---|---|
| Introduction | 5 min |
| Core Content: What is Git? | 7 min |
| Core Content: Essential Commands | 10 min |
| Core Content: Branching & Merging | 10 min |
| Practical Application | 7 min |
| Knowledge Check | 4 min |
| Summary & Wrap-up | 2 min |
| **Total** | **45 min** |

---

## 1. Introduction (5 min)

Imagine writing a 50-page report and accidentally deleting half of it — with no Undo. Version control prevents exactly that. **Git** is the world's most widely used version control system, underpinning platforms like GitHub, GitLab, and Bitbucket.

**Opening question:** *Have you ever accidentally overwritten a file and wished you could go back?*

---

## 2. What is Git? (7 min)

Git is a **distributed version control system** (DVCS):
- Every developer has a **full copy** of the repository.
- Changes are tracked as **snapshots** (not diffs) over time.
- It works **offline** — you can commit, branch, and view history without internet.

**Key concepts:**

| Term | Definition |
|---|---|
| Repository (repo) | The folder tracked by Git + its entire history |
| Commit | A saved snapshot of the project at a point in time |
| Branch | An independent line of development |
| Merge | Combining changes from two branches |
| HEAD | Pointer to the currently checked-out commit/branch |

> 📖 **Source:** [Pro Git Book — Chapter 1](https://git-scm.com/book/en/v2/Getting-Started-What-is-Git%3F)

---

## 3. Essential Commands (10 min)

### Setting up
```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### Starting a repository
```bash
git init my-project    # Create a new repo
cd my-project
```

### The staging area workflow
```
Working Directory → (git add) → Staging Area → (git commit) → Repository
```

```bash
git status             # See what's changed
git add README.md      # Stage a specific file
git add .              # Stage all changes
git commit -m "Add README"  # Save a snapshot
git log --oneline      # View commit history
```

> 📖 **Source:** [Git Documentation — git-scm.com](https://git-scm.com/docs)

### Checking and undoing
```bash
git diff               # See unstaged changes
git restore <file>     # Discard working-directory changes
git restore --staged <file>  # Unstage a file
```

---

## 4. Branching & Merging (10 min)

Branches let you develop features or fix bugs in isolation.

```bash
git branch             # List branches
git branch feature-x   # Create a new branch
git checkout feature-x # Switch to it
# (shortcut: git checkout -b feature-x)

# Make changes and commit on feature-x...
git add .
git commit -m "Add feature X"

# Merge back into main
git checkout main
git merge feature-x    # Fast-forward or creates a merge commit
```

**Visualising branches:**
```
main:      A---B---C
                    \\
feature-x:           D---E
                          -> merge into main: A---B---C---M
```

**Merge conflicts** happen when the same lines were changed on both branches. Git marks conflicts like:
```
<<<<<<< HEAD
Your version
=======
Their version
>>>>>>> feature-x
```
Edit the file to resolve, then `git add` and `git commit`.

> 📖 **Source:** [Pro Git — Branching](https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell)
> 🎥 **Git and GitHub for Beginners — freeCodeCamp:** https://www.youtube.com/watch?v=RGOj5yH7evk

---

## 5. Practical Application (7 min)

**Hands-on exercise:**
```bash
# 1. Create and initialise a repo
git init demo-repo && cd demo-repo

# 2. Create a file, stage, and commit
echo "# My Project" > README.md
git add README.md
git commit -m "Initial commit"

# 3. Create a branch and make changes
git checkout -b add-info
echo "More info here." >> README.md
git add README.md
git commit -m "Add more info"

# 4. Merge back to main
git checkout main
git merge add-info

# 5. View the full history
git log --oneline --graph --all
```

Expected output for step 5:
```
*   abc1234 (HEAD -> main) Merge branch 'add-info'
|\\
| * def5678 (add-info) Add more info
|/
* ghi9012 Initial commit
```

*(Note: your commit hashes will differ from the examples above.)*

---

## 6. Knowledge Check (4 min)

**Question 1:** What command do you use to stage all changed files?

**Question 2:** What single command creates a new branch called `feature-name` AND switches to it?

**Question 3:** After merging `feature-x` into `main`, you see conflict markers. What are the three steps to resolve the conflict?

**Question 4:** What is the difference between `git restore <file>` and `git restore --staged <file>`?

---

### ✅ Answer Key

**Q1:** `git add .`

**Q2:** `git checkout -b feature-name`

**Q3:** (1) Edit the file to remove conflict markers and keep the correct content. (2) `git add <file>`. (3) `git commit` (Git auto-generates the merge commit message).

**Q4:** `git restore <file>` discards **working-directory** changes (un-edits the file). `git restore --staged <file>` moves a file from the staging area back to the working directory (un-stages it) without changing the file content.

---

## 7. Supplementary Resources

- 🎥 **Git and GitHub for Beginners — freeCodeCamp (YouTube):** https://www.youtube.com/watch?v=RGOj5yH7evk *(1 hr overview)*
- 🌐 **Learn Git Branching (interactive):** https://learngitbranching.js.org/

---

## 8. Summary (2 min)

| Command | What it does |
|---|---|
| `git init` | Create a new repository |
| `git add` | Stage changes |
| `git commit` | Save a snapshot |
| `git branch` | List / create branches |
| `git checkout` | Switch branches or restore files |
| `git merge` | Combine branches |
| `git log` | View commit history |

---

## 9. References

1. Pro Git Book (free) — Scott Chacon & Ben Straub: https://git-scm.com/book/en/v2
2. Git Official Documentation: https://git-scm.com/docs
3. GitHub Git Guides: https://github.com/git-guides
4. Git and GitHub for Beginners — freeCodeCamp (YouTube): https://www.youtube.com/watch?v=RGOj5yH7evk
5. Learn Git Branching (interactive): https://learngitbranching.js.org/
""")


# ---------------------------------------------------------------------------
# Demo lessons registry
# ---------------------------------------------------------------------------

_DEMO_LESSONS: dict[str, dict] = {
    "http": {
        "content": _HTTP_LESSON_CONTENT,
        "time_breakdown": [
            {"section": "Introduction", "minutes": 5},
            {"section": "Core Content: HTTP Basics", "minutes": 10},
            {"section": "Core Content: Methods (GET & POST)", "minutes": 10},
            {"section": "Core Content: Status Codes", "minutes": 8},
            {"section": "Practical Application", "minutes": 5},
            {"section": "Knowledge Check", "minutes": 5},
            {"section": "Summary & Wrap-up", "minutes": 2},
        ],
        "total_minutes": 45,
        "generation_mode": "demo",
    },
    "git": {
        "content": _GIT_LESSON_CONTENT,
        "time_breakdown": [
            {"section": "Introduction", "minutes": 5},
            {"section": "Core Content: What is Git?", "minutes": 7},
            {"section": "Core Content: Essential Commands", "minutes": 10},
            {"section": "Core Content: Branching & Merging", "minutes": 10},
            {"section": "Practical Application", "minutes": 7},
            {"section": "Knowledge Check", "minutes": 4},
            {"section": "Summary & Wrap-up", "minutes": 2},
        ],
        "total_minutes": 45,
        "generation_mode": "demo",
    },
}


def _demo_lesson(
    title: str,
    objective: str,
    sources: list[dict],
    research_mode: str,
) -> dict[str, Any]:
    key = title.lower()
    if "http" in key or "request" in key or "response" in key:
        return dict(_DEMO_LESSONS["http"])
    if "git" in key or "version control" in key:
        return dict(_DEMO_LESSONS["git"])

    # Generic template for unknown topics
    source_refs = "\n".join(
        f"{i+1}. [{s['type']}] {s['title']}: {s['url']}"
        for i, s in enumerate(sources)
    )
    content = textwrap.dedent(f"""\
# {title}

> **⚠️ DEMO MODE** — Add `GEMINI_API_KEY` to `.env` for AI-generated content.
> This is a template lesson structure for demonstration.

## Learning Objective
{objective}

---

## ⏱️ Time Breakdown

| Section | Time |
|---|---|
| Introduction | 5 min |
| Core Content | 20 min |
| Practical Application | 10 min |
| Knowledge Check | 7 min |
| Summary | 3 min |
| **Total** | **45 min** |

---

## 1. Introduction (5 min)
*(Instructor: introduce the topic and connect it to learners' prior knowledge.)*

This lesson covers: **{title}**

By the end of this lesson you will be able to: {objective}

---

## 2. Core Content (20 min)

### Key Concepts

- **Concept 1:** Description and example.
- **Concept 2:** Description and example.
- **Concept 3:** Description and example.

---

## 3. Practical Application (10 min)

**Exercise:** Apply the concepts to a real scenario.

---

## 4. Knowledge Check (7 min)

1. Question 1 about the core concepts?
2. Question 2 about the core concepts?
3. Question 3 about the core concepts?

### Answer Key
1. Answer 1
2. Answer 2
3. Answer 3

---

## 5. Summary (3 min)

Recap the key points covered in this lesson.

---

## References

{source_refs}
""")
    return {
        "content": content,
        "time_breakdown": [
            {"section": "Introduction", "minutes": 5},
            {"section": "Core Content", "minutes": 20},
            {"section": "Practical Application", "minutes": 10},
            {"section": "Knowledge Check", "minutes": 7},
            {"section": "Summary", "minutes": 3},
        ],
        "total_minutes": 45,
        "generation_mode": "demo",
    }

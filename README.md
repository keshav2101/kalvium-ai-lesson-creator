# AI-Powered Lesson Creation Tool

An AI-powered instructional design platform for instructors to research authoritative sources, draft structured 45-minute lessons, run two independent quality-control audits, edit and apply recommendations non-destructively, preview, and export comprehensive lesson documents.

Built for the **AI Research Intern hiring task**.

---

## 🚀 Quick Start & Setup Instructions

### Prerequisites
- **Node.js** v18+ and **npm** v9+ (tested on Node v25 / npm v11)
- **Python** 3.10+ and **pip** (tested on Python 3.11)

### 1. Installation

```bash
# Clone or navigate to the repository
cd kalvium-ai

# Install backend dependencies
cd backend && pip install -r requirements.txt && cd ..

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### 2. Configuration (Optional)

The tool runs **completely locally in Demo Mode out of the box** with zero configuration required.

To enable live Google Gemini AI and live Google Search:
```bash
cp .env.example .env
```
Open `.env` and provide your credentials:
```ini
# Google Gemini API key (Free at https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Google Custom Search API for live web research
# (https://developers.google.com/custom-search/v1/overview)
GOOGLE_CSE_API_KEY=your_google_cse_key_here
GOOGLE_CSE_ID=your_programmable_search_engine_id_here
```

> **Demo Mode Disclosure:** When API keys are not provided, the platform operates in **Demo Mode**. All research references and QC reports are clearly tagged with `⚠️ DEMO MODE` badges and notices. Demo results are curated from real-world authoritative resources and are never presented as live research or independent factual verification.

### 3. Running the Tool

To start both servers with a single command:
```bash
./start.sh
```

Or start the servers manually in separate terminals:
```bash
# Terminal 1: FastAPI Backend (Port 8000)
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Next.js Frontend (Port 3000)
cd frontend && npm run dev
```

Open **[http://localhost:3000](http://localhost:3000)** in your web browser.
Interactive OpenAPI documentation is available at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

---

## 🏛️ Architecture & System Design

```
[ Instructor Inputs ]
  ├── Lesson Title (Required, validated >= 5 chars)
  └── Learning Objective (Required, validated >= 10 chars)
         │
         ▼
[ Step 1: Research Service (backend/services/research.py) ]
  ├── Live Search: Queries Google Custom Search for Books, Web Docs, and YouTube videos
  └── Demo Mode: Curated authoritative sources (Book, Reference, Website, YouTube)
  └── Categorization & graceful fallback when a source category is unavailable
         │
         ▼
[ Step 2: Lesson Drafting Service (backend/services/lesson_gen.py) ]
  ├── Live Generation: Google Gemini 1.5 Flash (structured prompt with 45-min budget)
  └── Demo Mode: Full-length structured lessons with explanations & answer keys
  └── Time Breakdown enforcement: parts strictly sum to <= 45 minutes
         │
         ▼
[ Step 3: Dual Independent QC Audits (backend/services/qc.py) ]
  ├── Report A: Research & Factual Accuracy (claims, source validity, gaps, contradictions)
  └── Report B: Instructional Quality (objective alignment, pedagogy, learner support)
  └── Actionable recommendations with target sections and suggested text additions
         │
         ▼
[ Local Disk Persistence (backend/services/persistence.py) ]
  Saved to backend/data/lessons/{id}.json after every step, edit, and recommendation
         │
         ▼
[ Review, Non-Destructive Editing & Retry Controls (frontend/app/page.tsx) ]
  ├── Markdown preview & live text editor
  ├── Surgical recommendation application (inserts without clobbering other edits)
  ├── Step-level and full retry controls for failed steps
  └── Re-run quality checks on updated drafts
         │
         ▼
[ Export & Print Preview (backend/routes/export.py) ]
  ├── Single-click download as complete Markdown (.md)
  └── Print / Save to PDF view (clean print-specific stylesheet)
```

---

## 📋 Supported Sample Lessons

The platform includes one-click demonstration loaders for both required sample lessons:

1. **HTTP Requests and Responses**
   - **Learning Objective:** Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.
   - **Sources:** *HTTP: The Definitive Guide* (O'Reilly Book), MDN HTTP Overview, MDN HTTP Methods, MDN HTTP Status Codes, RFC 9110 (IETF), and Traversy Media HTTP Crash Course (YouTube).
   - **Activities & Practice:** Hands-on `curl` commands, browser DevTools inspection, status classification exercises, and GET vs POST decision exercises.
   - **Assessment:** 4 multi-part knowledge check questions with complete answer keys.

2. **Git Version Control Fundamentals**
   - **Learning Objective:** Use core Git commands (init, add, commit, branch, merge) to track changes and manage branches in a local repository.
   - **Sources:** *Pro Git* (Official Free Book), git-scm.com documentation, GitHub Git Guides, Learn Git Branching sandbox, and freeCodeCamp Git crash course (YouTube).
   - **Activities & Practice:** Local repository initialization, staging area workflow, branching, commit log inspection, and merge conflict resolution.
   - **Assessment:** 4 conceptual and practical check questions with complete answer keys.

---

## 🔍 Quality Control & Non-Destructive Recommendation Workflow

The platform provides two strictly separate QC evaluations:

### Report A: Research and Factual Accuracy
- Evaluates factual claims against cited references.
- Assesses source reliability, relevance, and coverage gaps.
- Discloses the scope of review (internal consistency check against source references; does not claim external live endpoint polling).

### Report B: Instructional Quality
- Evaluates pedagogical alignment to the stated learning objective.
- Checks structural flow, concrete examples, and practical activities.
- Identifies missing learner support (e.g. beginner prerequisites, edge-case explanations).

### Non-Destructive Recommendation Application
Unlike tools that overwrite entire documents or merely mark checklists, this tool:
1. Each recommendation contains a `target_section` and a concrete `suggested_text` Markdown snippet.
2. Clicking **"Apply to Lesson"** surgically splices the suggested text into the target section of the active draft.
3. **All unrelated manual edits made by the instructor are 100% preserved**.
4. Instructors can also click **"Undo"** to cleanly remove an applied addition, or **"Mark Done"** if they addressed the suggestion with custom wording.
5. Instructors can click **"Re-evaluate Current Draft"** to trigger a fresh QC audit against their modified lesson text.

---

## 🧪 Demonstration & Testing Walkthrough

Follow these steps to exercise the full workflow in your browser:

1. **Input & Generation:**
   - Open **http://localhost:3000**.
   - Click the **"HTTP Requests and Responses"** quick example button.
   - Click **"✨ Generate 45-Min Lesson"**.
   - Observe the progressive generation indicator (Research → Drafting → Dual QC).

2. **Inspect Research Sources:**
   - Click the **"🔍 Research Sources"** tab.
   - Verify sources across all categories: **Book**, **Documentation / Reference**, **Website**, and **YouTube Video**.
   - Confirm each card displays title, type, link, and relevance note.

3. **Inspect Time Breakdown & Lesson:**
   - Review the color-coded time breakdown bar at the top (strictly sums to 45 minutes).
   - Scroll through the rendered lesson to inspect the explanations, tables, hands-on `curl` commands, learner activities, and answer keys.

4. **Edit & Persist:**
   - Switch to **"✏️ Edit Markdown"** mode.
   - Add a custom sentence to Section 1 (e.g. `> 🎯 Note: Ask students to open terminal.`).
   - Click **"Save Changes"** (notice `✓ Saved to disk`).
   - Refresh the browser (**F5** / **Cmd+R**). Re-select the lesson from the sidebar: confirm your custom edit is intact!

5. **Apply QC Recommendation Safely:**
   - Open the **"✅ Quality Checks"** tab.
   - Expand Report A and Report B.
   - On recommendation `R1` (HTTP/2 protocol note targeting Section 2.1), click **"Apply to Lesson"**.
   - Return to the **"📄 Lesson Document"** tab: confirm the protocol note was inserted into Section 2.1, and verify your custom note in Section 1 was **completely preserved**!

6. **Export & Print:**
   - Click **"⬇️ Export Markdown"** in the top-right header to download the complete file.
   - Open the downloaded `.md` file to confirm it contains the finalized lesson, sources appendix, and both QC reports.
   - Click **"🖨️ Print / PDF"** to preview the clean, print-optimized document.

7. **Exercise Sample Lesson 2:**
   - Click the **"Git Version Control Fundamentals"** quick example and generate.
   - Confirm the 45-minute pacing, Git-specific sources (Pro Git book, freeCodeCamp video), and Git QC reports.

---

## 📊 Verification Test Results

All core capabilities were tested and verified against the running FastAPI backend and Next.js frontend:

| Test Area | Verification Performed | Result |
|---|---|---|
| **Input Validation** | Tested empty title/objective and strings `< 5` characters via API and UI | ✅ **PASSED** (HTTP 422 with clear error messages) |
| **Sample Lesson 1** | Generated HTTP lesson; checked all 4 source types, time breakdown, GET/POST, 2xx/4xx/5xx, curl exercise, answer key | ✅ **PASSED** (All sections present; total = 45 min) |
| **Sample Lesson 2** | Generated Git lesson; checked Pro Git book, Git docs, YouTube video, branch/merge exercises, answer key | ✅ **PASSED** (Measurable objective; total = 45 min) |
| **Non-Destructive QC** | Added custom edit to Section 1; applied R1 to Section 2.1; applied I1 (prerequisites); confirmed Section 1 edit untouched | ✅ **PASSED** (Surgical insertion; 0 clobbered edits) |
| **Revert Recommendation** | Reverted R1; verified R1 removed while I1 and Section 1 edit remained | ✅ **PASSED** (Clean removal) |
| **Persistence Across Reloads** | Saved edit, queried `GET /api/lessons/{id}` after disk write; reloaded browser | ✅ **PASSED** (Matches disk state exactly) |
| **Retry Failed Steps** | Called `/api/generate/retry/{id}` with `step="qc"`; verified QC re-evaluated active draft without erasing edits | ✅ **PASSED** (Successful re-evaluation) |
| **Markdown Export** | Downloaded `/api/export/{id}`; verified header, finalized lesson, sources appendix, and both QC reports | ✅ **PASSED** (Complete single-file export) |
| **TypeScript / Build** | Executed `npm run build` on Next.js 14 frontend | ✅ **PASSED** (Compiled cleanly with 0 type errors) |

---

## ⚠️ Known Limitations & Future Enhancements

- **Live Google Search Quotas:** Google Custom Search API free tier provides 100 queries/day. If keys are missing or quotas are exhausted, the app falls back to curated Demo Mode.
- **Diff Comparison View:** The current interface provides side-by-side edit/preview and surgical recommendation insertion. A visual split Git-diff modal could be added in the future.
- **Direct PDF Export:** Users can currently print directly or save as PDF via the browser's print dialog (`Cmd+P`), styled with a dedicated `@media print` stylesheet. Native server-side PDF generation (e.g. WeasyPrint) could be added if system font libraries are installed.

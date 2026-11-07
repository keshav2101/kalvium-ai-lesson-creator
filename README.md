# AI-Powered Lesson Creation Tool

An AI-powered tool for instructors to create, research, draft, review, quality-check, edit, and export structured 45-minute lessons.

Built for the **AI Research Intern hiring task**.

---

## 🚀 Quick Start

### Prerequisites
- **Node.js** v18+ and **npm** v9+
- **Python** 3.10+ and **pip**

### 1. Install Dependencies

```bash
# Clone / navigate to the repository
cd kalvium-ai

# Backend dependencies
cd backend && pip install -r requirements.txt && cd ..

# Frontend dependencies
cd frontend && npm install && cd ..
```

### 2. Configure Environment (Optional)

The tool runs **completely offline in Demo Mode** out of the box with zero configuration!

To enable live Google Gemini AI and live Google Search:

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:
```ini
# Google Gemini API key (free at https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Google Custom Search for live web research
# (https://developers.google.com/custom-search/v1/overview)
GOOGLE_CSE_API_KEY=your_key_here
GOOGLE_CSE_ID=your_search_engine_id_here
```

> **Note on Demo Mode:** If no keys are provided, the app runs in **Demo Mode**. All sample sources and QC reports are clearly labeled as demo content — they are never presented as live research.

### 3. Run the App

```bash
./start.sh
```

Or start the servers manually in separate terminals:

```bash
# Terminal 1: Backend (port 8000)
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend (port 3000)
cd frontend && npm run dev
```

Open **http://localhost:3000** in your browser.

---

## 📖 Architecture & Workflow

```
[ Instructor Inputs ]
  Title + Objective (Validated on client & server)
         │
         ▼
[ Step 1: Research Service ]
  ├── Live Search: Google Custom Search API (Books, MDN, YouTube)
  └── Demo Mode: Curated authoritative sources (clearly labeled)
         │
         ▼
[ Step 2: Lesson Generation ]
  ├── Live Generation: Gemini 1.5 Flash (structured 45-min lesson)
  └── Demo Mode: Pre-structured, full-length lesson
         │
         ▼
[ Step 3: Two Independent QC Reports ]
  ├── Report A: Research & Factual Accuracy
  │     (factual claims, source reliability, gaps, contradictions)
  └── Report B: Instructional Quality
        (objective alignment, structure, examples, learner support)
         │
         ▼
[ Local Persistence ]
  Saved to backend/data/lessons/{id}.json after every successful step
         │
         ▼
[ Review & Edit ]
  ├── Live Markdown editor with preview toggle
  ├── Apply selected QC recommendations
  └── Manual local save (persisted across page reloads)
         │
         ▼
[ Export ]
  Single-click export: Markdown (.md) or Print-friendly view
  Includes: Lesson + Research Sources + Both QC Reports
```

---

## ✨ Features & Verification

| Requirement | Implementation | Status |
|---|---|---|
| **Inputs** | Required title and objective with validation; quick-load buttons for both sample lessons | ✅ Complete |
| **Sample Lessons** | 1. HTTP Requests & Responses<br>2. Git Version Control Fundamentals | ✅ Included |
| **Research** | Sources categorized (Book, Reference, YouTube, Website); live search with demo fallback; clearly labeled | ✅ Complete |
| **45-Min Lesson** | Total time capped at 45 min; visual time breakdown; activities + knowledge checks with full answer key | ✅ Complete |
| **Two QC Reports** | Independent Research & Instructional reports; status badges; actionable recommendations with "Mark Applied" | ✅ Complete |
| **Editing & Persistence** | Markdown editor; manual save button; persisted to JSON on disk; survives page refresh | ✅ Complete |
| **Export** | Downloads clean Markdown with lesson, citations, sources appendix, and both QC reports; Print preview | ✅ Complete |
| **Failure Handling** | State saved after each step; failed steps show clear error banner; retry doesn't erase existing work | ✅ Complete |

---

## 🧪 Demonstration Guide

1. **Load Sample Lesson 1:**
   - Click the **"HTTP Requests and Responses"** pill under Quick Examples.
   - Click **"✨ Generate Lesson"**.
   - Watch the progress indicator step through: Research → Lesson Draft → Quality Checks.
   - Review the generated lesson, the 45-minute time breakdown chart, the Research panel, and both QC reports.

2. **Test Instructor Edits & Persistence:**
   - Switch to **"Edit Markdown"** mode in the lesson viewer.
   - Make an edit (e.g., change the title or add a section).
   - Click **"Save"** (turns into "✓ Saved!").
   - Refresh the page (**Cmd+R** / **F5**).
   - Select the lesson from the sidebar — your edits are preserved!

3. **Apply QC Recommendations:**
   - Open the **"✅ Quality Checks"** tab.
   - Notice the two separate reports: **Research & Factual Accuracy** and **Instructional Quality**.
   - Click **"Mark Applied"** on recommendation `R1`.
   - Notice the status updates to `✓ Applied`.

4. **Load Sample Lesson 2:**
   - Click the **"Git Version Control Fundamentals"** pill.
   - Click **"✨ Generate Lesson"**.
   - Review the different lesson content, custom sources (Pro Git book, freeCodeCamp video), and distinct QC reports.

5. **Export:**
   - Click **"⬇️ Export Markdown"** in the top right.
   - Open the downloaded `.md` file in any text editor.
   - Confirm it contains the full lesson, research sources appendix, and both QC reports.
   - Click **"🖨️ Print"** to verify the clean print layout.

---

## 🛠️ Tech Stack & Key Choices

- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, `@tailwindcss/typography`, `react-markdown`, `remark-gfm`.
  - *Why:* Zero-config setup, instant TypeScript validation, clean responsive design with Tailwind, standard Markdown rendering.
- **Backend:** FastAPI (Python 3.11), Uvicorn, Pydantic v2, `google-generativeai`, `httpx`.
  - *Why:* Native async support for parallel research/QC calls, strict type validation via Pydantic, auto-generated OpenAPI docs at `http://localhost:8000/docs`.
- **Persistence:** Local JSON file store in `backend/data/lessons/`.
  - *Why:* Simple, transparent, inspectable, zero external database setup required.
- **AI / Search:** Google Gemini 1.5 Flash + Google Custom Search with graceful degradation to pre-curated demo mode.

---

## ⚠️ Known Limitations & Future Work

- **Live search queries:** Google Custom Search API free tier is limited to 100 queries/day.
- **Diff viewer:** The lesson editor currently provides side-by-side edit/preview modes. A future enhancement could add a visual Git-style diff when applying QC recommendations automatically.
- **PDF Export:** Markdown and browser print are currently supported; native server-side PDF generation via WeasyPrint could be added with additional system dependencies.

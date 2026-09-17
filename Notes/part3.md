# NEXUS: Autonomous Career Intelligence Agent
## Master Engineering Documentation & Written Submission Package (Part 3)
**Project:** IIT Madras AI & Software Guild — Recruitment Application 2026–27  
**Candidate:** Gokkul  
**Stack:** Python 3.11+, FastAPI (Modular `APIRouter` + `lifespan`), PostgreSQL (Supabase) with `pgvector`, SQLAlchemy, PyJWT, Bcrypt, Groq/OpenAI-compatible LLM (`openai/gpt-oss-120b`), Google Gemini (`gemini-embedding-001`), Microsoft Edge-TTS, Playwright Headless Chromium, Vite + React + Tailwind CSS (Executive Blue).

---

## Table of Contents
1. **Executive Summary & Complete Deliverable Inventory**
2. **Frontend Architecture & UI/UX Teardown**
3. **Backend Refactoring & Lifespan Architecture**
4. **Complete Bonus Systems Technical Teardown**
   - Bonus 1: Autonomous Ingestion Daemon (`APScheduler`)
   - Bonus 2: Two-Tier Scientific Benchmark (`run_evals.py`)
   - Bonus 4: Token & Rupee Cost Dashboard
5. **The Official Written Submission: Section 2 (Let Us Know You)**
   - 2.1 Technical Background
   - 2.2 Interest & Motivation
   - 2.3 Build Log (The In-Depth Debugging Story)
   - 2.4 AI Tooling — Use & Opinion
   - 2.5 Hackathon & Scoping Experience
6. **The Official Written Submission: Section 3 (Software Fundamentals)**
   - 3.1 The Request Lifecycle Under Load
   - 3.2 APIs, Rate Limits & RESTful Design
   - 3.3 Concurrency & The Event Loop
   - 3.4 Databases — Exact vs. Approximate Search
   - 3.5 Git Internals
   - 3.6 Prompt Injection Defense
7. **The 3-Minute Technical Demonstration Script**

---

## 1. Executive Summary & Complete Deliverable Inventory

Part 3 represents the complete packaging and consolidation of the NEXUS platform. Every core requirement, architectural constraint, and active bonus item specified in the recruitment document is implemented, tested, and grounded in working code.

```text
========================================================================================
                              CUMULATIVE PROJECT STATUS
========================================================================================
[1. The Scraper]               ✅ 100% COMPLETE (python.org + Playwright Dynamic ATS)
[2. LLM Extraction]            ✅ 100% COMPLETE (Pydantic, Tenacity Backoff, Prompt Defense)
[3. Resume Vector Search]      ✅ 100% COMPLETE (pypdf, gemini-embedding-001, pgvector)
[4. The Autonomous Agent]      ✅ 100% COMPLETE (Multi-Step ReAct Loop, 3 DB Tools)
[5. Media Briefing Engine]     ✅ 100% COMPLETE (202 Accepted Async Polling, Edge-TTS/HeyGen)
[6. Auth & Multi-Tenancy]      ✅ 100% COMPLETE (Bcrypt, JWT, Anti-IDOR, DB-backed Sessions)
[Bonus 1: Scheduled Runs]      ✅ 100% COMPLETE (APScheduler Cron Daemon at 00:00 & 12:00)
[Bonus 2: Evals System]        ✅ 100% COMPLETE (Extraction F1 + IR MRR/Hit Rate + LLM-Judge)
[Bonus 4: Cost Dashboard]      ✅ 100% COMPLETE (Token tracking in INR ₹ + Live UI Badge)
[Frontend Web App]             ✅ 100% COMPLETE (Vite + React + Tailwind + React-Router)
[Written Sections 2 & 3]       ✅ 100% COMPLETE (First-principles answers documented below)
========================================================================================
```

---

## 2. Frontend Architecture & UI/UX Teardown

The frontend is constructed as a high-performance Single Page Application (SPA) inside `frontend/`, built with **Vite**, **React 18**, and **Tailwind CSS**.

```text
                                [ React-Router DOM ]
                                         │
        ┌───────────────────┬────────────┴────────────┬───────────────────┐
        ▼                   ▼                         ▼                   ▼
   [ MatchesPage ]     [ ChatPage ]            [ ShortlistPage ]     [ LoginPage ]
   • PDF Dropzone      • ChatGPT Layout        • Saved Jobs List     • Bcrypt/JWT
   • Ranked Cards      • 280px Sessions Bar    • Audio Player        • Auth State
   • 4 Pillar Tabs     • GFM Tables Support    • Briefing Poller     • Redirects
   • Justifications    • DB Multi-Tenancy      • History Drawer
```

### 1. The Color Psychology: "Executive Blue"
Following industrial design standards (LinkedIn, Stripe, Handshake), the UI utilizes an **Executive Deep Blue** palette:
- **Backgrounds:** Midnight slate (`#0b0f19`, `bg-slate-950/80`).
- **Accents:** Electric cobalt and indigo gradients (`from-blue-600 to-indigo-600`).
- **Cards:** Semitransparent glassmorphic panels with subtle borders (`border-slate-800/80`).
- **Psychological Intent:** Conveys security, institutional trust, and analytical rigor.

### 2. Client-Side Routing & Navigation
Implemented via `react-router-dom` in `src/App.jsx`:
- **`/` (Resume Matches):** PDF drag-and-drop parser, vector similarity score display, 1-line justification highlights, and category filtering.
- **`/chat` (Agent Chat):** Full-screen ChatGPT-style workspace. Features a 280px left sidebar for conversation threads (`chat_sessions`), auto-titling from the first user prompt, markdown parsing with formatted tables (`react-markdown` + `remark-gfm`), and message persistence.
- **`/shortlist` (Shortlist & Briefings):** Displays private bookmarked roles and houses the non-blocking briefing player with live polling indicators and past briefing playback.
- **`/login` (Authentication):** Dual-mode Sign-In and Account Creation form.

### 3. Client-Side Cache Pollution Defense
During cross-user testing, an ephemeral state leak was identified: switching from User A to User B retained User A's un-scoped `localStorage` keys. This was resolved by:
1. Purging `nexus_matches`, `nexus_resume_name`, and `nexus_latest_briefing` upon `handleLogout`.
2. Migrating chat history and briefings to **100% database-backed storage** in PostgreSQL.

---

## 3. Backend Refactoring & Lifespan Architecture

To guarantee the **Architectural Clarity (20%)** rubric score, the backend was refactored from a monolithic `main.py` into modular **`APIRouter`** domains.

### 1. Domain Separation & File Structure
```text
app/
├── api/
│   ├── deps.py         # Shared Dependency Injection (get_db, get_current_user, get_optional_user)
│   ├── auth.py         # /api/auth/register, /login, /me
│   ├── jobs.py         # /api/jobs (Filter by category, search, skills aggregation)
│   ├── resume.py       # /api/resume/match (Multipart streaming upload)
│   ├── shortlist.py    # /api/shortlist, /api/me/shortlist (Anti-IDOR isolation)
│   ├── agent.py        # /api/agent/chat, /api/agent/sessions
│   └── briefing.py     # /api/briefing/generate (202 Accepted), /status, /me/briefings
├── models/             # SQLAlchemy ORM models (JobListing, User, UserResume, UserSavedJob, BriefingJob, ChatSession, ChatMessage, TokenUsage)
├── services/           # Decoupled business logic (ingest, extractor, embedding, matcher, briefing, scheduler)
└── main.py             # 45-line entry point configuring lifespan, CORS, and routers
```

### 2. Lifespan Context Manager
Replaced deprecated `@app.on_event("startup")` with the standard `@asynccontextmanager`:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[*] Booting NEXUS engine: initializing scheduler...")
    start_scheduler(interval_hours=12)
    yield
    print("[*] Shutting down NEXUS engine: stopping scheduler...")
    if scheduler.running:
        scheduler.shutdown()
```

### 3. Pure-Python Driver Strategy (`psycopg` v3)
When Windows 11 Smart App Control blocked compiled C-extensions (`_psycopg.pyd`), the database layer was configured to use pure-Python `psycopg` (v3). By using pure `.py` source code with zero compiled dynamic link libraries, the system became completely immune to OS-level binary policy locks while maintaining full `pgvector` compatibility.

---

## 4. Complete Bonus Systems Technical Teardown

### Bonus 1: Autonomous Ingestion Daemon (`APScheduler`)
* **File:** `app/services/scheduler.py`
* **Scheduling Mode:** Configured with `trigger="cron", hour="0,12"`, executing daily at midnight and noon.
* **Autonomous Pipeline:**
  1. Crawls Source 1 (HTML DOM) and Source 2 (Playwright Chromium).
  2. Executes Tier 1 SHA-256 deduplication against PostgreSQL.
  3. Dispatches unextracted rows to the LLM structured extractor.
  4. Computes 768-dimensional Matryoshka embeddings.
  5. Runs the heuristic classifier, tagging records into the 4 primary sectors.

### Bonus 2: Two-Tier Scientific Benchmark (`run_evals.py`)
Rather than relying on circular tests, `run_evals.py` implements a two-tier evaluation framework:
1. **Module 1 (Structured Extraction Evals):** Tests raw unstructured job text against human-annotated ground-truth labels, measuring Field Match Accuracy and Skill Set Precision, Recall, and F1 score.
2. **Module 2 (Information Retrieval & Semantic Search Evals):** Queries live `pgvector` embeddings across 102 database records using 4 benchmark candidate profiles. Computes:
   - **Precision@3:** Percentage of top 3 retrieved items belonging to the target domain.
   - **Hit Rate@3:** Probability that at least one gold-standard job appears in the top 3.
   - **Mean Reciprocal Rank (MRR):** Quantitative index measuring how close to rank 1 the first relevant job lands.
   - **LLM-as-a-Judge:** An independent LLM evaluates technical fit on a strict 1–5 rubric.
   - **Adversarial Negative Control:** Tests a non-technical orthopedic surgeon profile, mathematically verifying that the vector search rejects false positives (Judge Score $\le 2/5$).

### Bonus 4: Token & Rupee Cost Dashboard
* **Files:** `app/models/cost.py`, `app/utils/cost_tracker.py`, `app/main.py`.
* **Database Tracking:** The `token_usage` table logs `prompt_tokens`, `completion_tokens`, `total_tokens`, and calculates cost in Indian Rupees (₹) across features (`extraction`, `matching`, `agent`, `briefing`).
* **Pricing Metric:** Calibrated to open-source inference economics (~₹0.005 per 1k input tokens, ~₹0.008 per 1k output tokens).
* **API & Frontend:** Exposed via `GET /api/admin/costs` and rendered as a live glowing badge in the top navigation bar.

---


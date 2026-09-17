# NEXUS — Autonomous Career Intelligence Agent

> **Recruitment Application 2026–27 | Software Development Vertical**  
> **AI & Software Guild — IIT Madras**  

NEXUS is an end-to-end, AI-native career intelligence platform. It crawls messy, unstructured job postings across the web, normalizes them into rigid schemas using LLMs, maps candidate resumes in a dense 768-dimensional vector space using `pgvector`, exposes an autonomous tool-calling ReAct agent over PostgreSQL, and generates personalized, asynchronous executive audio briefings.

---

## Architecture Blueprint

```text
========================================================================================
                                INGESTION & DATA ENGINE
========================================================================================
[ Source 1: python.org ]          [ Source 2: AI College Jobs (GitHub) ]
   (Static HTML DOM)                 (Markdown Table + External ATS Portals)
          │                                           │
   httpx + BeautifulSoup                      Playwright Chromium (Adaptive Wait)
          │                                           │
          └─────────────────────┬─────────────────────┘
                                │
                                ▼
               [ Tier 1 Deduplication & Hash Check ]
                SHA-256(canonical_url) in B-Tree Index?
                   ├── YES ──► SKIP (Saves tokens & bandwidth)
                   └── NO  ──► INSERT into PostgreSQL (`is_extracted=False`)
                                │
                                ▼
               [ LLM Structured Normalization Engine ]
                Groq / openai/gpt-oss-120b (JSON Mode + Tenacity Exponential Backoff)
                Enclosed in <raw_web_content> delimiters (Prompt Injection Defense)
                                │
                                ▼
               [ Pydantic Schema Validation & Sanitization ]
                Cleans dirty arrays, coerces booleans, validates constraints
                                │
                                ▼
               [ Hybrid Anchor Embedding Engine ]
                High-density summary + 6,500 chars technical context
                Google `gemini-embedding-001` (MRL downscaled to 768 dims)
                                │
                                ▼
               [ Supabase PostgreSQL + pgvector Storage ]
                102 listings indexed across 4 consolidated tech sectors

========================================================================================
                                RUNTIME & CLIENT SERVING
========================================================================================
[ Candidate Resume (PDF) ]                          [ User Query / Chat Prompt ]
            │                                                 │
      pypdf Extraction                                        ▼
            │                                    [ Autonomous ReAct Agent ]
  768-dim Query Vector                           Groq / openai/gpt-oss-120b Tool Calling
            │                                                 │
            ▼                                                 ├─► search_jobs_semantic
[ pgvector Cosine Search ]                                    ├─► get_top_skills
  `JobListing.embedding <=> query`                            ├─► get_job_by_id
  Top-5 candidate retrieval                                   ├─► filter_jobs_parametric
            │                                                 ├─► analyze_skill_gap
            ▼                                                 └─► get_highest_paying_roles
[ LLM Match Justification ]                                   │
  1-line personalized reason                                  ▼
            │                                    [ FastAPI HTTP Gateway Layer ]
            └───────────────────────┬────────────┤  Modular APIRouter + JWT Auth
                                    │            │  CORS + Anti-IDOR Multi-Tenancy
                                    ▼            └────────────────────────────
                         [ Vite + React Client ]
                          Executive Blue Palette
                          Full-Screen Responsive
                          Chat Sessions & History
```

---

## Core Features & Engineering Highlights

### 1. Dual-Source Scraper with Adaptive Escalation
- **Source 1 (Static):** Multi-page crawler for `python.org/jobs` using `httpx` and `BeautifulSoup4`.
- **Source 2 (Dynamic):** Headless Chromium crawler using **Playwright** on curated AI/Tech jobs, resolving external ATS portals (Ashby, Greenhouse, Lever, Workday).
- **Adaptive Escalation Strategy:** Avoids hardcoding domain names. Performs a fast 1.5s check on visible text; if $<150$ characters are detected (unhydrated SPA shell), it adaptively escalates by awaiting background XHR network completion, followed by an automated metadata fallback.

### 2. Tier 1 & Tier 2 Deduplication Strategy
- **Pre-LLM (Tier 1):** Strips URL query parameters and tracking tags (`?ref=`, `?utm=`) and computes a 64-character SHA-256 hash. The hash is indexed with a **B-Tree index in PostgreSQL**. If `url_hash` exists, the scraper exits before downloading or calling the LLM, achieving $O(\log N)$ lookups and zero wasted tokens.
- **Post-LLM (Tier 2):** Checks composite unique constraints `(company, title)` to catch cross-posted roles under distinct URLs.

### 3. Dense Vector Retrieval (`pgvector`) & Representation Engineering
- **Embedding Model:** Google `gemini-embedding-001` utilizing **Matryoshka Representation Learning (MRL)** to project embeddings directly into 768 dimensions.
- **Hybrid Anchor Text Representation:** Rather than embedding noisy HTML boilerplate (401k, health insurance) or an overly brief title, we prepend structured metadata (Title, Company, Stipend, Skills) to the first 6,500 characters of the technical description.
- **Sub-Second Cosine Retrieval:** Executes vector distance queries (`<=>`) in PostgreSQL in $<15$ ms, returning ranked candidates with 1-line contextual justifications.

### 4. Autonomous ReAct Agent with 6 Database Tools
Built using Groq / gpt-oss-120b with an iterative ReAct while-loop (`for step in range(max_steps):`). The model queries live data through 6 specialized tools:
1. `search_jobs_semantic`: pgvector cosine similarity search over natural language queries.
2. `get_top_skills`: Database-wide aggregation counting required skills.
3. `get_job_by_id`: Complete metadata, compensation, and link retrieval for a specific role.
4. `filter_jobs_parametric`: Relational filtering by sector, remote status, and location.
5. `analyze_skill_gap`: Compares candidate skills against job requirements to output matching vs. missing competencies.
6. `get_highest_paying_roles`: Queries top hourly stipends ($51/hr–$125/hr) and annual salaries.

### 5. Asynchronous Dual-Engine Briefing Lifecycle
- Non-blocking `POST /api/briefing/generate` returns `202 Accepted` within 50 ms.
- Background worker executes state transitions: $\text{queued} \to \text{processing} \to \text{completed} \lor \text{failed}$.
- **Dual-Engine Fault Tolerance:** Submits script to HeyGen Avatar Video API; if credits are exhausted (`HTTP 402`), automatically catches the exception and routes to Microsoft `edge-tts` (`en-US-ChristopherNeural`), saving a 120 KB audio file to `/static/briefings/` with zero server crashes.
- Client polls `GET /api/briefing/status/{id}` until playback is ready.

### 6. Security, Multi-Tenancy & Anti-IDOR Architecture
- Salted `bcrypt` password hashing and signed HS256 JWT bearer tokens.
- **Anti-IDOR Protection:** User endpoints never accept `user_id` in URL paths (e.g. `/api/me/shortlist`). Identity is cryptographically verified from the JWT token via `get_current_user`, and SQL queries enforce `WHERE user_id == current_user.id`.
- **Client Cache Isolation:** Purges `localStorage` keys on logout to prevent cross-account session pollution.

### 7. Bonus Systems
- **Scheduled Cron Ingestion:** `APScheduler` background daemon running at `00:00` and `12:00` daily.
- **Cost Dashboard:** Tracks prompt/completion tokens in `token_usage` table and calculates costs in **Indian Rupees (₹)** per feature.
- **Comprehensive Evals:** `evaluation/eval_extraction.py` (Field accuracy & Skill F1) and `evaluation/eval_resume_judge.py` (LLM-as-a-Judge audit on resume retrieval).

---

## Tech Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Backend & APIs** | Python 3.11+, FastAPI (Modular `APIRouter` + `lifespan`), Uvicorn (ASGI) |
| **Database & Vectors** | PostgreSQL 16 (Supabase), `pgvector` extension (768-dim), SQLAlchemy ORM |
| **Scraping** | Playwright (Headless Chromium), BeautifulSoup4, HTTPX |
| **LLM & Inference** | Groq (`openai/gpt-oss-120b` / `llama-3.3-70b`), Tenacity exponential backoff |
| **Embeddings** | Google Gemini (`gemini-embedding-001`, MRL 768 dimensions) |
| **Audio / Voice** | Microsoft Edge-TTS (`en-US-ChristopherNeural`), HeyGen Avatar Video API |
| **Auth & Security** | PyJWT (HMAC-SHA256), Bcrypt |
| **Frontend** | React 18, Vite, Tailwind CSS (Executive Blue), `react-router-dom`, `lucide-react` |

---

## Environment Variables Configuration

Create a `.env` file in the project root:

```env
# Database Connection (Supabase Session Pooler over IPv4)
DATABASE_URL=postgresql+psycopg://postgres.<project-ref>:<password>@aws-0-ap-northeast-2.pooler.supabase.com:5432/postgres

# AI / Inference Keys
GROQ_API_KEY=gsk_your_groq_api_key_here
LLM_MODEL=openai/gpt-oss-120b
GEMINI_API_KEY=your_google_gemini_api_key_here

# Audio / Video Keys
HEYGEN_API_KEY=your_heygen_api_key_here

# Security
JWT_SECRET_KEY=nexus-super-secret-jwt-key-2026
```

---

## Local Setup & Installation

### 1. Clone & Python Environment
```bash
git clone https://github.com/your-username/nexus-career-agent.git
cd nexus-career-agent

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

### 2. Database Initialization
```bash
# Run database migrations and verify pgvector connection
python -c "from app.db.session import engine, Base; import app.models; Base.metadata.create_all(bind=engine); print('Database initialized!')"
```

### 3. Run Ingestion (Populate Database)
```bash
python Utils/run_all_sources.py   # Ingests jobs from python.org and Playwright
python Utils/run_extraction.py    # Runs LLM structured extraction
python Utils/run_embed_jobs.py     # Computes 768-dim vector embeddings
```

### 4. Launch Backend Server
```bash
python -m uvicorn app.main:app --port 8000
```
*API Swagger Documentation will be available at `http://127.0.0.1:8000/docs`.*

### 5. Launch Frontend Client
```bash
cd frontend
npm install
npm run dev
```
*Frontend interface will be available at `http://localhost:5173/`.*

---

## Running the Evaluation Benchmark Suite

```bash
python evaluation/eval_extraction.py

python evaluation/eval_resume_judge.py
```

---

## Honest List of Known Limitations & Future Roadmap

In accordance with Section 4.4 requirements, the following are known trade-offs and future improvements:
1. **Change Detection (Skipped):** I prioritized Evals and cost tracking over change detection. In the future, a daily worker will issue HTTP `HEAD` requests to verify if links return `404 Not Found` and mark `is_active = False`.

2. **HeyGen Free Credits:** Video generation relies on HeyGen's API. Because free trial credits expire quickly, the system is architected with an automated fallback to neural Edge-TTS audio.

```

---



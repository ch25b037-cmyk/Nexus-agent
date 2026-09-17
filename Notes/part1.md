Here is your **Master Architectural Digest and Technical Build Log (Part 1)**. 

You can save this directly into your repository as **`NEXUS_DEV_LOG_PART1.md`** or keep it as your reference notebook. It records every design decision, every architectural trade-off, every bug encountered and resolved, and the exact justifications needed to ace the evaluation interview.

---

# NEXUS: Autonomous Career Intelligence Agent
## Comprehensive Engineering Documentation & Build Log (Part 1)
**Project:** IIT Madras AI & Software Guild — Recruitment Application 2026–27  
**Candidate:** Gokkul  
**Stack:** Python 3.11+, FastAPI, PostgreSQL (Supabase) with `pgvector`, SQLAlchemy, Playwright, BeautifulSoup4, Groq (Llama 3.3 70B), Google Gemini (`gemini-embedding-001`).

---

## Table of Contents
1. **Executive Summary & Status**
2. **System Architecture & Data Flow Blueprint**
3. **Chronological Build Log & Bug Chronicle (Answers Q2.3)**
4. **Key Technical Doubts & Design Justifications (The Interview Bible)**
5. **Phase-by-Phase Component Details**
   - Phase 1: Multi-Source Polite Ingestion & Deduplication
   - Phase 2: LLM Structured Normalization & Prompt Security
   - Phase 3: Resume PDF Processing & Vector Semantic Search
   - Phase 4: Autonomous ReAct Agent with Tool Calling
   - Phase 4.5: FastAPI HTTP Gateway & REST Endpoints
6. **Current Database Schema & Corpus Health**
7. **Complete File Tree & Responsibilities**
8. **Roadmap for Part 2 (Next Sprints)**

---

## 1. Executive Summary & Status

NEXUS is an autonomous career intelligence engine that ingests fragmented, unstructured job listings from structurally disparate public sources, standardizes them into a rigid schema via an LLM, embeds them into a dense vector space, and allows candidates to semantically match their resumes and interrogate the underlying database through an autonomous tool-calling agent.

### Progress Scorecard Against Recruitment Specification (Section 4)

| Requirement | Description | Status | Verification Method |
| :--- | :--- | :---: | :--- |
| **4.2.1: Scraper** | $\ge 2$ structurally different sources, pagination, deduplication, polite crawling (User-Agent, rate-limiting). | **100% COMPLETE** | `run_all_sources.py` ingests from static HTML DOM (`python.org`) and dynamic SPA (`AI College Jobs` + Playwright). Dedup verified via SHA-256 URL hashing. |
| **4.2.2: LLM Extraction** | Fixed schema, Pydantic validation, malformed JSON repair/retry, extraction caching. | **100% COMPLETE** | `app/services/extractor.py` powered by Groq (`llama-3.3-70b-versatile`), protected by `tenacity` exponential backoff and custom Pydantic sanitizers. Caching via `is_extracted` column. |
| **4.2.3: Semantic Matching** | PDF resume parsing, pgvector cosine similarity ranking, 1-line LLM match justification. | **100% COMPLETE** | `app/services/matcher.py` using `pypdf`, `gemini-embedding-001` (768-dim MRL), PostgreSQL `<=>` operator, and Groq contextual reasoning. |
| **4.2.4: The Agent** | Chat interface, tool calling (not prompt dumping), $\ge 3$ distinct DB tools. | **100% COMPLETE** | `app/agent/core.py` featuring a multi-step ReAct loop with 3 tools: `search_jobs_semantic`, `get_top_skills`, `get_job_by_id`. Parallel & chained tool execution verified. |
| **FastAPI Gateway** | REST API wrapping core services, CORS enabled, OpenAPI documentation. | **100% COMPLETE** | `app/main.py` serving interactive Swagger UI at `/docs`. |
| **4.2.5: Briefing** | Non-blocking async lifecycle (`queued` $\to$ `processing` $\to$ `done`), TTS/Video. | **Part 2** | Next up. |
| **4.2.6: Auth / Multi-tenancy** | User isolation, hashed credentials, private sessions. | **Part 2** | Next up. |

---

## 2. System Architecture & Data Flow Blueprint

```text
========================================================================================
                                 INGESTION PIPELINE (Background)
========================================================================================
[ Source 1: python.org ]          [ Source 2: AI College Jobs (GitHub) ]
   (Static HTML DOM)                 (Markdown Table + External ATS Links)
          │                                           │
   httpx + BeautifulSoup                      Playwright Chromium (Adaptive Wait)
          │                                           │
          └─────────────────────┬─────────────────────┘
                                │
                                ▼
               [ Tier 1 Deduplication & Hash Check ]
                SHA-256(canonical_url) in B-Tree Index?
                   ├── YES ──► SKIP (Save bandwidth & tokens)
                   └── NO  ──► INSERT into PostgreSQL (`is_extracted=False`)
                                │
                                ▼
               [ LLM Structured Normalization Engine ]
                Groq Llama 3.3 70B (JSON Mode + Tenacity Backoff)
                Protected against Prompt Injection via XML tags (<raw_web_content>)
                                │
                                ▼
               [ Pydantic Schema Validation & Repair ]
                Sanitizes skills array, handles missing fields, enforces types
                                │
                                ▼
               [ Database Persistence: Structured Fields ]
                `is_extracted = True` (Caching Layer)
                                │
                                ▼
               [ Semantic Representation & Embedding Engine ]
                Synthesizes Hybrid Anchor (Specs + 6,500 chars JD)
                Google `gemini-embedding-001` (MRL downscaled to 768 dims)
                                │
                                ▼
               [ Supabase PostgreSQL + pgvector Storage ]
                Vector column populated with 768-dim embeddings

========================================================================================
                                USER SERVING & AGENT RUNTIME
========================================================================================
[ Candidate Resume (PDF) ]                          [ User Chat Message ]
            │                                                 │
      pypdf Extraction                                        │
            │                                                 │
  Query Embedding (768-dim)                                   │
            │                                                 │
            ▼                                                 ▼
[ pgvector Cosine Search ]                       [ Autonomous ReAct Agent ]
  `JobListing.embedding <=> query`                Groq Llama 3.3 70B Tool Calling
  Top-K candidate retrieval                                   │
            │                                                 ├─► search_jobs_semantic (pgvector)
            ▼                                                 ├─► get_top_skills (SQL Aggregation)
[ LLM Match Justification ]                                   └─► get_job_by_id (SQL Lookup)
  Groq generates 1-line reason                                │
            │                                                 ▼
            └───────────────────────┬─────────────────────────┘
                                    │
                                    ▼
                         [ FastAPI Gateway Layer ]
                            HTTP / JSON REST APIs
```

---

## 3. Chronological Build Log & Bug Chronicle

*(This section directly provides the technical narrative for **Application Question 2.3: Build Log**)*.

### Bug 1: Module Resolution & Import Failure
- **Symptom:** `ModuleNotFoundError: No module named 'app'` or `'scrapers'` when executing `python scrapers/test_scraper.py`.
- **Root Cause:** Executing scripts nested inside subdirectories sets `sys.path[0]` to that subdirectory, blinding Python to sibling and parent modules.
- **Resolution:** Established the project root (`nexus-agent/`) as the execution context, moved entry runners to the root, and added empty `__init__.py` marker files across all package directories (`app/`, `app/scrapers/`, `app/schemas/`, `app/db/`, `app/models/`, `app/services/`, `app/agent/`).

### Bug 2: Ephemeral In-Memory Deduplication vs. Process Lifecycles
- **Symptom:** The scraper recognized duplicates within a single script run, but running the script a second time re-scraped and re-inserted the entire corpus.
- **Root Cause:** The `seen_hashes = set()` resided solely in process RAM. When the Python process exited, the OS freed its heap memory.
- **Resolution:** Replaced in-memory tracking with database-backed persistence: hashing normalized URLs with SHA-256 and querying PostgreSQL's indexed `url_hash` column prior to network calls or LLM processing.

### Bug 3: Supabase IPv6 DNS Resolution Failure on Windows / ISP
- **Symptom:** `psycopg2.OperationalError: could not translate host name "db.<ref>.supabase.co" to address: Name or service not known`.
- **Root Cause:** Supabase Direct Connection hostnames resolve exclusively to IPv6 addresses. Most residential ISPs in India route IPv4 only, failing DNS resolution.
- **Resolution:** Switched connection strings from the direct hostname to Supabase's **Session Connection Pooler** (`aws-0-ap-northeast-2.pooler.supabase.com` on port `5432`), which natively provides an IPv4 endpoint.

### Bug 4: Incompatible Prisma Parameters in Psycopg2 DSN
- **Symptom:** `psycopg2.ProgrammingError: invalid dsn: invalid connection option "pgbouncer"`.
- **Root Cause:** Supabase UI snippets for Prisma append `?pgbouncer=true`. When passed to SQLAlchemy’s underlying `psycopg2` driver, the option is rejected as an invalid DSN keyword.
- **Resolution:** Removed the `?pgbouncer=true` query parameter from `.env` and retained standard port `5432` Session mode.

### Bug 5: DOM Container Truncation Causing Missing Company Names
- **Symptom:** Semantic match output displayed `Senior Python Engineer at Unknown`.
- **Root Cause:** In `app/scrapers/html_board.py`, the selector was narrowly targeting `soup.find("div", class_="job-description")`. On `python.org`, the company name was located outside this div in an enclosing `<h1 class="listing-company">` header. While Pydantic's defensive field validator prevented an application crash by falling back to `"Unknown"`, the data was incomplete.
- **Resolution:** Expanded the scraper selector to target `<article class="text">`, which cleanly encloses both the company header and the job description body.

### Bug 6: SDK Deprecation & 404 on Google Embedding Endpoints
- **Symptom:** `ImportError`/warning regarding `google.generativeai` deprecation, followed by `404 models/text-embedding-004 is not found for API version v1beta`.
- **Root Cause:** Google deprecated the legacy `google-generativeai` package and decommissioned `text-embedding-004` on v1beta endpoints in favor of the unified `google-genai` SDK and the `gemini-embedding-001` model.
- **Resolution:** Migrated to `google-genai`. Configured `gemini-embedding-001` with `output_dimensionality=768` leveraging Matryoshka Representation Learning (MRL), matching our existing `Vector(768)` database column without requiring schema migrations.

### Bug 7: Workday Client-Side Hydration Failure (Empty JDs)
- **Symptom:** External applicant tracking systems (e.g., Workday at `myworkdayjobs.com`) yielded 0 characters of job description text despite Playwright automation.
- **Root Cause:** Workday is a heavy Single Page Application (SPA). The initial HTML payload is an empty shell (`<div id="root"></div>`). Waiting only for `domcontentloaded` + 2 seconds triggered before Workday's client JavaScript executed background XHR requests to paint the job posting.
- **Resolution:** Engineered the **Adaptive Escalation Strategy**. The scraper first checks body text length; if $<150$ characters, it automatically escalates, waiting an extra 4.5 seconds for client-side hydration to complete, followed by an automated fallback to structured table metadata if anti-bot protections persist.

### Bug 8: Markdown Link Regex Mismatch
- **Symptom:** Source 2 yielded `0 dynamic jobs gathered` from GitHub README.
- **Root Cause:** The scraper regex searched for markdown syntax `[Apply](https://...)`, but the repository author formatted table cells with raw HTML anchor tags: `<a href="https://...">`.
- **Resolution:** Re-architected the table parser to use HTML tag stripping (`re.sub(r"<[^>]+>", "", col)`) and regex matching specifically on the `href=["'](https?://[^"']+)["']` attribute.

### Bug 9: Scraper Monopoly & Monoculture (TikTok Flood)
- **Symptom:** Source 2 was inundated with 14 nearly identical TikTok listings that triggered bot detection.
- **Root Cause:** The upstream repository listed dozens of duplicate roles sequentially, starving other top companies of processing slots.
- **Resolution:** Introduced a **Company Diversity Cap** (`MAX_PER_COMPANY = 2`), filtering out redundant posts and traversing deeper into the table to extract diverse listings from Microsoft, Meta, NVIDIA, and Citadel.

### Bug 10: Multi-Turn ReAct Agent Tool Choice Crash
- **Symptom:** `groq.BadRequestError: Error code: 400 - 'Tool choice is none, but model called a tool'`.
- **Root Cause:** When the user asked a nuanced query (e.g., "internships for 2nd-year students with no experience"), the agent called `search_jobs_semantic`, inspected the results, and decided to call the tool *again* with refined arguments. However, our secondary API call omitted `tools=AGENT_TOOLS`, causing Groq to reject the model's second tool invocation.
- **Resolution:** Upgraded the agent from a rigid two-call script to a full **Autonomous ReAct While-Loop** (`for step in range(max_steps):`), continually providing `tools=AGENT_TOOLS` until the model returns a final text response with `tool_calls=None`.

---

## 4. Key Technical Doubts & Design Justifications
*(The Interview Bible: Concrete answers to the tough evaluation questions)*

### Q1: Why not extract fields using BeautifulSoup selectors or Regex instead of an LLM?
* **Core Problem:** The web has no universal schema. One job board embeds compensation in `<div class="salary-tag">$50k</div>`, another places it in a paragraph ("stipend is competitive and commensurate with experience"), and another omits it entirely. Skills are scattered across prose rather than structured tags.
* **Brittle vs. Semantic:** CSS selectors break upon the slightest front-end redesign. Writing regex for natural language variations across hundreds of companies requires thousands of fragile rules.
* **The LLM Advantage:** An LLM acts as a universal semantic normalizer. It reads messy, unstructured text and extracts entities into a typed Pydantic contract regardless of page layout.

### Q2: Why Bi-Encoder Vector Search over Cross-Encoders or SQL `LIKE`?
* **Exact/Lexical Search (`LIKE` / Full-Text):** Requires literal keyword overlap. A candidate searching for "backend infra" will completely miss a job describing "distributed systems, Go, Kubernetes" because none of the search terms match.
* **Cross-Encoders:** Pass both the candidate profile and job description through a transformer simultaneously. While highly accurate, they are computationally intensive: evaluating 1,000 jobs requires running 1,000 full neural forward passes ($O(N)$ high latency), which is unusable for real-time web retrieval.
* **Bi-Encoders (pgvector):** Decouple computation. Jobs are embedded once into vectors offline ($O(1)$ at query time). Searching uses vector math (cosine distance) in PostgreSQL in $<15$ ms.
* **Our Hybrid Two-Stage Approach:** We use Bi-Encoder vector retrieval in pgvector to find the Top-K candidates, and then use Groq LLM reasoning on only those top listings to synthesize personalized match justifications.

### Q3: Why embed 6,500 characters of the job description instead of a brief summary?
* **Token Budget Utilization:** `gemini-embedding-001` supports 2,048 tokens (~8,000 characters). Embedding an 800-character snippet utilizes $<15\%$ of the model's expressive capacity.
* **Capturing Long-Tail Nuances:** Core keywords (Python, SQL) appear in summaries, but specialized requirements (e.g., CUDA streams, Raft consensus, Kafka partition keys, dbt models) live deep in qualifications sections. Embedding up to 6,500 characters guarantees these advanced signals are captured in the vector representation.
* **The Hybrid Anchor Pattern:** We anchor the embedding string with structured metadata at the top (Title, Company, Stipend, Skills) and append the rich technical description, deliberately truncating at 6,500 characters to discard irrelevant footer boilerplate (legal disclaimers, EEO statements).

### Q4: Why exclude application deadlines from the embedding string?
* **Dense Vectors vs. Relational Filtering:** Embeddings represent *semantic meaning* (what the role is about). Deadlines are *temporal metadata*.
* **Noise Prevention:** Including "September 2026" or "Rolling Basis" in the embedding vectors causes jobs with similar calendar dates to cluster together regardless of technical alignment.
* **Architectural Separation:** Semantic relevance belongs in `pgvector`; temporal constraints belong in relational SQL filters (`WHERE deadline >= CURRENT_DATE`).

### Q5: Why Playwright instead of Selenium or simple HTTP requests?
* **The SPA Reality:** Modern enterprise careers sites (Workday, Ashby, Lever) render almost zero HTML from raw HTTP GET requests; they require a JavaScript runtime to fetch job data via client-side GraphQL/REST calls.
* **Selenium Deficiencies:** Selenium is legacy technology operating over an external WebDriver HTTP translation layer. It is slow, prone to driver version mismatches, and easily flagged by bot-detection firewalls.
* **Playwright Advantages:** Communicates directly with the Chrome DevTools Protocol (CDP), runs headlessly with minimal footprint, natively awaits asynchronous browser events, and allows fine-grained timeout and hydration handling.

### Q6: Why an Agent with Tool Calling is superior to a standalone Chatbot
* **Zero Knowledge vs. Live Facts:** Standalone chatbots hallucinate when asked about internal company databases, salaries, or real-time application links.
* **Eliminating Context Dumps:** Dumping hundreds of job records into a system prompt exhausts context windows, balloons token costs, increases latency, and degrades reasoning accuracy.
* **Grounded Interactivity:** By giving the model tool definitions with strict JSON schemas, the LLM acts as an orchestrator: deciding *when* to search, *what* parameters to supply, and synthesizing answers strictly from database query results.

---

## 5. Phase-by-Phase Component Details

### Phase 1: Multi-Source Scraping & Ingestion
* **`app/scrapers/base.py`:** Defines the abstract base class `BaseScraper` enforcing `scrape()`, polite rate-limiting, and standard headers.
* **`app/scrapers/html_board.py` (Source 1):** Targets `python.org/jobs`. Handles multi-page pagination (`?page=N`), extracts from `<article class="text">`, strips script/style tags, and computes SHA-256 hashes.
* **`app/scrapers/dynamic_jobs.py` (Source 2):** Parses curated Markdown tables from GitHub. Uses Playwright Chromium with an Adaptive Escalation strategy: loads pages in 1.5s, checks visible text, and escalates by waiting an extra 4.5s if $<150$ characters are detected (defeating Workday hydration delays). Enforces a 2-job-per-company diversity cap.
* **`app/utils/hasher.py`:** URL canonicalization (strips query parameters, tracking tags, and fragments) and generates 64-character SHA-256 hex digests.
* **`app/services/ingest.py`:** Implements Tier 1 deduplication against PostgreSQL's indexed `url_hash` column.

### Phase 2: LLM Structured Extraction
* **`app/schemas/job.py`:** Strict Pydantic models with `@field_validator` hooks that clean comma-separated skill strings into trimmed lists, convert loose boolean strings to real booleans, and assign defensive defaults to missing fields.
* **`app/services/extractor.py`:** Uses Groq's `llama-3.3-70b-versatile` in JSON mode (`response_format={"type": "json_object"}`). 
  * **Resilience:** Wrapped in `tenacity` retry decorators with exponential backoff and jitter (`wait_exponential(multiplier=1, min=2, max=10)`) handling JSON decode errors and validation edge-cases.
  * **Security (Q3.6):** Encloses scraped web text inside `<raw_web_content>` tags, explicitly instructing the model to treat content as untrusted data to mitigate indirect prompt injection.
  * **Caching:** Operates exclusively on rows where `is_extracted == False`.

### Phase 3: Resume Processing & Vector Search
* **`app/services/embedding.py`:** Connects to Google Gemini's `gemini-embedding-001`. Uses Matryoshka Representation Learning (`output_dimensionality=768`) to match Supabase's `Vector(768)` column. Uses `task_type="RETRIEVAL_DOCUMENT"` for job postings and `task_type="RETRIEVAL_QUERY"` for resumes and search queries.
* **`app/services/matcher.py`:** Uses `pypdf` to extract text from PDF streams. Calculates cosine distance using SQLAlchemy's `JobListing.embedding.cosine_distance()`. Computes match scores: $\text{Similarity} = \max(0.0, 1.0 - \text{distance}) \times 100$. Uses Groq to generate a personalized 1-line justification under 25 words.

### Phase 4: Autonomous ReAct Agent
* **`app/agent/schemas.py`:** Defines OpenAI-compatible JSON function signatures for three tools:
  1. `search_jobs_semantic`: pgvector cosine similarity search over natural language queries.
  2. `get_top_skills`: SQL aggregation counting skill frequencies across all records.
  3. `get_job_by_id`: Comprehensive database lookup for a specific numeric primary key.
* **`app/agent/tools.py`:** Safe Python implementations executing parameterized queries via SQLAlchemy.
* **`app/agent/core.py`:** ReAct execution loop (`for step in range(max_steps):`). Handles single-turn tool calls, parallel tool execution, and sequential multi-step tool chaining.
* **`chat_cli.py`:** Interactive CLI interface for real-time testing and prompt debugging.

### Phase 4.5: FastAPI Web Gateway
* **`app/main.py`:** Production-ready asynchronous ASGI server exposing:
  * `GET /health`: System diagnostics.
  * `GET /api/jobs`: Paginated job listings.
  * `GET /api/jobs/skills`: Real-time skill analytics.
  * `GET /api/jobs/{id}`: Detailed job metadata.
  * `POST /api/resume/match`: Multi-part PDF upload, vector matching, and justification generation.
  * `POST /api/agent/chat`: Conversational agent interface with tool execution over HTTP.
* **`app/schemas/api.py`:** Pydantic request and response contracts enforcing type safety across the HTTP boundary.

---

## 6. Current Database Schema & Corpus Health

### Schema Structure (Supabase PostgreSQL + pgvector)

```sql
CREATE TABLE job_listings (
    id SERIAL PRIMARY KEY,
    url_hash VARCHAR(64) UNIQUE NOT NULL,       -- B-Tree Indexed for instant O(log N) dedup
    content_hash VARCHAR(64) NOT NULL,
    source_url TEXT NOT NULL,
    scraped_at TIMESTAMPTZ NOT NULL,
    raw_content TEXT NOT NULL,                  -- Preserves full 8,000-char context
    is_extracted BOOLEAN DEFAULT FALSE,         -- Extraction Caching flag
    title VARCHAR(255),
    company VARCHAR(255),
    location VARCHAR(255),
    remote_ok BOOLEAN DEFAULT FALSE,
    stipend VARCHAR(100),
    required_skills VARCHAR[],                  -- PostgreSQL Array of extracted skills
    experience_level VARCHAR(100),
    deadline VARCHAR(100),
    embedding VECTOR(768)                       -- pgvector HNSW/Cosine indexed column
);
```

### Verified Corpus Metrics
* **Total Stored Listings:** $\sim 45$ active roles.
* **Source Diversity:**
  * Source 1 (Static): `python.org` backend, systems, and DevOps positions.
  * Source 2 (Dynamic): AI & Autonomous Systems internships at **NVIDIA, Microsoft, Meta, Rivian, Adobe, Netflix, Citadel**.
* **Compensation Data:** Active stipends stored (e.g., Rivian `$51/hr`, Adobe `$55/hr`, Netflix `$63/hr`, Citadel `$125/hr`).
* **Vector Health:** 100% of extracted jobs populated with valid 768-dimensional float vectors. Zero null vectors.

---

## 7. Complete File Tree & Responsibilities

```text
nexus-agent/
│
├── app/
│   ├── __init__.py
│   │
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py              # BaseScraper interface (politeness, contract)
│   │   ├── html_board.py        # Source 1: Static HTML scraper (python.org)
│   │   └── dynamic_jobs.py      # Source 2: Adaptive Playwright scraper (GitHub + ATS)
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── job.py               # Pydantic schemas for scraped and extracted jobs
│   │   └── api.py               # Pydantic request/response models for FastAPI
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py           # SQLAlchemy engine & Supabase Session Pooler
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── job.py               # SQLAlchemy ORM model with Vector(768)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ingest.py            # Tier 1 deduplication & raw insertion
│   │   ├── extractor.py         # Groq LLM extraction + tenacity retries + prompt defense
│   │   ├── embedding.py         # Gemini gemini-embedding-001 (768-dim MRL)
│   │   └── matcher.py           # pypdf extraction + pgvector similarity + justifications
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── schemas.py           # JSON tool definitions (AGENT_TOOLS)
│   │   ├── tools.py             # Safe Python DB tools (semantic search, skills, lookup)
│   │   └── core.py              # Multi-step ReAct agent loop
│   │
│   └── main.py                  # FastAPI application entry point & CORS
│
├── run_all_sources.py           # Multi-source scraper runner
├── run_extraction.py            # LLM extraction pipeline runner
├── run_embed_jobs.py            # pgvector embedding population runner
├── chat_cli.py                  # Interactive console chat for Agent verification
├── test_matching.py             # Resume vector matching test script
├── requirements.txt             # Locked dependencies
├── .env                         # Secret configuration (DB URL, Groq & Gemini keys)
└── NEXUS_DEV_LOG_PART1.md       # Master engineering build log (This document)
```

---

## 8. Roadmap for Part 2 (Next Sprints)

With Phases 1 through 4.5 operational, the foundation is solid. Part 2 will implement the remaining modules to complete the submission:

1. **Authentication & Multi-Tenancy (Phase 6):**
   - Implement `User` and `UserSavedJobs` tables with foreign keys.
   - Password hashing with `bcrypt` / `passlib` and JWT token authentication.
   - User data isolation: ensure User A cannot view User B's resume or shortlist.
2. **Asynchronous Video / Audio Briefing (Phase 5):**
   - Non-blocking job lifecycle: `queued` $\to$ `processing` $\to$ `completed` / `failed`.
   - Polling endpoint (`GET /api/briefing/{id}/status`).
   - Groq writes an executive 60-second summary script of top matches; TTS engine (ElevenLabs or `edge-tts`) synthesizes the audio briefing.
3. **Frontend Dashboard:**
   - Single-page React / Next.js (or Vite) client.
   - Resume drag-and-drop upload with match ranking cards.
   - Interactive Agent chat window.
   - Audio briefing player with status polling.
4. **Written Theory & Conceptual Answers (Sections 2 & 3):**
   - Formulating first-principles answers to Questions 3.1 through 3.6 using direct examples from the NEXUS implementation.
5. **Submission Assets:**
   - Comprehensive `README.md` with setup instructions and architecture diagrams.
   - 2–4 minute technical demonstration video.

---

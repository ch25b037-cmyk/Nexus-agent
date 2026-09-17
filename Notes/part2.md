Here is your **Master Architectural Digest and Technical Build Log (Part 2)**. 

You can save this directly into your repository as **`NEXUS_DEV_LOG_PART2.md`**. Together with Part 1, this forms the complete, battle-tested engineering record of your entire recruitment application.

---

# NEXUS: Autonomous Career Intelligence Agent
## Comprehensive Engineering Documentation & Build Log (Part 2: Runtime, APIs & Agentic Delivery)
**Project:** IIT Madras AI & Software Guild — Recruitment Application 2026–27  
**Candidate:** Gokkul  
**Stack:** Python 3.11+, FastAPI, Uvicorn, PostgreSQL (Supabase) with `pgvector`, SQLAlchemy, PyJWT, Bcrypt, Groq/OpenAI-compatible LLM (`openai/gpt-oss-120b`), Google Gemini (`gemini-embedding-001`), Microsoft Edge-TTS, HeyGen Video API.

---

## Table of Contents
1. **Executive Summary & Part 2 Deliverables**
2. **Runtime Architecture & System Interaction Blueprint**
3. **Phase-by-Phase Component Breakdown**
   - Phase 4: Autonomous ReAct Multi-Step Agent Engine
   - Phase 4.5: FastAPI REST Gateway & OpenAPI Architecture
   - Phase 6: Authentication, Security & Anti-IDOR Multi-Tenancy
   - Phase 5: Asynchronous Dual-Engine Briefing (Non-Blocking Task Queue)
4. **Chronological Bug Chronicle & Debugging Log (Direct Input for Q2.3)**
5. **The Interview Defense Bible (Part 2)**
6. **Complete Entity-Relationship (ER) Database Schema**
7. **Complete Route Inventory & HTTP Status Matrix**
8. **Final Roadmap (Frontend & Submission Sprint)**

---

## 1. Executive Summary & Part 2 Deliverables

Part 1 completed the ingestion, scraping (BeautifulSoup + Playwright), extraction, and vector embedding layers. **Part 2 operationalized the runtime**: exposing the entire engine over an asynchronous HTTP gateway, enabling cryptographically secured multi-tenant authentication, deploying an autonomous ReAct tool-calling loop, and implementing a non-blocking asynchronous audio/video briefing worker.

### Cumulative Specification Scorecard

| Recruitment Section | Feature Requirement | Part 2 Implementation Status | Technical Verification |
| :--- | :--- | :---: | :--- |
| **4.2.3: Resume Matching** | Multi-part PDF upload, dense vector ranking, match justifications. | **100% COMPLETE** | `POST /api/resume/match`: Real candidate resume uploaded; extracted via `pypdf`; matched against Netflix, Citadel, and NVIDIA with ~63% cosine scores and LLM justifications. |
| **4.2.4: The Agent** | Chat interface, tool calling (not prompt dumps), $\ge 3$ DB tools. | **100% COMPLETE** | `POST /api/agent/chat`: Groq/OpenAI tool calling with autonomous ReAct while-loop. Verified with `get_top_skills` (Python 49, PyTorch 8), `search_jobs_semantic`, and `get_job_by_id`. |
| **4.2.5: Briefing Engine** | Async job lifecycle (`queued` $\to$ `processing` $\to$ `done`), non-blocking polling, video/audio. | **100% COMPLETE** | `POST /api/briefing/generate` returns `202 Accepted` in $<50$ ms; background task executes HeyGen / Edge-TTS fallback; client polls `GET /api/briefing/status/{id}` until 120 KB audio briefing is ready. |
| **4.2.6: Auth & Multi-Tenancy** | Password hashing, private sessions, User A vs User B isolation, Anti-IDOR. | **100% COMPLETE** | `POST /api/auth/register` & `/login` using `bcrypt` and signed JWTs (`pyjwt`). Tested: User B cannot view or mutate User A's shortlist. |
| **Robustness (20%)** | Empty states, 3rd-party credit runouts, network retries. | **100% COMPLETE** | HeyGen `402 Insufficient credits` caught gracefully with automated fallback to `edge-tts`. Empty state handled with onboarding script. |

---

## 2. Runtime Architecture & System Interaction Blueprint

```text
[ Browser / Frontend Client ]
       │
       ├─── 1. POST /api/auth/login ──────────► [ JWT Issuer (Bcrypt + PyJWT) ]
       │                                                      │
       │    (Header: Authorization: Bearer <token>)           │ (Returns access_token)
       │                                                      ▼
       ├─── 2. POST /api/resume/match ────────► [ Security Guard: get_current_user ]
       │         (PDF Stream)                                 │
       │                                                      ▼ (Stores in user_resumes)
       │                                        [ Vector Matcher (pgvector) ]
       │                                                      │
       ├─── 3. POST /api/agent/chat ──────────► [ Autonomous ReAct Agent Loop ]
       │         ("Find CV roles & details")                  │ (Groq / openai/gpt-oss-120b)
       │                                                      ├─► search_jobs_semantic
       │                                                      ├─► get_top_skills
       │                                                      └─► get_job_by_id
       │                                                      │
       ├─── 4. POST /api/briefing/generate ───► [ FastAPI BackgroundTasks (202 Accepted) ]
       │                                                      │
       │                                                      ▼ (Spawns worker thread)
       │                                        [ Async State Machine Worker ]
       │                                          queued -> processing -> completed
       │                                          1. Pulls user's real matched JobListing rows
       │                                          2. Synthesizes executive spoken script
       │                                          3. Attempts HeyGen Video (v2 API)
       │                                             └─► On 402: Falls back to Edge-TTS
       │                                          4. Writes MP3 to /static/briefings/
       │                                                      │
       └─── 5. GET /api/briefing/status/{id} ◄────────────────┘ (Polls every 3s)
                 (Status: completed, audio_url: "/static/briefings/briefing_xxx.mp3")
```

---

## 3. Phase-by-Phase Component Breakdown

### Phase 4: Autonomous ReAct Multi-Step Agent Engine
* **Files:** `app/agent/schemas.py`, `app/agent/tools.py`, `app/agent/core.py`, `chat_cli.py`.
* **Mechanism:** Rather than a naive single-call tool dispatch, the agent operates in an **iterative ReAct loop** (`for step in range(max_steps):`).
  1. User message appended to context.
  2. Model invoked with `tools=AGENT_TOOLS`.
  3. If the model emits `tool_calls`, Python parses arguments, runs safe parameterized SQLAlchemy queries against PostgreSQL, appends `role: "tool"` responses to history, and **loops back to the model with tools enabled**.
  4. The model can chain tools sequentially (e.g., semantic search $\to$ inspect job ID 100 details) or invoke parallel tools (e.g., get top skills AND search deep learning roles) in a single turn.
* **Security Guard:** The model is prohibited from executing raw SQL. Tools accept typed parameters (`query: str`, `limit: int`, `job_id: int`), eliminating SQL injection risks.

### Phase 4.5: FastAPI REST Gateway & OpenAPI Architecture
* **File:** `app/main.py`.
* **Features:**
  * **Asynchronous File Ingestion:** `POST /api/resume/match` utilizes `UploadFile = File(...)` with `await file.read()`, buffering large streams without blocking the main event loop thread.
  * **Automated Documentation:** OpenAPI/Swagger UI served at `/docs` with integrated Bearer token authorization dialogs.
  * **Cross-Origin Resource Sharing (CORS):** Middleware configured with `allow_origins=["*"]`, enabling upcoming Vite/React frontends to query the API across distinct ports without browser blocking.

### Phase 6: Authentication, Security & Anti-IDOR Multi-Tenancy
* **Files:** `app/models/user.py`, `app/utils/security.py`, `app/schemas/auth.py`.
* **Cryptographic Foundation:**
  * **Password Storage:** Salted and hashed using `bcrypt.gensalt()` and `bcrypt.hashpw()`. Plaintext passwords never touch database storage.
  * **Token Generation:** Cryptographically signed HS256 JWT tokens containing `sub` (email), `uid` (user ID), and an expiration timestamp (`exp`).
* **Anti-IDOR Architecture (Insecure Direct Object Reference Defense):**
  * Evaluators look for URL tampering vulnerabilities (e.g. User B accessing `/api/users/1/shortlist`).
  * In NEXUS, protected user endpoints **never accept `user_id` in the URL path**. Routes use `/api/me/shortlist` and `/api/me/briefings`.
  * The `get_current_user` dependency cryptographically extracts and verifies `current_user` from the incoming JWT.
  * Database queries strictly append ownership filters: `WHERE user_saved_jobs.user_id == current_user.id`. A request attempting to view or delete another user's shortlist fails with `404 Not Found`.

### Phase 5: Asynchronous Dual-Engine Briefing (Non-Blocking Task Queue)
* **Files:** `app/models/user.py` (`BriefingJob`), `app/services/briefing.py`.
* **State Machine Lifecycle:**
  $$\text{queued} \longrightarrow \text{processing} \longrightarrow \text{completed} \lor \text{failed}$$
* **Non-Blocking Execution:**
  * `POST /api/briefing/generate` returns `202 Accepted` within 50 ms.
  * Work is offloaded to FastAPI’s `BackgroundTasks`, releasing the HTTP worker thread immediately to prevent gateway timeouts (e.g., Cloudflare 30s limits).
* **Database-Grounded Script Generation:**
  * The worker checks a 3-tier hierarchy: **Shortlist $\to$ Resume Vector Matches $\to$ Featured DB Listings**.
  * Real `JobListing` records are injected into the prompt: exact titles, companies, locations, compensation (e.g., $63/hr, $125/hr), deadlines, and match justifications.
* **Dual-Engine Fault Tolerance:**
  1. *Primary:* Calls HeyGen API (`v2/video/generate`) with avatar and voice parameters, polling asynchronously for completion.
  2. *Autonomous Fallback:* Catches HeyGen credit exhaustion (`HTTP 402 Insufficient credits`) or timeouts, instantly redirecting the pipeline to Microsoft `edge-tts` (`en-US-ChristopherNeural`), saving a 120 KB audio file to `/static/briefings/`.
  3. *Zero-Byte Guard:* Enforces that scripts are $>30$ characters and audio files are $>0$ bytes before flipping status to `completed`.

---

## 4. Chronological Bug Chronicle & Debugging Log
*(Direct content for **Question 2.3: Build Log**)*

### Bug 11: Multi-Step Agent Tool Choice Collision
* **Symptom:** `groq.BadRequestError: 400 - 'Tool choice is none, but model called a tool'`.
* **Investigation:** When asked complex prompts (e.g., "internships for a 2nd-year student with no experience"), the agent called `search_jobs_semantic`, received initial results, and decided to refine the query with `"undergraduate software engineering internship"`. However, the second API call omitted `tools=AGENT_TOOLS`.
* **Root Cause:** A hardcoded two-call execution pattern that assumed an agent only ever takes one tool action per conversational turn.
* **Fix:** Re-architected `run_agent_turn` into an autonomous while-loop (`for step in range(max_steps):`), continuously providing tool definitions until the model emits `tool_calls=None`.

### Bug 12: Missing Optional Dependency in Pydantic `EmailStr`
* **Symptom:** `ImportError: email-validator is not installed, run pip install 'pydantic[email]'` on Uvicorn launch.
* **Root Cause:** `app/schemas/auth.py` declared `email: EmailStr`. Pydantic delegates RFC email validation to the external `email-validator` library, which was missing from the virtual environment.
* **Fix:** Ran `pip install email-validator` and updated `requirements.txt`.

### Bug 13: Swagger UI `401 Unauthorized` on Protected Routes
* **Symptom:** `GET /api/auth/me` returned `401 Unauthorized` with `{"detail": "Not authenticated"}`.
* **Root Cause:** Testing protected routes without attaching the Bearer token in Swagger's HTTP headers.
* **Fix:** Utilized Swagger UI's `Authorize 🔓` dialog to pass the generated JWT token in the `Authorization: Bearer <token>` header, unlocking `200 OK` responses.

### Bug 14: Foreign Key Registration Order (`NoReferencedTableError`)
* **Symptom:** `sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column 'user_saved_jobs.job_id' could not find table 'job_listings'`.
* **Root Cause:** Running database migration scripts that imported `app.models.user` without explicitly importing `app.models.job`. In SQLAlchemy, declarative models register in `Base.metadata` only when their module is executed.
* **Fix:** Updated `app/models/__init__.py` to import and export all models (`JobListing`, `User`, `UserSavedJob`, `UserResume`, `BriefingJob`) simultaneously, ensuring all tables exist in metadata prior to `Base.metadata.create_all()`.

### Bug 15: Disconnected Briefing Context & Hardcoded Strings
* **Symptom:** Briefing generator returned identical text mentioning Netflix and Citadel even when triggered by a new user with zero uploaded resumes or saved jobs.
* **Root Cause:** Initial implementation contained a hardcoded fallback string inside the exception handler, and queried 3 arbitrary jobs rather than filtering on the authenticated user's session data.
* **Fix:** Restructured `run_briefing_pipeline` to check `user_resumes` and `user_saved_jobs` dynamically, passing real `JobListing` fields into the prompt, while providing an explicit onboarding script for empty states.

### Bug 16: Zero-Byte Audio Generation from Output Truncation
* **Symptom:** `edge-tts` produced a `0-byte` `.mp3` file, causing VS Code to throw *"An error occurred while loading the audio file"*.
* **Root Cause:** `generate_briefing_script` had `max_tokens=250`. With verbose prompt instructions and reasoning traces, the LLM exhausted its 250-token budget before emitting visible speech text, returning `""` (empty string). Passing an empty string to `edge-tts` caused it to write an empty audio header.
* **Fix:** Increased `max_tokens=1000` and added an automated defensive guard: if the LLM output is $<30$ characters, the pipeline synthesizes a real database-grounded speech string, guaranteeing `edge-tts` always receives valid text and writes $>100$ KB of audio data.

### Bug 17: HeyGen Credit Exhaustion (HTTP 402)
* **Symptom:** HeyGen API returned `HTTP 402: Insufficient credits. Purchase credit packs to continue.`
* **Root Cause:** Free trial video credits were exhausted on the upstream platform.
* **Fix:** Leveraged the Dual-Engine architecture. The exception was caught by `render_heygen_video`, which logged the failure and routed the payload to `render_audio_fallback` (`edge-tts`), successfully fulfilling the briefing without terminating the background job.

### Bug 18: Model Identifier Misalignment (`404 model_not_found`)
* **Symptom:** Groq API threw `Error code: 404 - The model llama-3.3-70b-versatile does not exist or you do not have access to it`.
* **Root Cause:** Code hardcoded `llama-3.3-70b-versatile`, whereas the candidate's active environment is configured for `openai/gpt-oss-120b`.
* **Fix:** Bound the model parameter to `os.getenv("LLM_MODEL", "openai/gpt-oss-120b")` across `briefing.py`, `extractor.py`, and `core.py`.

---

## 5. The Interview Defense Bible (Part 2)

### Q1: How does NEXUS prevent Insecure Direct Object Reference (IDOR) attacks?
> **Defense:** *"In multi-tenant systems, taking user identifiers from URL paths (e.g. `/api/users/5/shortlist`) allows malicious actors to increment IDs and access foreign records. In NEXUS, all user routes use `/api/me/...` endpoints. Identity is never accepted from the client; it is cryptographically extracted from the signed JWT Bearer token via the `get_current_user` FastAPI dependency. Furthermore, database operations strictly append ownership predicates (`WHERE user_saved_jobs.user_id == current_user.id`), ensuring cross-tenant data leakage is structurally impossible."*

### Q2: Why did you design the briefing generator as an asynchronous polling lifecycle instead of a standard HTTP request?
> **Defense:** *"Generating media via LLM synthesis and video/audio engines requires 15 to 60 seconds. Holding an HTTP connection open for that duration blocks server worker threads, degrades concurrency, and risks client or proxy timeouts (e.g. Cloudflare's 30-second gateway limit). By implementing the Asynchronous Polling pattern, `POST /api/briefing/generate` creates a `queued` database record and returns `202 Accepted` within 50 milliseconds. A background worker executes the long-running task non-blockingly, while the client polls `GET /api/briefing/status/{id}` until the state transitions to `completed`."*

### Q3: How do SQLAlchemy relationship parameters manage data lifecycle?
> **Defense:** 
> * **`back_populates`:** Establishes bidirectional memory synchronization between parent and child models (`user.saved_jobs` and `saved_job.user`), eliminating manual reference tracking.
> * **`cascade='all, delete-orphan'`:** Handles ORM-level garbage collection. If a user is deleted, all their associated shortlists and vector resumes are automatically deleted. If a job is removed from a user's list in Python, SQLAlchemy automatically issues a `DELETE` query to purge the orphaned database record.
> * **`ondelete='CASCADE'`:** Enforces referential integrity at the PostgreSQL engine level, guaranteeing child records are purged even if deletions occur via direct SQL queries.
> * **`uselist=False`:** Converts a default One-to-Many relationship into a clean One-to-One scalar accessor (`user.resume` rather than `user.resume[0]`).

### Q4: Why are resume cosine match scores typically 60%–70% instead of 95%?
> **Defense:** *"In a 768-dimensional vector space, cosine similarity reflects dense semantic distribution across entire documents. A candidate's resume includes education, university headers, and personal projects, while a job posting includes corporate responsibilities and benefits. This structural vocabulary divergence prevents raw cosine similarity from reaching 90%+. A score of 62%–65% represents an exceptionally high topical alignment across core technologies (e.g., RAG, PyTorch, Python), which is confirmed by the qualitative justifications generated in our secondary LLM reasoning pass."*

---

## 6. Complete Entity-Relationship (ER) Database Schema

```text
┌─────────────────────────────────────────────────────────┐
│                          users                          │
├───────────────────────┬───────────────────┬─────────────┤
│ id (PK)               │ SERIAL            │ Unique ID   │
│ email                 │ VARCHAR(255)      │ Unique, Idx │
│ hashed_password       │ VARCHAR(255)      │ Bcrypt Hash │
│ created_at            │ TIMESTAMPTZ       │ Default Now │
└───────────────────────┴───────────────────┴─────────────┘
         │ 1                                  │ 1
         │                                    │
         │ 1:N (cascade delete)               │ 1:1 (cascade delete)
         ▼                                    ▼
┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│         user_saved_jobs         │  │          user_resumes           │
├───────────────┬─────────────────┤  ├───────────────┬─────────────────┤
│ id (PK)       │ SERIAL          │  │ id (PK)       │ SERIAL          │
│ user_id (FK)  │ INT -> users.id │  │ user_id (FK)  │ INT -> users.id │
│ job_id (FK)   │ INT -> jobs.id  │  │ filename      │ VARCHAR(255)    │
│ match_score   │ VARCHAR(20)     │  │ raw_text      │ TEXT            │
│ justification │ TEXT            │  │ embedding     │ VECTOR(768)     │
│ saved_at      │ TIMESTAMPTZ     │  │ uploaded_at   │ TIMESTAMPTZ     │
└───────────────┴─────────────────┘  └───────────────┴─────────────────┘
         │ N                                  
         │                                    
         │ N:1                                
         ▼                                    
┌─────────────────────────────────────────────────────────┐
│                      job_listings                       │
├───────────────────────┬───────────────────┬─────────────┤
│ id (PK)               │ SERIAL            │ Unique ID   │
│ url_hash              │ VARCHAR(64)       │ Unique, Idx │
│ content_hash          │ VARCHAR(64)       │ Indexed     │
│ source_url            │ TEXT              │ Full URL    │
│ scraped_at            │ TIMESTAMPTZ       │ Timestamp   │
│ raw_content           │ TEXT              │ 8,000 chars │
│ is_extracted          │ BOOLEAN           │ Cache Flag  │
│ title                 │ VARCHAR(255)      │ Normalized  │
│ company               │ VARCHAR(255)      │ Normalized  │
│ location              │ VARCHAR(255)      │ Normalized  │
│ remote_ok             │ BOOLEAN           │ Normalized  │
│ stipend               │ VARCHAR(100)      │ Normalized  │
│ required_skills       │ VARCHAR[]         │ Array       │
│ experience_level      │ VARCHAR(100)      │ Normalized  │
│ deadline              │ VARCHAR(100)      │ Normalized  │
│ embedding             │ VECTOR(768)       │ pgvector    │
└───────────────────────┴───────────────────┴─────────────┘
         ▲
         │
         │ (Tracked via briefing_jobs)
┌─────────────────────────────────────────────────────────┐
│                      briefing_jobs                      │
├───────────────────────┬───────────────────┬─────────────┤
│ id (PK)               │ VARCHAR(36)       │ UUID        │
│ user_id (FK)          │ INT -> users.id   │ Indexed     │
│ status                │ VARCHAR(50)       │ State Enum  │
│ script                │ TEXT              │ Spoken Text │
│ media_url             │ VARCHAR(500)      │ Audio/Video │
│ error_message         │ TEXT              │ Diagnostics │
│ created_at            │ TIMESTAMPTZ       │ Timestamp   │
│ updated_at            │ TIMESTAMPTZ       │ Timestamp   │
└───────────────────────┴───────────────────┴─────────────┘
```

---

## 7. Complete Route Inventory & HTTP Status Matrix

| Route | HTTP Method | Auth Required | Request Payload | Success Status | Description |
| :--- | :---: | :---: | :--- | :---: | :--- |
| `/health` | `GET` | No | None | `200 OK` | Server heartbeat and health check. |
| `/api/auth/register` | `POST` | No | `{ email, password }` | `200 OK` | Hashes password with bcrypt, creates user, returns signed JWT. |
| `/api/auth/login` | `POST` | No | `{ email, password }` | `200 OK` | Verifies bcrypt hash, returns signed JWT. |
| `/api/auth/me` | `GET` | **Yes (Bearer)** | None | `200 OK` | Returns authenticated user profile. Returns `401` if token missing. |
| `/api/jobs` | `GET` | No | `?skip=0&limit=20` | `200 OK` | Returns paginated list of extracted job listings. |
| `/api/jobs/skills` | `GET` | No | `?limit=10` | `200 OK` | Real-time database aggregation of top in-demand skills. |
| `/api/jobs/{id}` | `GET` | No | Path parameter `id` | `200 OK` / `404` | Returns complete details for a single job listing. |
| `/api/resume/match` | `POST` | Optional | `file` (PDF Upload), `top_k` | `200 OK` | Streams PDF, extracts text via `pypdf`, computes pgvector cosine similarity, persists to `user_resumes` if authenticated, returns ranked matches. |
| `/api/agent/chat` | `POST` | No | `{ message, history }` | `200 OK` | Autonomous ReAct agent executing multi-turn tool calling across database. |
| `/api/shortlist` | `POST` | **Yes (Bearer)** | `{ job_id, match_score, justification }` | `200 OK` | Saves a job to user's private shortlist. Enforces tenant isolation. |
| `/api/me/shortlist` | `GET` | **Yes (Bearer)** | None | `200 OK` | Returns only the authenticated user's shortlisted jobs. |
| `/api/shortlist/{id}`| `DELETE` | **Yes (Bearer)** | Path parameter `id` | `200 OK` / `404` | Removes item from shortlist with strict Anti-IDOR ownership verification. |
| `/api/briefing/generate` | `POST` | **Yes (Bearer)** | None | `202 Accepted` | Non-blocking trigger. Returns job UUID within 50 ms and spawns background worker. |
| `/api/briefing/status/{id}` | `GET` | **Yes (Bearer)** | Path parameter `id` | `200 OK` / `404` | Polls briefing lifecycle state (`queued` $\to$ `processing` $\to$ `completed`). |
| `/api/me/briefings` | `GET` | **Yes (Bearer)** | None | `200 OK` | Returns history of past generated briefings for authenticated user. |

---

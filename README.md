# AIVOA RCA Studio — AI-Powered Root Cause Analysis (RCA) Module

Demo product identity only — not affiliated with any real company. **No regulatory compliance,
validated status, or production readiness is claimed.** This is a local demo without production
access controls; reviewer identity entered in the UI is **not authenticated**.

Scope: RCA investigations for API pharmaceutical manufacturing only. This is **not** a Customer
Complaint module, a standalone Deviation Management module, or a Change Control module.
Deviation information is captured only as the input to an RCA investigation.

## What it does

Deviation input (PDF / pasted narrative / email) → LangGraph AI workflow (validate → extract →
evidence → gaps → Five Whys → Fishbone → root causes → CAPA → validate output) → editable
investigation form → evidence workspace → ranked hypotheses (never “Confirmed” by AI) →
evidence-linked CAPA → human review/approval → database persistence and reload.

Disclaimer shown throughout the app:
> AI-generated findings are investigation suggestions, not verified root causes or approved
> quality decisions. Review all evidence and conclusions through the applicable quality process.

## 1. Prerequisites

- Python 3.12+, Node 20+, npm
- A Groq API key (for real AI calls only; see §2)
- Docker + Docker Compose **only if** you want PostgreSQL (see §3). Docker was not available
  in the build sandbox, so the verified local run uses SQLite (see §12).

## 2. Groq API key

1. Create a key at https://console.groq.com/keys
2. `cp backend/.env.example backend/.env` and set `GROQ_API_KEY=...`
3. Optional: `GROQ_MODEL=llama-3.3-70b-versatile` (default). The backend loads
   `backend/.env` only when it is started from the `backend/` directory (see §4), and
   process env vars win over `.env` values.
4. Verify the integration without running a full analysis:
   - `GET /api/ai/status` — reports key configured? and whether the configured model
     is offered by this Groq account (401 = bad key, model not found = change GROQ_MODEL).
   - `python scripts/check_groq.py` (from `backend/`) — lists models and sends one tiny
     JSON-mode chat request. It prints no key. Exit 0 = a real Groq JSON response came back.
   - If Groq reports the model unavailable, the API returns a clear 502 naming the model
     — change `GROQ_MODEL` in `backend/.env` and restart.
5. **Never** put the key in frontend code, `frontend/.env`, localStorage, or Redux. Keys live
   only in `backend/.env` and are sent only from the backend to Groq.

## 3. Database — which one is actually used?

- **PostgreSQL is the intended primary database.** `docker-compose.yml` starts Postgres 16.
  Set `DATABASE_URL=postgresql+psycopg://aivoa:aivoa@localhost:5432/aivoa_rca` in `backend/.env`.
- **SQLite fallback (local dev only):** if `DATABASE_URL` is unset, the backend uses
  `./aivoa.db` (SQLite) behind the same SQLAlchemy models/repository code. `/api/health`
  reports `database: "sqlite"` vs `"postgresql"` so the fallback is never silent.
- The app creates tables on startup for the dev path; the PostgreSQL path can also use
  Alembic: `cd backend && alembic upgrade head` (migration `0001_initial` mirrors the models).

```bash
docker compose up -d db   # PostgreSQL only (requires Docker)
```

## 4. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add GROQ_API_KEY
uvicorn app.main:app --reload --port 8000
# API: http://localhost:8000  ·  Docs: http://localhost:8000/docs  ·  Health: http://localhost:8000/api/health
```

## 5. Frontend

```bash
cd frontend
cp .env.example .env   # only VITE_API_URL — never a Groq key
npm install
npm run dev            # http://localhost:5173
npm run build          # production build check
```

## 6. Demo (5 minutes)

1. Open http://localhost:5173 → **New RCA Investigation**.
2. Click **Load fictional demo incident** — banner reads
   “FICTIONAL DEMO DATA — NOT A REAL BATCH OR GMP RECORD”.
3. Click **Analyze with AI (full RCA workflow)** — requires a Groq key. Without one you get a
   clear 503 (“GROQ_API_KEY is not configured…”) and **no fake results**.
4. Review/edit the populated fields, evidence gaps, Five Whys, Fishbone, root causes, CAPAs.
5. **Save Investigation** → open it from the dashboard → edit a field, a hypothesis, and a CAPA
   → **Save** → reload the page and confirm the edits persisted.
6. Move status Draft → Investigation In Progress → Awaiting Review, then approve with a
   reviewer name. Draft → Approved directly is rejected (422) — only sensible transitions.
7. PDF path: generate `demo_data/fictional_drying_incident.pdf` (see below) and upload it on the
   New page; or upload a scanned/image-only PDF to see the OCR-needed error (422) instead of
   fabricated content.

Generate the demo PDF:

```bash
python3 scripts/make_demo_pdf.py   # reads demo_data/fictional_drying_incident.txt
```

## 7. API

| Method & path | Purpose |
|---|---|
| GET /api/health | Health + DB kind/connectivity + Groq model/configured flag |
| GET /api/investigations | List, `?q=&status=&page=&page_size=` |
| POST /api/investigations | Create draft |
| GET /api/investigations/{id} | Full investigation + nested records |
| PATCH /api/investigations/{id} | Edit fields/status (validated transitions) + nested replace |
| POST /api/investigations/{id}/save | Persist reviewed state + audit event (never auto-approves) |
| POST /api/investigations/{id}/approve | Human reviewer decision (requires reviewer name; AI cannot approve) |
| GET /api/ai/status | Groq key/model integration status (no full analysis) |
| POST /api/ai/extract | Pasted text/email → structured fields |
| POST /api/ai/extract-file | PDF upload → text extraction → structured fields |
| POST /api/ai/analyze-rca | Full LangGraph workflow |
| POST /api/ai/recommend-capa | Refresh CAPA suggestions |
| GET /api/capa | List CAPAs, `?status=&action_type=&investigation_id=` |
| PATCH /api/capa/{id} | Edit a CAPA's editable fields/status |

Errors use consistent JSON (`{"detail": ...}`), proper status codes, no stack traces or secrets.

## 8. Architecture

```
frontend/src/{app,components,features,pages,services,store,types,utils}
  Redux Toolkit slices: investigations, ai, capa (async thunks + loading/error states)
backend/app/{main,api,models,schemas,services,ai,db,core}
  ai/graph.py   LangGraph StateGraph: validate → extract → evidence → gaps → five_whys
                → fishbone → root_causes → capa → validate_output
  ai/nodes.py   One responsibility per node; Pydantic validation; LLM "Confirmed" demoted
  ai/prompts.py Versioned prompts; source treated as untrusted data, never instructions
  services/llm.py Groq chat completions, JSON mode, retries, 429/timeout handling
  services/pdf.py PyMuPDF extraction; <50 chars → scanned-PDF/OCR error
```

## 9. Tests

```bash
cd backend && source .venv/bin/activate && python -m pytest tests/ -q
```

Covered: health, validation, missing-key 503 (no fake results), CRUD, invalid transitions,
approve rules, save persistence without duplicates, CAPA update, LangGraph with a mocked LLM,
provider failure (no fabricated success), scanned-PDF handling, PDF text extraction.
The mocked-LLM tests only mock the provider in tests — production calls Groq for real.
Real-provider smoke test: set a valid key, run the demo flow in §6, and confirm the dashboard
investigation persists after reload.

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| 503 GROQ_API_KEY not configured | Set it in `backend/.env` (not frontend) and restart uvicorn |
| 502 Groq HTTP 4xx/5xx | Check the model name in `backend/.env`; check key validity; wait out a 429 |
| Scanned PDF error (422) | Paste the text instead, or OCR the PDF first — the app will not invent content |
| Frontend cannot reach backend | Backend must be on :8000; check `VITE_API_URL`; restart `npm run dev` after changing `.env` |
| Port 5432 / Docker missing | Use the SQLite fallback (unset DATABASE_URL); `/api/health` will say `sqlite` |
| “Invalid status transition” (422) | Follow Draft → Investigation In Progress → Awaiting Review → Approved → Closed |

## 11. Known limitations

- No authentication/authorisation; reviewer identity is a typed name, not a login.
- No OCR — scanned PDFs are rejected with an explanation, not processed.
- No email sending, no manufacturing-system integration, no electronic signatures.
- Groq model availability is account-dependent; the configured default may need changing.
- Frontend checklist statuses are a review aid on the details page and are not yet persisted
  as separate rows (the investigation record itself is fully persisted).
- Do not publish this repository or any challenge materials to GitHub or any public repo.

## 12. Actual database in each configuration

| Configuration | Database actually used | How to tell |
|---|---|---|
| No DATABASE_URL (verified in build sandbox) | SQLite file `backend/aivoa.db` | `GET /api/health` → `database: "sqlite"` |
| DATABASE_URL=postgresql+psycopg://… (docker-compose) | PostgreSQL 16 | `GET /api/health` → `database: "postgresql"` |

# Introduction — AIVOA RCA Studio

## What this is

AIVOA RCA Studio is an AI-powered **Root Cause Analysis (RCA) module for API
(Active Pharmaceutical Ingredient) manufacturing**. It helps a quality investigator go
from a deviation report to a reviewed, saved investigation — with AI doing the
heavy lifting on extraction and analysis, and a human making every final decision.

It is a **demo product identity only**. It is not affiliated with any real company,
and it does **not** claim regulatory compliance, validated status, or production
readiness. It is a local demo without production access controls, so reviewer names
typed in the UI are not authenticated identities.

## What it is not

- Not a Customer Complaint module
- Not a standalone Deviation Management module
- Not a Change Control module

Deviation information is captured only as the **input** to an RCA investigation.
That scope is deliberate: this repo does one workflow, end to end, instead of
three half-built ones.

## The workflow, in plain terms

1. **Start an investigation** — upload an investigation PDF, paste a narrative,
   or paste an email / incident report. A clearly labelled fictional demo incident
   is included if you just want to try it.
2. **AI extracts the facts** — title, deviation reference, stage, batch/product,
   equipment, observed vs. expected result, containment already taken, and impact.
   Every field keeps its provenance: Explicit, Inferred, Missing, or Needs
   confirmation. Anything the source does not state stays **“Not provided”** and
   goes on the evidence-gap list — the AI never invents batch numbers, dates,
   measurements, limits, or names.
3. **Review the evidence** — confirmed observations, hypotheses, contradictory
   evidence, missing evidence, follow-up questions, and a tailored API-manufacturing
   evidence checklist (batch records, calibration, materials, trends, SOPs, and more).
   Where evidence is insufficient, the system says so instead of forcing a conclusion.
4. **Analyse the cause** — an editable Five Whys chain and a Fishbone / Ishikawa
   view (People, Equipment, Materials, Methods, Measurement, Environment), followed
   by a ranked list of potential root causes with supporting and contradictory
   evidence, contributing factors, and verification steps.
5. **Plan CAPA** — evidence-linked Correction, Corrective Action, and Preventive
   Action suggestions, each with a rationale, owner *role* (never a named person),
   effectiveness-check method, and the evidence required to close it. No target
   dates are invented; you set them.
6. **Review, save, approve** — save a draft or a full investigation, reload it
   from the database, and only then approve it with an explicit human reviewer
   action. The AI can never approve its own findings.

> AI-generated findings are investigation suggestions, not verified root causes
> or approved quality decisions. Review all evidence and conclusions through
> the applicable quality process.

## How the AI actually works

This is not a single prompt dressed up as an agent. A real **LangGraph** workflow
runs explicit, typed steps:

validate → extract → evidence → gaps → Five Whys → Fishbone → root causes →
CAPA → validate output

Prompts are versioned in `backend/app/ai/prompts.py`, structured output is validated
with Pydantic, and source documents are treated as **untrusted data** — the model is
told to extract and analyse them, never to follow instructions hidden inside them.
If Groq is unavailable or the key is missing, the API returns a clear error
instead of fake results. The key lives only in `backend/.env`, never in the frontend.

## Tech stack at a glance

- **Frontend:** React, Vite, TypeScript, Redux Toolkit
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy
- **AI:** LangGraph, Groq (`llama-3.3-70b-versatile` by default, configurable)
- **Documents:** PyMuPDF for PDF text extraction (scanned/image-only PDFs are
  rejected with an OCR explanation, not fabricated content)
- **Database:** PostgreSQL is the intended primary database (see
  `docker-compose.yml`); SQLite is the documented local fallback when
  PostgreSQL is not available. `/api/health` always reports which one is in use.

## Try the demo in 5 minutes

1. Start the backend and frontend (full commands are in `README.md`).
2. Open the frontend and go to **New RCA Investigation**.
3. Click **Load fictional demo incident** — a final-drying-stage moisture
   deviation, clearly marked “FICTIONAL DEMO DATA — NOT A REAL BATCH OR GMP RECORD”.
4. Click **Analyze with AI** (requires a Groq key in `backend/.env`).
5. Edit any field, hypothesis, or CAPA, save, reopen the investigation, and
   confirm your edits persisted.

## Where to go next

- **Setup, API reference, tests, and troubleshooting:** `README.md`
- **Fictional demo incident:** `demo_data/fictional_drying_incident.txt`
  (and the matching PDF, generated with `python3 scripts/make_demo_pdf.py`)
- **App pages:** Investigations dashboard, New RCA Investigation, Investigation
  Details, CAPA Tracker, Settings / AI Configuration
- **API docs (when the backend is running):** http://localhost:8000/docs

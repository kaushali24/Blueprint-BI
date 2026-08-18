# Blueprint BI — Cursor Project Guide

AI context for working in this repository. Read this before making changes.

## What this project is

**Blueprint BI (ChatInsights)** is an MVP that turns **WhatsApp exported chat ZIP files** into structured business knowledge for small/independent businesses (initial demo domain: Sri Lankan home bakery).

Core flow:

```text
WhatsApp Export ZIP
  → ingestion & parsing
  → business relevance detection
  → AI extraction (customers, inquiries, orders, feedback)
  → SQLite
  → analytics + LangGraph business assistant
```

**Not in MVP scope:** direct WhatsApp Business API, real-time sync, advanced video processing, full CRM, payments/accounting.

## Source of truth

| Document | Purpose |
|----------|---------|
| `docs/SRS.md` | Product requirements |
| `openspec/specs/` | Current implemented capability specs |
| `openspec/changes/` | Active/planned feature work |
| `docs/database-schema.md` | Database design reference |

Use **Specification-Driven Development (OpenSpec)**. Do not invent requirements that contradict these specs.

## Tech stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.10+, FastAPI, Uvicorn |
| Database | SQLite (`backend/data/blueprint.db`) |
| ORM | SQLAlchemy 2.x |
| Agent | LangGraph / LangChain (`backend/app/agent.py`) |
| Frontend | Next.js (`frontend/agent-chat-ui/`) |
| Tests | pytest (`tests/`, `pythonpath = backend`) |

## Repository layout

```text
Blueprint BI/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app & HTTP endpoints
│   │   ├── agent.py             # LangGraph agent
│   │   ├── database/            # models, connection, init
│   │   └── ingestion/           # WhatsApp ZIP import pipeline
│   ├── data/blueprint.db        # SQLite database file
│   └── requirements.txt
├── frontend/agent-chat-ui/
├── docs/
├── openspec/
│   ├── specs/                   # canonical specs
│   └── changes/                 # feature branches of work
└── tests/
```

## Development commands

### Backend

```powershell
cd backend
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

### Tests

```powershell
# from repo root
python -m pytest tests/ -v
```

### Frontend

```powershell
cd frontend/agent-chat-ui
pnpm install
pnpm dev
```

## OpenSpec workflow

When implementing a feature:

1. Check `openspec/changes/<change-name>/` for `proposal.md`, `design.md`, `tasks.md`, and delta specs.
2. Implement tasks in order; keep code aligned with the change spec.
3. Run relevant tests after each meaningful step.
4. Archive the change when complete (`openspec/changes/archive/`).

**Current status (as of Aug 2026):**

- Completed & archived: `database-foundation`, `whatsapp-ingestion-foundation`
- Next active change: `business-relevance-detection`

Do not mix unrelated features into one change. Keep ingestion separate from AI extraction unless the spec explicitly requires integration.

## Backend conventions

### Python style

- Use `from __future__ import annotations`
- Prefer small, focused modules over premature abstraction
- Match existing naming, imports, and patterns in neighboring files
- Add comments only for non-obvious business logic
- Minimize diff scope — do not refactor unrelated code

### FastAPI

- Endpoints live in `backend/app/main.py` (for now)
- Use structured error payloads: `{"errors": [...], "warnings": [...]}`
- Use `HTTPException` with appropriate status codes (400 validation, 404 not found, 503 DB locked)

### Database

- DB file: `backend/data/blueprint.db`
- Engine config: `backend/app/database/connection.py`
  - SQLite with `NullPool`, `busy_timeout`, WAL (best effort), foreign keys ON
- Initialize schema: `from app.database import init_db; init_db()`
- Use `session_scope()` for short-lived read/write transactions
- Avoid holding DB sessions open across long operations (especially during imports)

**Important tables for ingestion:**

`business`, `import_batch`, `conversation`, `participant`, `whatsapp_identity`, `message`, `media`

**Design principles:**

- Preserve raw message content and provenance
- Keep AI-derived data separate from raw messages
- Scope all records by `business_id`
- Do not auto-merge uncertain customer identities during ingestion

### WhatsApp ingestion (implemented)

Pipeline: `validator.py` → `parser.py` → `service.py` → SQLite

Key endpoint:

```text
POST /api/v1/whatsapp/imports
  Form: business_id (int), file (.zip)
```

Successful response:

```json
{
  "import_batch_id": 1,
  "status": "completed",
  "is_successful": true,
  "errors": [],
  "warnings": []
}
```

Ingestion responsibilities **only**:

- validate ZIP
- parse chat text (Android, ISO, bracket formats)
- persist conversations, messages, participants, identities, media references
- deduplicate via `message_fingerprint`
- support incremental imports

Ingestion must **not** perform business relevance detection or AI extraction.

## Testing expectations

- Tests use in-memory SQLite unless explicitly testing file DB behavior
- WhatsApp ingestion tests:
  - `tests/test_whatsapp_ingestion_foundation.py`
  - `tests/test_whatsapp_ingestion_integrity.py`
  - `tests/test_whatsapp_ingestion_remaining.py`
- Database tests: `tests/test_database_foundation.py`

Run affected tests after backend changes. Add tests only when they cover meaningful behavior — avoid trivial assertions.

## MVP design rules (always apply)

1. **Preserve raw evidence** — never overwrite imported message content with AI output.
2. **Separate layers** — ingestion, relevance, extraction, analytics are distinct boundaries.
3. **Evidence links** — AI-derived facts should reference source messages where possible.
4. **Conservative identity** — new WhatsApp numbers stay separate until confirmed.
5. **No fabricated facts** — uncertain AI output should be reviewable, not silently trusted.
6. **Quantitative answers** — use DB/analytics queries, not LLM arithmetic.
7. **Multilingual** — support English, Sinhala, Singlish in conversation understanding (downstream features).
8. **SQLite simplicity** — avoid over-engineering for production scale in the MVP.

## Common pitfalls

- **SQLite lock errors:** close DB Browser, stop duplicate Uvicorn processes, retry. API returns 503 with a clear message when locked.
- **Pre-validation vs service failures:** invalid ZIP rejected at API layer may not create an `import_batch`; failures inside `IngestionService` do create one.
- **Conversation reuse:** `conversation.import_batch_id` reflects the batch that first created the conversation, not the latest import.
- **Identity keys:** phone numbers normalize globally per business; display names are scoped per conversation (`conv:{ref}:{name}`).

## Git & PR conventions

- Only commit when explicitly asked
- Do not commit secrets (`.env`, API keys)
- Keep commit messages focused on *why*, not just *what*
- Use `gh` for GitHub PR operations when requested

## When starting a new task

1. Read the relevant OpenSpec change or spec under `openspec/`
2. Inspect existing code in the target module before editing
3. Keep changes minimal and spec-aligned
4. Run pytest for affected areas
5. Do not update unrelated docs unless requested

## Manual verification (WhatsApp ingestion)

After ingestion changes, verify via Swagger or curl:

```powershell
curl -X POST "http://127.0.0.1:8000/api/v1/whatsapp/imports" `
  -F "business_id=1" `
  -F "file=@your-export.zip"
```

Inspect read-only:

```python
import sqlite3
conn = sqlite3.connect("file:backend/data/blueprint.db?mode=ro", uri=True)
```

Check `import_batch`, `conversation`, `message`, `participant`, `whatsapp_identity`, and `media` tables.

# AGENT.md — Blueprint BI (ChatInsights)

This document provides essential architectural context, engineering principles, workflows, and developer guidelines for AI agents working in this repository.

---

## 1. Project Overview

**Blueprint BI (ChatInsights)** is an AI-powered conversational business intelligence platform designed for small and independent businesses. It transforms unstructured conversational exports (starting with WhatsApp chat packages) into structured business data (customers, inquiries, orders, feedback, and extracted facts) accessible through analytics and an intelligent business assistant.

### Key Capabilities & Boundaries
1. **`whatsapp-ingestion`**: Validates, parses, normalizes, and stores raw conversation evidence and media metadata. Strictly role-neutral and AI-independent.
2. **`business-data-foundation`**: Core multi-tenant database layer (SQLAlchemy 2.0 ORM, SQLite) enforcing business isolation, audit timestamps, and extraction evidence linkages.
3. **`business-relevance-detection`**: Post-ingestion capability to separate business-relevant communication from personal/unrelated chat messages before downstream AI extraction.
4. **`business-extraction` & Assistant (Downstream)**: Structured entity extraction (orders, inquiries, feedback) and natural-language query resolution for business owners.

---

## 2. Technology Stack

* **Backend:** Python 3.11+ / 3.14, FastAPI, Uvicorn, Pydantic v2
* **Database & ORM:** SQLAlchemy 2.0 (Mapped Column syntax), SQLite (`backend/data/blueprint.db`)
* **Frontend:** Next.js (App Router), TypeScript, React, TailwindCSS (in `frontend/agent-chat-ui`)
* **Testing:** `pytest`, `pytest-asyncio`, `httpx`
* **Change Management:** OpenSpec (`openspec/`) specification-driven development

---

## 3. Core Architectural Rules & Invariants

### A. Strict Raw Ingestion Boundary
* Ingestion **must only** parse, normalize, deduplicate, and persist raw messages, participants, identities, and media attachments.
* **Role Neutrality:** Ingestion **must not** infer or hardcode participant roles (e.g. marking participants as `"customer"` or `"owner"`). `Participant.participant_type` must remain `None` (NULL) during raw ingestion.
* **No AI Extraction During Ingestion:** Ingestion must never invoke LLMs or perform business entity classification. Raw evidence must remain untouched.

### B. Identity Resolution & Scoping
* If a sender contains a valid phone number (E.164-like), treat it as a business-scoped identity.
* If a sender only has a display name, scope the identity to the conversation (`conv:<conversation_ref>:<display_name>`) to prevent cross-conversation identity collisions.
* Never merge identities automatically without explicit confirmation.

### C. Database & Transaction Integrity
* **Multi-Tenant Business Isolation:** Every query, conversation, message, participant, and derived record must preserve explicit business ownership (`business_id`).
* **SQLite Concurrency & Pragmas:**
  * Connections must enforce `PRAGMA foreign_keys = ON` and `PRAGMA busy_timeout = 30000`.
  * The database uses WAL (Write-Ahead Logging) mode for concurrent access.
* **Session Lifecycle:** Use `session_scope()` for transactional service operations. In FastAPI endpoints, release or close route dependencies before launching background ingestion pipelines to avoid SQLite connection locks.

### D. Evidence Traceability
* Every AI-derived record (`Inquiry`, `Order`, `Feedback`, `ExtractedFact`) must reference its supporting raw source `Message` through `ExtractionEvidence` linking records.

---

## 4. Repository Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── database/          # Models (SQLAlchemy), connection, base
│   │   ├── ingestion/         # WhatsApp parser, validator, identity, service
│   │   ├── main.py            # FastAPI application & API endpoints
│   │   └── agent.py           # Core agent interfaces
│   ├── data/
│   │   └── blueprint.db       # SQLite database file (WAL mode)
│   └── requirements.txt
├── frontend/
│   └── agent-chat-ui/         # Next.js web application
├── openspec/
│   ├── specs/                 # Active capability specifications
│   │   ├── business-data-foundation/
│   │   └── whatsapp-ingestion/
│   └── changes/               # Active proposals and archived changes
├── docs/                      # SRS and database schema references
└── tests/                     # Unit and integration test suites
```

---

## 5. Development & Testing Commands

### Backend Server
Run the FastAPI development server with auto-reload:
```bash
cd backend
python -m uvicorn app.main:app --reload
```

### Running Test Suite
Execute tests with `pytest`:
```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run a specific test file
python -m pytest tests/test_whatsapp_ingestion_integrity.py
```

### Frontend UI
Run the Next.js frontend:
```bash
cd frontend/agent-chat-ui
pnpm install
pnpm dev
```

---

## 6. Guidelines for AI Agents

1. **Verify Before Modifying:** Always inspect active code and OpenSpec specifications (`openspec/specs/`) before implementing features or making schema changes.
2. **Preserve Documentation Integrity:** Maintain existing docstrings, comments, and rationale unless explicitly asked to modify them.
3. **Write Unit Tests for Every Change:** All additions to the ingestion pipeline, database models, or API endpoints must be accompanied by comprehensive tests in `tests/`.
4. **Never Break Backward Compatibility:** Do not drop existing tables, remove essential columns, or break existing API response schemas without an explicit migration plan.

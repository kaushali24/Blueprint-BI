# Blueprint BI (ChatInsights)

**Blueprint BI (ChatInsights)** is an AI-powered conversational business intelligence platform designed to help small and independent businesses turn customer conversations into structured business information and actionable insights.

The MVP focuses on **WhatsApp exported chat data** and uses AI to identify customers, inquiries, orders, requirements, and feedback, making this information accessible through analytics and a natural-language business assistant.

> **MVP Goal:** Transform unstructured WhatsApp conversations into structured business knowledge that a business owner can query and understand through AI.

---

## The Problem
Many small and independent businesses manage their customer interactions primarily through WhatsApp.

As conversations grow, valuable business information becomes scattered across informal conversations involving:

- Customer inquiries
- Product and service discussions
- Orders and bookings
- Price discussions
- Order modifications
- Delivery arrangements
- Customer requirements
- Customer feedback
- Text and voice messages
- Images and other media

Manually reviewing these conversations to understand what is happening in the business can become time-consuming and inefficient.

Business owners may want to ask questions such as:

> "What product did customers ask about most?"

> "How many pending orders do I have?"

> "What happened to this customer's order?"

> "What are my recent unresolved inquiries?"

> "What are customers saying about delivery?"

Blueprint BI aims to turn these conversations into an evolving source of structured business knowledge.

---

## The Solution
For the MVP, Blueprint BI processes **WhatsApp exported chat ZIP files** rather than connecting directly to the WhatsApp Business API.

The core workflow is:

```
WhatsApp Export ZIP
        ↓
Data Ingestion
        ↓
Chat Parsing & Normalization
        ↓
Business-Relevance Detection
        ↓
Business Episode Grouping
        ↓
AI Information Extraction
        ↓
Validation & Atomic Replacement
        ↓
Structured Business Data
        ↓
SQLite Database
        ↓
Analytics + AI Business Assistant
        ↓
Business Owner
```

The system is designed so that the current export-based ingestion approach can later be replaced or supplemented by a real-time WhatsApp Business Platform integration.

---

## Testing & Validation
The MVP has been validated through:
- automated backend tests
- API/database verification
- frontend TypeScript/lint/build checks
- manual end-to-end demo scenarios

Supporting evidence:
- [docs/testing/](docs/testing/)
- [docs/SUBMISSION_EVIDENCE.md](docs/SUBMISSION_EVIDENCE.md)
- [docs/architecture/mvp-architecture.md](docs/architecture/mvp-architecture.md)

---

# MVP Features

## 📥 WhatsApp Data Ingestion
- Import WhatsApp exported chat ZIP files
- Parse exported chat text files
- Preserve original conversation data, including media filenames
- Detect duplicate messages
- Support **incremental imports** when an updated export is provided
- Show recent import history and processing status

The MVP does **not** provide real-time WhatsApp synchronization.

---

## 🌍 Multilingual Conversation Understanding
The MVP is designed to evaluate conversations containing:
- English
- Sinhala
- Singlish / Romanized Sinhala
- English + Sinhala mixed conversations
- Informal conversational language

The system understands business intent across these languages, converting informal texts into structured order and inquiry entities.

---

## 🧠 AI Business Information Extraction
The system extracts useful business information from relevant conversations, including:
- Customers
- Customer Inquiries
- Products/services
- Quantities
- Prices
- Confirmed Orders
- Pending Orders / Quotes
- Customer Feedback

AI-derived information is grounded, keeping explicit relational links to the originating WhatsApp `message_ids` for evidence.

---

## 👥 Customer Intelligence & Resolution
The system associates customer interactions using available WhatsApp identity, participant, and conversation metadata. Customer resolution is heuristic and is designed to preserve existing identities conservatively during imports.

Important merges or CRM-like contact management require human-in-the-loop review (future scope).

---

## 📦 Order & Inquiry Intelligence
The system isolates distinct business episodes to correctly classify orders.
Current states include:
- **Pending** (e.g., quotes, unconfirmed intent)
- **Confirmed** (e.g., agreed purchases)
- **Cancelled**

Inquiries (unresolved questions) are tracked distinctly from orders.

---

## 💬 Customer Feedback
Customers may provide useful feedback after receiving a product or service. Blueprint BI identifies feedback (positive, negative, neutral) regarding product quality, delivery, and taste.

Feedback remains tied to the specific message evidence and survives incremental re-imports.

---

## 📊 Business Insights & Analytics
The MVP provides deterministic, structured business analytics, such as:
- Total known customers and repeat customer count
- Total inquiries and open/unresolved inquiries
- Pending orders
- Confirmed orders
- Confirmed revenue (explicitly excluding pending quotes)
- Top products (by confirmed volume)
- Feedback metrics and recent feedback

Quantitative calculations are performed via backend SQL aggregations, strictly bounding the LLM to prevent hallucination of core metrics.

---

## 🤖 Natural-Language Business Assistant
The LangGraph-powered AI assistant allows the business owner to ask questions naturally in English, Sinhala, or Singlish.

The Assistant uses deterministic tools to query the Analytics layer and database. Markdown responses are rendered in the frontend.

Browser chat-session history supports navigation and persistence. The backend assistant remains strictly stateless between API requests.

---

# Multimodal Limitations
- **Media Preservation:** Media references and filenames are preserved from the ZIP exports.
- **Image/Voice Interpretation:** Advanced image understanding and voice-to-text are out of scope for the current MVP.

---

# Human-in-the-Loop Validation
AI extraction can be uncertain. Important AI-derived information provides direct links back to the original WhatsApp message evidence, ensuring the business owner can verify the AI's conclusions. Direct editing and identity merges are identified as necessary future features.

---

# MVP Scope
## ✅ Must Have
- WhatsApp ZIP ingestion, parsing, duplicate detection, incremental import
- English/Sinhala/Singlish evaluation
- SQLite database persistence
- Customer, Inquiry, Order (Pending/Confirmed), and Feedback extraction
- Business/personal relevance detection
- Basic deterministic analytics
- AI business assistant with tool use
- Source/evidence references
- Next.js responsive frontend (Overview, Imports, Orders, Inquiries, Assistant)

## 🔵 Future Scope
- Real-time WhatsApp Business API integration
- Advanced multimodal understanding (Images/Voice)
- Advanced customer identity resolution UI
- PostgreSQL-based production storage
- Full CRM capabilities
- Production Authentication/Authorization

---

# MVP Architecture

See [docs/architecture/mvp-architecture.md](docs/architecture/mvp-architecture.md) for the detailed architecture diagram and technical boundaries.

---

# Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | Python, FastAPI |
| Database | SQLite, SQLAlchemy |
| Agent | LangGraph, LangChain |
| AI Model | Gemini 3.6 Flash |
| Development | OpenSpec, AI-Assisted Iteration |

---

# Project Structure

```text
Blueprint-BI/
├── backend/
│   ├── app/
│   │   ├── analytics/
│   │   ├── api/
│   │   ├── assistant/
│   │   ├── database/
│   │   ├── extraction/
│   │   ├── ingestion/
│   │   └── relevance/
│   ├── scripts/
│   └── .env.example
├── frontend/
│   └── agent-chat-ui/
│       ├── src/
│       │   ├── app/
│       │   ├── components/
│       │   ├── hooks/
│       │   └── lib/
│       ├── .env.example
│       └── package.json
├── demo-data/
├── docs/
│   ├── architecture/
│   ├── development/
│   ├── testing/
│   └── SUBMISSION_EVIDENCE.md
├── openspec/
│   ├── changes/
│   └── specs/
├── tests/
├── pytest.ini
└── README.md
```

---

# Development Methodology
Blueprint BI utilizes a **Hybrid Development Methodology**:
- **Specification-Driven Development (OpenSpec):** Used for foundational architectural capabilities and selected planned changes.
- **AI-Assisted Direct Iteration:** AI coding agents were used extensively for implementation assistance, debugging, UX, testing, and hardening. Changes were reviewed using code inspection, tests, and manual verification. Not every AI-assisted change has an OpenSpec artifact.

For detailed evidence, see [docs/development/ai-assisted-development.md](docs/development/ai-assisted-development.md) and [docs/development/development-methodology.md](docs/development/development-methodology.md).

---

# Getting Started

## Prerequisites
- Python 3.11
- Node.js & pnpm
- Git

## Backend
```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt

# Windows PowerShell:
Copy-Item .env.example .env
# macOS/Linux:
# cp .env.example .env
```
*(Add your `GOOGLE_API_KEY` to the `.env` file)*

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Frontend
```bash
cd frontend/agent-chat-ui
pnpm install

# Windows PowerShell:
Copy-Item .env.example .env
# macOS/Linux:
# cp .env.example .env

pnpm dev
```
Access the application at `http://localhost:3000`.

---

# Current Status
✅ **MVP Development — AI LaunchPad — COMPLETED**

The core MVP development is **successfully completed** according to the SRS and OpenSpec specifications. Current focus is demo preparation and submission readiness.

### Development achievements

1. ✅ WhatsApp data ingestion
2. ✅ Reliable structured data storage
3. ✅ AI business information extraction
4. ✅ Business analytics & dashboard
5. ✅ AI business assistant (English, Sinhala, Singlish)
6. ✅ Customer insights drill-down
7. ✅ End-to-end MVP validation (181 backend tests passed)

---

# Future Direction
After validating the MVP, the ingestion layer could evolve from:

```
WhatsApp Export ZIP
        ↓
ChatInsights
```
to:

```
WhatsApp Business Platform
        ↓
Webhook / API
        ↓
ChatInsights
        ↓
Real-Time Business Knowledge
```
Other potential future capabilities include:

- Advanced multimodal conversation understanding
- Video analysis
- Better customer identity resolution
- Semantic conversation search / RAG
- Business forecasting
- Customer segmentation
- Cloud deployment
- PostgreSQL-based production storage
- CRM integrations

---

# License
See the relevant project/license files for licensing information.

---
**Last Updated:** 2026-08-26

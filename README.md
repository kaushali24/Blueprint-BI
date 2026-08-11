# Blueprint BI
**Blueprint BI (ChatInsights)** is an AI-powered conversational business intelligence platform designed to help small and independent businesses turn customer conversations into structured business information and actionable insights.

The initial MVP focuses on **WhatsApp exported chat data** and uses AI to identify customers, inquiries, orders, requirements, and feedback, making this information accessible through analytics and a natural-language business assistant.

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

> "How many inquiries became orders?"

> "What happened to this customer's order?"

> "What questions do customers ask most frequently?"

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
AI Information Extraction
        ↓
Validation
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

# MVP Features

## 📥 WhatsApp Data Ingestion

- Import WhatsApp exported chat ZIP files
- Parse exported chat text files
- Detect associated media
- Import multiple conversations
- Preserve original conversation data
- Detect duplicate messages
- Support incremental imports when an updated export is provided
- Show import and processing status
For example:

```
Initial export:
100 messages

Updated export:
120 messages

System:
100 existing messages
20 new messages

Database:
120 messages
```
The MVP does **not** provide real-time WhatsApp synchronization.

---

## 🌍 Multilingual Conversation Understanding
The MVP is designed to evaluate conversations containing:

- English
- Sinhala
- Singlish / Romanized Sinhala
- English + Sinhala mixed conversations
- Informal conversational language
Example:

```
"1kg chocolate cake eka kiyada?"
```
The system should understand this as a business inquiry about the price of a 1kg chocolate cake rather than treating it as ordinary English text.

---

## 🧠 AI Business Information Extraction
The system extracts useful business information from relevant conversations, including:

- Customers
- Customer inquiries
- Products/services
- Quantities
- Dates
- Prices
- Requirements
- Order status
- Customer feedback
Example:

```
Customer:
"Actually 1.5kg karanna."

Extracted information:

Intent:
Order modification

Product:
Chocolate cake

Quantity:
1.5 kg
```
AI-derived information should remain associated with its source conversation/message where possible.

---

## 👥 Customer & Conversation Intelligence
The system organizes customer interactions into structured records.

A customer profile can provide:

- Customer/contact information
- Conversation history
- Inquiries
- Orders
- Feedback
- Last interaction
The system also considers customer identity edge cases.

For example:

- Two customers may have the same name.
- One customer may contact the business using multiple WhatsApp numbers.
- A family member or friend may contact the business on behalf of another person.
A new WhatsApp number will initially be treated as a separate identity. Potential relationships may be suggested, but important identity merges should require business-owner confirmation.

---

## 📦 Order & Inquiry Intelligence
The system identifies business inquiries and confirmed orders from conversations.

It can capture information such as:

```
Customer
Product / Service
Quantity
Price
Date
Delivery / Service requirements
Order status
```
Possible order states include:

- Inquiry
- Confirmed
- Completed
- Cancelled
- Unknown
The system should also recognize basic order modifications.

---

## 💬 Customer Feedback
Customers may provide useful feedback after receiving a product or service.

Blueprint BI aims to identify:

- Positive feedback
- Negative feedback
- Mixed feedback
- Neutral feedback
Potential feedback topics include:

- Product quality
- Taste
- Appearance
- Delivery
- Price
- Customer service
- Customization
This allows the business owner to understand not only what customers **ordered**, but also what they **said afterwards**.

---

## 📊 Business Insights & Analytics
The MVP provides structured business analytics such as:

- Total customers
- New customers
- Returning customers
- Total inquiries
- Confirmed orders
- Inquiry-to-order conversion
- Frequently requested products/services
- Frequently asked questions
- Customer feedback patterns
Quantitative calculations are performed using structured business data rather than relying only on the language model.

---

## 🤖 Natural-Language Business Assistant
The business owner can ask questions naturally instead of manually searching through conversations.

Examples:

```
"What product was requested most frequently?"

"How many inquiries became orders?"

"What happened to Nethmi's order?"

"What are customers asking about most?"

"Who are my returning customers?"

"What are customers saying about delivery?"
```
The AI assistant uses controlled tools to retrieve relevant business data and conversations before generating an answer.

Where possible, important answers should provide supporting conversation/data references.

---

# Multimodal Data
WhatsApp conversations can contain different types of media.

### MVP Priority
Text conversation processing is the primary focus.

### Secondary / Optional
The architecture may support:

- Images
- Voice notes
- Post-call voice summaries

### Future
Advanced video understanding is outside the core MVP.

Future processing could potentially combine:

```
Video
 ├── Key frames → Vision
 └── Audio → Speech-to-text
                  ↓
           Multimodal analysis
```
Direct WhatsApp voice/video call recording and analysis are **not part of the MVP**.

---

# Human-in-the-Loop Validation
AI extraction can be uncertain.

Therefore, important AI-derived information should be reviewable by the business owner.

For example:

```
Possible customer match

Customer A
        ↕
Customer B

The system believes these may be
the same customer.

[Confirm]   [Keep Separate]
```
Similarly, uncertain order or customer information can be reviewed and corrected.

The goal is not to assume that the AI is always correct, but to provide useful automation while keeping the business owner in control.

---

# MVP Scope

## ✅ Must Have

- WhatsApp ZIP ingestion
- Chat parsing
- Message normalization
- SQLite database
- Duplicate detection
- Incremental import
- Customer extraction
- Inquiry extraction
- Order extraction
- Basic feedback extraction
- Business/personal relevance detection
- English/Sinhala/Singlish evaluation
- Basic business analytics
- AI business assistant
- Database/analytics tools
- Source/evidence references

## 🟡 Should Have

- Basic image processing
- Voice-note transcription
- Customer search/filtering
- Customer identity suggestions
- Post-call voice summaries
- Mobile-responsive interface

## 🔵 Future Scope

- Real-time WhatsApp Business API integration
- WhatsApp webhooks
- Automatic WhatsApp messaging
- Direct WhatsApp call recording
- Advanced video understanding
- Advanced customer identity resolution
- Advanced forecasting
- Full CRM capabilities
- Accounting/payment integration
- Production-scale infrastructure

---

# MVP Architecture

```
                    WhatsApp Export ZIP
                           │
                           ▼
                    Ingestion Service
                           │
                           ▼
                  Chat / Media Parser
                           │
                           ▼
                 Message Normalization
                           │
                           ▼
               Business Relevance Check
                           │
                           ▼
               AI Information Extraction
                           │
                           ▼
                     Validation
                           │
                           ▼
                        SQLite
                    ┌──────┴──────┐
                    │             │
                    ▼             ▼
                Analytics     Agent Tools
                                  │
                                  ▼
                           LangGraph Agent
                                  │
                                  ▼
                         AI Business Assistant
                                  │
                                  ▼
                           Business Owner
```

---

# Technology Stack
LayerTechnologyFrontendNext.jsBackendPython + FastAPIDatabaseSQLiteORMSQLAlchemyAgentLangGraphLLM FrameworkLangChainAI ModelLLM with structured-output capabilitiesDevelopmentAI-assisted developmentSpecificationOpenSpecVersion ControlGit / GitHubTechnology choices may evolve during MVP development where necessary, while the SRS and OpenSpec specifications remain the source of truth for requirements.

---

# Project Structure

```
Blueprint BI/
│
├── backend/
│   ├── app/
│   │   ├── agent.py
│   │   └── ...
│   ├── requirements.txt
│   └── langgraph.json
│
├── frontend/
│   └── agent-chat-ui/
│       ├── src/
│       ├── package.json
│       └── README.md
│
├── docs/
│   └── SRS.md
│
├── openspec/
│   ├── specs/
│   └── changes/
│
├── tests/
│
├── data/
│
└── README.md
```

> The exact project structure may evolve as implementation progresses.

---

# Three-Week MVP Roadmap
The MVP is being developed using a highly focused three-week schedule.

## Week 1 — Data Foundation
**Goal:** Reliably ingest WhatsApp exported data.

```
WhatsApp ZIP
      ↓
ZIP Extraction
      ↓
Chat Parser
      ↓
Message Normalization
      ↓
SQLite
      ↓
Duplicate Detection
      ↓
Incremental Import
      ↓
Conversation Viewer
```

### Milestone M1
**Reliable WhatsApp Data Foundation**

---

## Week 2 — Business Intelligence
**Goal:** Transform conversations into structured business knowledge.

```
Conversation
      ↓
AI Extraction
      ↓
Business Relevance
      ↓
Customers
      ↓
Inquiries
      ↓
Orders
      ↓
Feedback
      ↓
Analytics
```

### Milestone M2
**Conversation → Business Intelligence**

---

## Week 3 — AI Assistant & MVP Integration
**Goal:** Make the system usable and demonstrable.

```
Structured Data
      +
Analytics
      ↓
Agent Tools
      ↓
LangGraph Agent
      ↓
AI Business Assistant
      ↓
Dashboard
```

### Milestone M3
**Demonstrable ChatInsights MVP**

The core functional MVP is targeted for completion during the **first half of Week 3**.

The remainder of Week 3 is reserved for:

- Testing
- Bug fixing
- Evaluation
- UI refinement
- Demo dataset preparation
- Documentation
- Demonstration preparation

---

# Development Methodology
Blueprint BI follows a **Specification-Driven Development (SDD)** approach using OpenSpec.

The project uses different levels of documentation for different purposes:

```
SRS
 │
 │ Overall product requirements
 ▼
OpenSpec
 │
 │ Feature-level specifications
 ▼
Implementation
 │
 │ AI-assisted development
 ▼
Testing
 │
 ▼
Validated Feature
```
The general OpenSpec workflow is:

```
Explore
   ↓
Propose
   ↓
Review Specification
   ↓
Apply
   ↓
Test
   ↓
Archive
```
The SRS defines the overall MVP boundary, while OpenSpec changes define individual implementation capabilities.

---

# Getting Started

## Prerequisites

- Python 3.10+
- Node.js
- pnpm
- Git

## Backend

```
cd backend

python -m venv .venv
```

### Windows

```
.venv\Scripts\activate
```

### macOS / Linux

```
source .venv/bin/activate
```
Install dependencies:

```
pip install -r requirements.txt
```
Start the backend using the project's configured FastAPI/LangGraph development command.

> The exact command may change as the backend architecture is implemented. Keep this section synchronized with the actual project configuration.

---

## Frontend

```
cd frontend/agent-chat-ui

pnpm install
pnpm dev
```
The development frontend is expected to run at:

```
http://localhost:3000
```

---

# Environment Variables
Environment configuration will depend on the selected AI provider and backend implementation.

Example:

```
# Backend
API_URL=http://localhost:8000

# AI provider configuration
# Add provider-specific variables here
```
Do not commit API keys or other secrets to the repository.

---

# Documentation
The project documentation is organized as follows:

DocumentPurpose`README.md`Project overview, setup, scope, and development roadmap`docs/SRS.md`Complete MVP software requirements`openspec/specs/`Current feature specifications`openspec/changes/`Feature-level implementation changes`frontend/agent-chat-ui/README.md`Frontend-specific documentation
---

# Current Status
🚧 **MVP Development — AI LaunchPad**

### Current focus
Building the three-week MVP according to the SRS and OpenSpec specifications.

### Development priorities

1. WhatsApp data ingestion
2. Reliable structured data storage
3. AI business information extraction
4. Business analytics
5. AI business assistant
6. End-to-end MVP validation

---

# Important MVP Constraints
The current MVP intentionally does **not** attempt to provide real-time WhatsApp synchronization.

The initial data flow is:

```
WhatsApp
    ↓
Export Chat
    ↓
ZIP File
    ↓
ChatInsights
```
This allows the core business intelligence problem to be validated before investing in WhatsApp Business Platform/API integration.

Similarly, advanced video processing, full CRM functionality, accounting, payments, and advanced forecasting are outside the current MVP scope.

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
**Last Updated:** 2026-08-10

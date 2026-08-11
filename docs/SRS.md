# Software Requirements Specification
 
# Blueprint BI / ChatInsights

**Project:** AI LaunchPad Rapid MVP  
**Project Name:** ChatInsights  
**Working/Technical Name:** Blueprint BI  
**Version:** 2.0 — MVP-Focused SRS  
**Development Methodology:** Specification-Driven Development (SDD)  
**Development Duration:** 3 Weeks  
**Development Approach:** AI-assisted rapid prototyping  
**Primary Prototype Domain:** Small independent business — Home Bakery  
**Target User:** Small / Independent Business Owner

---

# 1. Document Purpose

This Software Requirements Specification defines the requirements, boundaries, architecture, priorities, acceptance criteria, and development milestones for the **three-week MVP of ChatInsights**.

The purpose of this document is to provide a precise specification that can be used during rapid AI-assisted development.

The SRS is intentionally focused on delivering a **complete working MVP within three weeks** rather than attempting to implement the full long-term product vision.

The system shall demonstrate that unstructured WhatsApp customer conversations can be transformed into structured business information and then used to provide useful business analytics and AI-assisted answers.

---

# 2. Product Vision

## 2.1 Product Description

ChatInsights is an AI-powered business intelligence assistant for small and independent businesses that primarily communicate with customers through WhatsApp.

The system processes exported WhatsApp conversations and extracts useful business information such as:

- Customers
- Inquiries
- Orders
- Products/services
- Requirements
- Customer feedback
- Conversation trends

The extracted information is stored in a structured database and made available through:

1. A business dashboard.
2. Basic analytics.
3. A natural-language AI business assistant.

---

# 3. Core Problem

Small businesses often manage their customer relationships almost entirely through informal WhatsApp conversations.

These conversations may contain:

- Customer inquiries
- Orders
- Price discussions
- Product requirements
- Delivery information
- Changes to orders
- Customer feedback
- English
- Sinhala
- Singlish
- Code-mixed language
- Images
- Voice notes
- Other media

As the number of conversations increases, it becomes difficult for the business owner to manually identify patterns and answer questions such as:

> "What product did customers ask about most?"

> "How many inquiries became orders?"

> "What happened to this customer's order?"

> "What questions do customers ask repeatedly?"

> "What are customers saying after receiving their orders?"

> "Which customers are returning?"

The system addresses this problem by converting conversational data into an evolving business knowledge base.

---

# 4. MVP Goal

The MVP shall prove the following complete workflow:

```text
WhatsApp Export ZIP
        ↓
Data Ingestion
        ↓
Chat Parsing
        ↓
Message Normalization
        ↓
Business-Relevance Detection
        ↓
AI Information Extraction
        ↓
Structured Business Data
        ↓
SQLite Database
        ↓
Business Analytics
        ↓
AI Business Assistant
        ↓
Business Owner
```

The MVP is considered successful when a business owner can upload a realistic WhatsApp export and subsequently ask useful business questions about the imported data.

---

# 5. Three-Week Constraint

The development period is limited to **three weeks**.

Therefore:

> **The MVP shall prioritize depth and completeness of one end-to-end workflow over breadth of features.**

The final MVP should be functionally complete by the **first half of Week 3**, leaving the second half of Week 3 for:

- Testing
- Bug fixing
- Evaluation
- Demonstration preparation
- Documentation
- Refinement

---

# 6. MVP Scope Strategy

## 6.1 Must Have

The following are mandatory:

1. WhatsApp ZIP import.
2. Chat parsing.
3. Message normalization.
4. SQLite database.
5. Duplicate detection.
6. Incremental import.
7. Basic English/Sinhala/Singlish understanding.
8. Business relevance detection.
9. Customer extraction.
10. Inquiry extraction.
11. Order extraction.
12. Basic feedback extraction.
13. Structured business records.
14. Basic dashboard.
15. Business analytics.
16. AI business assistant.
17. Database/analytics tools for the assistant.
18. Evidence/source reference for important answers.
19. Human review for uncertain extracted records.
20. A realistic demonstration dataset.

---

# 7. MVP Scope Classification

## Must Have — MVP

| Capability | Priority |
|---|---|
| WhatsApp ZIP ingestion | MUST |
| TXT parsing | MUST |
| Multiple chat import | MUST |
| Incremental import | MUST |
| Duplicate detection | MUST |
| SQLite | MUST |
| Customer extraction | MUST |
| Inquiry extraction | MUST |
| Order extraction | MUST |
| Basic feedback extraction | MUST |
| English/Sinhala/Singlish | MUST |
| Business relevance detection | MUST |
| Dashboard | MUST |
| Basic analytics | MUST |
| AI assistant | MUST |
| Structured database tools | MUST |
| Source/evidence references | MUST |
| Human review | MUST |
| Testing | MUST |

## Should Have

| Capability | Priority |
|---|---|
| Basic image understanding | SHOULD |
| Voice-note transcription | SHOULD |
| Post-call voice summary | SHOULD |
| Customer identity suggestions | SHOULD |
| Customer search/filtering | SHOULD |
| Mobile-responsive UI | SHOULD |

## Could Have

| Capability | Priority |
|---|---|
| Advanced feedback categorization | COULD |
| Advanced customer segmentation | COULD |
| Advanced visualization | COULD |
| Key-frame video analysis | COULD |
| Advanced multimodal processing | COULD |

## Won't Have in MVP

| Capability | Status |
|---|---|
| Real-time WhatsApp API | WON'T |
| WhatsApp webhook integration | WON'T |
| Automatic WhatsApp messaging | WON'T |
| Direct WhatsApp call recording | WON'T |
| Direct WhatsApp video-call analysis | WON'T |
| Advanced video understanding | WON'T |
| Full CRM | WON'T |
| Accounting system | WON'T |
| Payment processing | WON'T |
| Production-scale infrastructure | WON'T |
| Complex forecasting | WON'T |

---

# 8. Target Prototype

The primary prototype scenario shall be a **Sri Lankan home bakery**.

Example conversations may contain:

```text
Customer:
"Hi akka, 1kg chocolate cake eka kiyada?"

Customer:
"Sunday delivery karanna puluwanda?"

Customer:
"Actually 1.5kg karanna."

Customer:
"Last cake eka godak lassanai ❤️"
```

The system should transform these into structured information.

Example:

```text
Customer:
Unknown → identified customer

Inquiry:
Chocolate cake

Order:
1.5kg chocolate cake

Delivery:
Sunday

Feedback:
Positive
```

The same underlying architecture should remain usable for other independent businesses.

---

# 9. System Boundary

## 9.1 MVP Input

The primary input is:

```text
WhatsApp Export ZIP
```

containing:

```text
_chat.txt
Images
Audio
Videos
Documents
Other supported media
```

## 9.2 MVP Output

The system shall produce:

```text
Structured business data
+
Analytics
+
Business insights
+
AI answers
```

---

# 10. High-Level Architecture

```text
                    FRONTEND
                       |
                       v
                 FastAPI Backend
                       |
       +---------------+---------------+
       |                               |
       v                               v
 Ingestion Service              AI Assistant
       |                               |
       v                               v
 Processing Pipeline            Agent Tools
       |                               |
       +---------------+---------------+
                       |
                       v
                    SQLite
                       |
             +---------+---------+
             |                   |
             v                   v
        Business Data        Analytics
```

---

# 11. Recommended MVP Technology Direction

The exact technology can be adjusted during implementation, but the intended architecture is:

### Frontend

**Next.js**

### Backend

**Python + FastAPI**

### AI/Agent

**LangGraph / LangChain**

### Database

**SQLite**

### ORM

**SQLAlchemy**

### AI model

A suitable LLM with structured output and multilingual capabilities.

### Speech-to-text

A suitable speech-to-text model/service if voice notes are included.

### Vision

A suitable vision-capable model if image processing is included.

### Development

AI-assisted development using coding agents/tools, with the SRS acting as the specification source.

---

# 12. Functional Requirements

# 12.1 WhatsApp Data Import

### FR-001 — Upload Export

The system shall allow the business owner to provide a WhatsApp exported chat ZIP.

### FR-002 — ZIP Validation

The system shall verify that the uploaded file is a supported WhatsApp export.

### FR-003 — ZIP Extraction

The system shall extract the contents of the ZIP for processing.

### FR-004 — Chat File Detection

The system shall identify the exported chat text file.

### FR-005 — Media Detection

The system shall identify media files associated with messages.

### FR-006 — Import Status

The system shall provide an import status:

- Processing
- Completed
- Partially completed
- Failed

### FR-007 — Import Summary

The system shall show:

- Number of conversations
- Number of messages
- Number of new messages
- Number of duplicates
- Number of media files
- Processing errors

---

# 13. Message Parsing

### FR-008 — Parse Messages

The system shall parse supported WhatsApp message formats.

### FR-009 — Extract Timestamp

The system shall extract timestamps.

### FR-010 — Extract Sender

The system shall identify the sender.

### FR-011 — Identify Message Type

Supported types:

```text
text
image
audio
video
document
system
```

### FR-012 — Preserve Original Content

The original message content shall be retained.

---

# 14. Incremental Import

This is an important MVP requirement because WhatsApp exports are not real-time.

### FR-013 — Existing Conversation Detection

The system shall determine whether an imported conversation already exists.

### FR-014 — Duplicate Detection

The system shall identify messages that have already been imported.

### FR-015 — Duplicate Prevention

Previously imported messages shall not be duplicated.

### FR-016 — Incremental Update

When a new export contains old and new messages, only new messages shall be added.

Example:

```text
Existing:
100 messages

New export:
120 messages

Result:
100 existing
20 new

Database:
120 total
```

### FR-017 — Data Freshness

The system shall display when business data was last updated.

Example:

> Last updated: August 9, 2026, 10:42 AM

---

# 15. Multilingual Processing

### FR-018 — English

The system shall process English business conversations.

### FR-019 — Sinhala

The system shall process Sinhala where supported.

### FR-020 — Singlish

The system shall process Romanized Sinhala/Singlish.

### FR-021 — Code Mixing

The system shall process mixed English/Sinhala/Singlish conversations.

Example:

> "1kg chocolate cake eka kiyada?"

### FR-022 — Informal Language

The system should handle informal spelling and conversational expressions.

### FR-023 — Business Meaning

The system shall prioritize understanding business meaning rather than performing literal translation.

---

# 16. Business Relevance

A WhatsApp export can contain personal conversations.

### FR-024 — Relevance Classification

The system shall classify conversational content as:

- Business relevant
- Personal
- Uncertain

### FR-025 — Mixed Conversation

The system shall allow different messages within the same conversation to have different relevance.

Example:

```text
"Hi akka kohomada?"
→ Personal/social

"1kg chocolate cake eka kiyada?"
→ Business

"Saturday delivery puluwanda?"
→ Business
```

### FR-026 — Personal Data Exclusion

Personal/irrelevant content shall not unnecessarily contribute to business analytics.

### FR-027 — Uncertain Content

Uncertain content shall not be treated as confirmed business facts.

---

# 17. Customer Management

### FR-028 — Customer Creation

The system shall create customer/contact records from relevant conversations.

### FR-029 — Customer Search

The owner shall be able to search customers.

### FR-030 — Customer Profile

The system shall show:

- Conversations
- Inquiries
- Orders
- Feedback
- Last interaction

### FR-031 — Multiple Numbers

The system shall support multiple WhatsApp identities associated with a customer.

### FR-032 — Conservative Identity Resolution

A new WhatsApp number shall initially be treated as a separate identity.

### FR-033 — Same Name Protection

Matching names shall not automatically result in merging.

### FR-034 — Potential Duplicate Suggestion

The system may suggest that two contacts could represent the same customer.

### FR-035 — Owner Confirmation

The owner may confirm or reject the suggested relationship.

**Automatic merging is not required for MVP.**

This is an important scope reduction.

---

# 18. Inquiry Extraction

### FR-036 — Inquiry Detection

The system shall identify customer inquiries.

Examples:

- Price inquiry
- Availability inquiry
- Product inquiry
- Service inquiry
- Delivery inquiry
- General business question

### FR-037 — Inquiry Details

The system should extract:

- Customer
- Product/service
- Quantity
- Date
- Relevant requirements
- Conversation reference

### FR-038 — Inquiry Status

Possible statuses:

```text
New
Pending
Converted
Not converted
Unknown
```

---

# 19. Order Extraction

### FR-039 — Order Detection

The system shall identify confirmed orders where sufficient evidence exists.

### FR-040 — Order Details

The system should extract:

- Customer
- Product/service
- Quantity
- Price
- Date
- Delivery/service details
- Requirements

### FR-041 — Order Modification

The system should detect basic order changes.

Example:

```text
1kg
↓
1.5kg
```

### FR-042 — Order Status

Supported MVP states:

```text
Inquiry
Confirmed
Completed
Cancelled
Unknown
```

---

# 20. Customer Feedback

### FR-043 — Feedback Detection

The system shall identify relevant customer feedback.

### FR-044 — Post-Order Feedback

The system should associate feedback with a previous order where possible.

### FR-045 — Basic Feedback Classification

MVP classifications:

```text
Positive
Negative
Mixed
Neutral
Unknown
```

### FR-046 — Feedback Topic

The system may identify basic topics:

- Product
- Taste/quality
- Delivery
- Price
- Service
- Design/customization

### FR-047 — Feedback Evidence

Feedback shall retain a source message reference.

---

# 21. Media Processing

Because of the three-week constraint, media processing must be carefully scoped.

## 21.1 Images

### FR-048

The system should identify image attachments.

### FR-049

If implemented, the system may use vision/OCR to understand relevant images.

### MVP limitation

Image understanding is **secondary to the text pipeline**.

---

## 21.2 Voice Notes

### FR-050

The system shall identify audio attachments.

### FR-051

If included in the MVP, voice notes shall be converted to text using speech-to-text.

### FR-052

The transcript shall be associated with the original audio message.

---

## 21.3 Videos

Advanced video understanding is outside the MVP.

The system shall:

- Detect videos.
- Preserve video metadata.
- Preserve the association with the original message.

Future architecture may support:

```text
Video
├── Key frames
│      ↓
│   Vision
│
└── Audio
       ↓
 Speech-to-text
```

This should not consume Week 1 or Week 2 development time.

---

# 22. Post-Call Summary

A lightweight post-call feature may be included if the core MVP is stable.

### FR-053

The owner may record/provide a short summary after a customer call.

### FR-054

The system may transcribe the summary.

### FR-055

The system may extract business information.

### FR-056

The owner shall review important extracted changes before they affect business records.

This feature is **Should Have**, not a core dependency.

---

# 23. Database Requirements

The MVP shall use SQLite.

Core entities:

```text
Business
Customer
Contact / WhatsApp Identity
Conversation
Participant
Message
Media
Inquiry
Order
OrderItem
Feedback
ExtractedFact
```

The database shall preserve relationships between:

```text
Customer
   ↓
Conversation
   ↓
Message
   ↓
Extracted Fact
```

and:

```text
Customer
   ↓
Inquiry
   ↓
Order
   ↓
Feedback
```

---

# 24. Raw Data and AI Data Separation

The system shall distinguish:

### Raw data

What was actually imported.

```text
Original message
Original timestamp
Original sender
Original media
```

### Derived data

What the AI interpreted.

```text
Intent
Order
Product
Quantity
Sentiment
Feedback
```

Example:

```text
Source message:
"Actually make it 1.5kg."

Derived fact:
order.quantity = 1.5kg
```

The source message should remain available.

---

# 25. AI Extraction Requirements

The LLM shall use structured output schemas.

Example:

```json
{
  "intent": "order_modification",
  "product": "chocolate cake",
  "quantity": "1.5kg",
  "confidence": 0.93,
  "source_message_id": 128
}
```

The system shall validate AI output before storing important business records.

The LLM shall not directly manipulate the database without backend validation.

---

# 26. AI Business Assistant

The AI assistant is a **core MVP feature**.

### FR-057 — Natural Language Question

The owner shall be able to ask business questions naturally.

### FR-058 — Customer Questions

Example:

> "What happened to Nethmi's order?"

### FR-059 — Product Questions

Example:

> "What product did customers ask about most?"

### FR-060 — Inquiry Questions

Example:

> "What are customers asking most frequently?"

### FR-061 — Conversion Questions

Example:

> "How many inquiries became orders?"

### FR-062 — Feedback Questions

Example:

> "What are customers saying about delivery?"

### FR-063 — Customer Questions

Example:

> "Who are my returning customers?"

---

# 27. Agent Tool Requirements

The agent shall use tools rather than relying entirely on the LLM's internal reasoning.

MVP tools:

```text
search_customers
get_customer_history
search_conversations
get_order
search_orders
get_feedback
query_business_metrics
```

Potentially:

```text
search_inquiries
get_insight_evidence
```

The agent should select the appropriate tool based on the user's question.

---

# 28. Database vs LLM Responsibilities

## Database / Analytics

Responsible for:

- Counts
- Filtering
- Sorting
- Aggregation
- Dates
- Conversion rates
- Customer lists
- Order lists

## LLM

Responsible for:

- Language understanding
- Conversation interpretation
- Extraction
- Summarization
- Insight explanation
- Natural-language interaction

The system shall avoid asking the LLM to perform calculations that can be reliably performed using structured data.

---

# 29. AI Evidence Requirements

The assistant should provide evidence where appropriate.

Example:

> Chocolate cake was the most requested product, with 37 inquiries.

Then:

```text
Based on:
37 inquiries
21 confirmed orders

[View supporting conversations]
```

The system should not present unsupported assumptions as facts.

---

# 30. Dashboard Requirements

The dashboard shall focus on answering:

> **What is happening in my business?**

MVP dashboard sections:

### Summary

```text
Total inquiries
Confirmed orders
New customers
Returning customers
```

### Top products/services

```text
Chocolate Cake — 37 inquiries
Red Velvet — 21 inquiries
Cupcakes — 17 inquiries
```

### Recent activity

```text
New inquiry
New order
Feedback
```

### Needs attention

```text
Pending inquiries
Uncertain extraction
Potential duplicate customer
```

### Recent insights

```text
Most requested product
Common question
Feedback trend
```

---

# 31. Customer Interface

The MVP customer interface shall provide:

### Customer List

- Name/identifier
- Number of inquiries
- Number of orders
- Last interaction

### Search

```text
[ Search customer... ]
```

### Customer Profile

```text
Customer
   ↓
Conversation history
   ↓
Orders
   ↓
Feedback
```

The system should support at least **hundreds of customers** conceptually.

The MVP should test with approximately **500 synthetic/realistic customer records** if feasible.

---

# 32. Conversation Interface

The owner shall be able to inspect:

- Conversation
- Timestamp
- Sender
- Message
- Media reference
- Extracted business information

The conversation view shall help the owner understand **why the system produced a particular business fact**.

---

# 33. Privacy and Security

The system processes potentially sensitive personal conversations.

### NFR-001

Business data shall be isolated between business accounts.

### NFR-002

Raw conversation data shall not be exposed unnecessarily.

### NFR-003

Access to business information shall require appropriate authentication in the deployed prototype.

### NFR-004

Personal conversation content should not be used for business insights unless classified as relevant.

### NFR-005

AI processing should use only required conversation context where feasible.

---

# 34. Performance Requirements

Because this is a rapid prototype, performance targets should be realistic.

### NFR-006

The system shall process a representative MVP dataset within an acceptable prototype processing time.

### NFR-007

The UI shall remain usable with hundreds of customers and thousands of messages.

### NFR-008

Customer lists shall support search and pagination where necessary.

### NFR-009

Repeated imports shall avoid unnecessary reprocessing of unchanged messages.

---

# 35. Reliability Requirements

### NFR-010

Repeated imports shall be idempotent.

### NFR-011

A failure in AI processing shall not destroy successfully imported raw data.

### NFR-012

Media processing failures shall not prevent text data from being stored.

### NFR-013

AI extraction failures shall be recorded and identifiable.

---

# 36. Usability Requirements

The system is intended for non-technical business owners.

### NFR-014

The import workflow shall be simple.

### NFR-015

The dashboard shall use understandable business terminology.

### NFR-016

The AI assistant shall allow natural-language questions.

### NFR-017

Important AI-derived information shall be reviewable.

### NFR-018

The interface shall be responsive enough for desktop and mobile use.

---

# 37. MVP UI Structure

The minimum navigation should be:

```text
Dashboard
Customers
Inquiries / Orders
Insights
AI Assistant
Import Data
```

Avoid building unnecessary CRM functionality.

---

# 38. Three-Week Development Milestones

This is a critical part of this SRS.

The project shall be developed in three focused milestones.

---

# WEEK 1 — DATA FOUNDATION

## Goal

> **Get real WhatsApp exported data into a reliable database.**

The end of Week 1 must have a working ingestion pipeline.

### Day 1 — Project Setup

Tasks:

- Repository cleanup
- Backend setup
- Frontend setup
- Environment configuration
- SQLite setup
- SQLAlchemy setup
- Basic project structure
- SDD documentation setup

Deliverable:

```text
Backend runs
Frontend runs
Database connects
```

---

### Day 2 — WhatsApp Parser

Implement:

- ZIP extraction
- `_chat.txt` detection
- Message parsing
- Timestamp extraction
- Sender extraction
- Message type detection

Deliverable:

```text
ZIP
 ↓
Structured messages
```

---

### Day 3 — Database

Implement:

- Business
- Customer/contact
- Conversation
- Participant
- Message
- Media

Deliverable:

```text
WhatsApp export
        ↓
SQLite
```

---

### Day 4 — Incremental Import

Implement:

- Conversation identification
- Message fingerprint
- Duplicate detection
- Updated export handling
- Import status

Test:

```text
Export 1 = 100 messages

Export 2 = 120 messages

Database = 120
```

---

### Day 5 — Basic Conversation Viewer

Build a minimal UI to verify imported data.

Deliverable:

```text
Import
 ↓
Conversation list
 ↓
Conversation detail
 ↓
Messages
```

---

### Week 1 Exit Criteria

By the end of Week 1:

- [ ] Backend working
- [ ] Frontend working
- [ ] SQLite working
- [ ] ZIP import working
- [ ] TXT parsing working
- [ ] Messages stored
- [ ] Media references stored
- [ ] Duplicate detection working
- [ ] Incremental import working
- [ ] Conversation viewer working

### Week 1 Milestone

> **M1 — Reliable WhatsApp Data Foundation**

---

# WEEK 2 — AI BUSINESS INTELLIGENCE

## Goal

> **Turn conversations into structured business knowledge.**

This is the most important AI development week.

---

## Day 6 — LLM Extraction

Implement structured extraction for:

```text
Customer
Intent
Product/service
Quantity
Date
Price
Requirement
Order status
```

Create a strict JSON schema.

---

## Day 7 — Multilingual Processing

Create evaluation conversations containing:

```text
English
Sinhala
Singlish
Code-mixed
Informal language
```

Test extraction accuracy.

Example:

> "1kg chocolate cake eka kiyada?"

Expected:

```text
intent = price_inquiry
product = chocolate cake
quantity = 1kg
```

---

## Day 8 — Business Relevance

Implement:

```text
Business relevant
Personal
Uncertain
```

Use realistic mixed conversations.

Example:

```text
"Hi akka kohomada?"
→ Personal

"Cake eka Saturday ready da?"
→ Business
```

---

## Day 9 — Customer / Inquiry / Order / Feedback

Create structured business records.

Implement:

```text
Customer
Inquiry
Order
Feedback
```

Connect them to source messages.

---

## Day 10 — Analytics

Implement reliable database analytics:

```text
Total customers
New customers
Returning customers
Total inquiries
Confirmed orders
Conversion rate
Top products
Frequently asked questions
Feedback summary
```

These calculations should be performed by the backend/database.

---

## Week 2 Exit Criteria

By the end of Week 2:

- [ ] LLM extraction works
- [ ] Structured output works
- [ ] English processing works
- [ ] Sinhala/Singlish testing works
- [ ] Business relevance works
- [ ] Customer extraction works
- [ ] Inquiry extraction works
- [ ] Order extraction works
- [ ] Basic feedback extraction works
- [ ] Analytics work
- [ ] Source references work

### Week 2 Milestone

> **M2 — Conversation-to-Business Intelligence Pipeline**

---

# WEEK 3 — AI ASSISTANT + DEMO

## Goal

> **Make the system usable and demonstrable to a real business owner.**

---

# Day 11 — Agent Tools

Implement:

```text
search_customers
get_customer_history
search_conversations
search_orders
get_order
query_business_metrics
get_feedback
```

---

# Day 12 — LangGraph Agent

Build the agent flow:

```text
User Question
      ↓
Understand Intent
      ↓
Select Tool
      ↓
Retrieve Data
      ↓
LLM Interpretation
      ↓
Answer
```

---

# Day 13 — AI Assistant UI

Build the chat interface.

Test questions:

> "What product was requested most?"

> "How many orders did I get?"

> "What happened to Nethmi's order?"

> "What do customers say about delivery?"

> "Which customers are returning?"

---

# Day 14 — Dashboard + Integration

Connect:

```text
Import
+
Database
+
Analytics
+
AI Assistant
+
Customer View
```

At this point the product should feel like one application rather than separate features.

---

# Day 15 — MVP Freeze

**No new major features.**

Focus only on:

- Bug fixing
- Data validation
- UI cleanup
- Error handling
- Performance
- Demo flow
- Documentation

---

# 39. Final Milestone Timing

The functional MVP should be complete by:

> **Day 13–14 / first half of Week 3**

This is intentional.

Day 15 onward should be protected as a buffer.

Do not plan to finish the core product on the final day.

---

# 40. Week 3 Exit Criteria

The final MVP must demonstrate:

```text
Upload WhatsApp Export
        ↓
Process
        ↓
View Conversations
        ↓
Extract Business Information
        ↓
View Dashboard
        ↓
Ask AI Assistant
        ↓
Receive Evidence-Based Answer
```

### Final checklist

- [ ] Import works
- [ ] Updated imports work
- [ ] Duplicate detection works
- [ ] Database works
- [ ] AI extraction works
- [ ] Multilingual examples work
- [ ] Business relevance works
- [ ] Customers work
- [ ] Orders work
- [ ] Feedback works
- [ ] Analytics work
- [ ] Agent tools work
- [ ] AI assistant works
- [ ] Dashboard works
- [ ] Evidence works
- [ ] Error handling works
- [ ] Demo dataset prepared
- [ ] Final demo flow tested

### Week 3 Milestone

> **M3 — Demonstrable ChatInsights MVP**

---

# 41. Critical Scope Control

The following rule shall apply during the three-week development period:

> **A feature cannot be added to the MVP merely because it is technically interesting. It must directly support the core demonstration.**

The core demonstration is:

```text
WhatsApp conversation
        ↓
Business knowledge
        ↓
Business insight
        ↓
Owner question
        ↓
AI answer
```

If a feature does not strengthen this flow, it should be postponed unless there is significant remaining time.

---

# 42. AI-Assisted Development Strategy

Because development will use AI heavily, AI tools should be treated as implementation assistants rather than sources of requirements.

The workflow shall be:

```text
SRS
 ↓
Feature Specification
 ↓
AI Coding Agent
 ↓
Implementation
 ↓
Tests
 ↓
Human Review
 ↓
Acceptance Criteria
```

The AI coding agent should not independently redefine project requirements.

---

# 43. Recommended AI Development Rules

### Rule 1

Give the AI coding agent the relevant specification before asking it to implement a feature.

### Rule 2

Implement one feature at a time.

### Rule 3

Ask the AI to create tests alongside implementation.

### Rule 4

Do not allow large uncontrolled rewrites of the codebase.

### Rule 5

Review database migrations before applying them.

### Rule 6

Keep API contracts explicit.

### Rule 7

Commit after each stable milestone.

### Rule 8

Do not add advanced features before core flows are stable.

---

# 44. Specification-Driven Development Workflow

For each feature:

## Step 1 — Requirement

Example:

> The system shall prevent duplicate messages during repeated imports.

## Step 2 — Specification

Define exactly how duplicate detection works.

## Step 3 — Acceptance Test

```text
100 messages imported.

Same ZIP imported again.

Expected:
100 messages, not 200.
```

## Step 4 — AI Implementation

Ask the coding agent to implement only that requirement.

## Step 5 — Test

Run automated/manual test.

## Step 6 — Accept

If the test passes, move to the next feature.

---

# 45. Definition of Done

A feature is considered complete only when:

- Requirement implemented.
- Relevant test exists.
- Expected behavior verified.
- Errors handled.
- Code integrated.
- No critical regression introduced.
- Documentation updated if required.

---

# 46. MVP Dataset Requirements

A major risk is building the system but not having good data to demonstrate it.

Therefore, a realistic synthetic WhatsApp dataset shall be prepared.

The dataset should contain approximately:

### Conversations

20–50 realistic conversations for initial development.

### Customers

50–100 realistic customer identities for core testing.

### Scale test

Potentially 500 synthetic customer records for UI/database testing.

### Language distribution

Include:

```text
English
Sinhala
Singlish
English + Sinhala
```

### Conversation types

Include:

```text
Pure business
Purely personal
Mixed personal/business
Inquiry
Converted inquiry
Non-converted inquiry
Order modification
Cancellation
Feedback
Ambiguous conversation
```

---

# 47. Required Demonstration Dataset

At least one complete customer journey should exist:

```text
Inquiry
 ↓
Price discussion
 ↓
Order confirmation
 ↓
Order modification
 ↓
Completion
 ↓
Feedback
```

Example:

```text
Customer asks for cake
        ↓
Asks price
        ↓
Confirms 1kg
        ↓
Changes to 1.5kg
        ↓
Receives cake
        ↓
Sends feedback
```

This single journey is extremely useful for demonstrating the value of the system.

---

# 48. Evaluation Requirements

The MVP should be evaluated on five dimensions.

## 48.1 Ingestion Accuracy

Can the system correctly import WhatsApp messages?

## 48.2 Extraction Accuracy

Can it correctly identify:

- Customer
- Intent
- Product
- Quantity
- Date
- Order
- Feedback?

## 48.3 Language Understanding

Can it understand:

- English
- Sinhala
- Singlish
- Code-mixed messages?

## 48.4 Business Insight Quality

Are the generated insights actually useful to a business owner?

## 48.5 Agent Accuracy

Does the assistant answer questions using the correct data?

---

# 49. Minimum Evaluation Questions

The following questions shall be tested:

### Q1

> What product was requested most frequently?

### Q2

> How many inquiries became confirmed orders?

### Q3

> What happened to Nethmi's order?

### Q4

> What are customers asking most frequently?

### Q5

> Who are my returning customers?

### Q6

> What are customers saying about delivery?

### Q7

> Which inquiries did not become orders?

### Q8

> What feedback did customers give about the product?

---

# 50. Critical Risks

## Risk 1 — Overbuilding

### Risk

Trying to implement API integration, video processing, advanced RAG, CRM, analytics, and everything else within three weeks.

### Mitigation

Strict MVP scope.

---

## Risk 2 — AI Hallucination

### Risk

AI generates business facts that do not exist.

### Mitigation

Structured extraction + source references + validation.

---

## Risk 3 — Poor Multilingual Understanding

### Risk

Singlish/Sinhala conversations are incorrectly interpreted.

### Mitigation

Build a small representative evaluation dataset during Week 2.

---

## Risk 4 — Duplicate Data

### Risk

Repeated WhatsApp exports create duplicate records.

### Mitigation

Implement incremental import during Week 1, not later.

---

## Risk 5 — Poor Demo Data

### Risk

System works technically but doesn't demonstrate meaningful intelligence.

### Mitigation

Prepare realistic conversations early.

---

## Risk 6 — AI Agent Becomes Too Complex

### Risk

Spending too much time building sophisticated agent orchestration.

### Mitigation

Start with a small number of deterministic tools and one clear agent workflow.

---

## Risk 7 — UI Takes Too Long

### Risk

Spending the majority of the project on visual design.

### Mitigation

Functional wireframe-first UI.

---

# 51. RAG Decision

RAG should **not be a core MVP requirement**.

The primary information source is structured business data derived from conversations.

Therefore:

```text
Customer/order question
        ↓
Database
```

rather than:

```text
Customer/order question
        ↓
Vector database
        ↓
RAG
```

RAG may become useful later for:

- Long-form conversation retrieval
- Semantic conversation search
- Business documents
- Policies
- Product catalogs
- FAQs
- Unstructured knowledge

But for the three-week MVP:

> **Prioritize structured database querying and evidence retrieval over building a complex RAG architecture.**

---

# 52. MVP Agent Architecture

The recommended initial agent is:

```text
                User Question
                     ↓
              LangGraph Agent
                     ↓
          Determine question type
                     ↓
       +-------------+-------------+
       |             |             |
       ↓             ↓             ↓
 Customer        Metrics       Conversation
   Tool            Tool           Tool
       |             |             |
       +-------------+-------------+
                     ↓
              Retrieved Data
                     ↓
                  LLM
                     ↓
             Natural Answer
                     ↓
                Evidence
```

This is sufficient for the MVP.

---

# 53. What the MVP Should NOT Attempt to Prove

The MVP does not need to prove that ChatInsights can:

- Fully understand every WhatsApp conversation.
- Perfectly understand every Sinhala/Singlish expression.
- Automatically understand every video.
- Automatically identify every real-world customer.
- Provide real-time WhatsApp monitoring.
- Replace WhatsApp Business.
- Replace accounting software.
- Replace a CRM.
- Forecast the entire business.
- Automatically make business decisions.

The MVP needs to prove one thing:

> **There is value in transforming informal WhatsApp conversations into structured business knowledge and allowing a business owner to query and understand that knowledge through AI.**

---

# 54. Final MVP Definition

At the end of three weeks, ChatInsights shall be a working prototype where a business owner can:

1. Upload a WhatsApp exported chat ZIP.
2. Import multiple conversations.
3. Re-import updated conversations without duplicating messages.
4. View imported conversations.
5. Identify business-relevant information.
6. Extract customers, inquiries, orders, requirements, and basic feedback.
7. Store the information in SQLite.
8. View basic business metrics.
9. Search customer information.
10. Ask natural-language questions through an AI assistant.
11. Receive answers based on structured business data.
12. Inspect supporting conversation information.
13. Review uncertain AI-generated information.

The complete functional flow shall be:

```text
             WHATSAPP EXPORT
                    │
                    ▼
              IMPORT / PARSE
                    │
                    ▼
            NORMALIZED MESSAGES
                    │
                    ▼
         BUSINESS RELEVANCE CHECK
                    │
                    ▼
           AI INFORMATION EXTRACTION
                    │
                    ▼
             VALIDATED DATA
                    │
                    ▼
                 SQLITE
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
      ANALYTICS          AGENT TOOLS
          │                   │
          └─────────┬─────────┘
                    ▼
             AI ASSISTANT
                    │
                    ▼
             BUSINESS OWNER
```

---

# 55. Three-Week Final Roadmap

```text
WEEK 1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATA FOUNDATION

ZIP Import
TXT Parser
Media Detection
SQLite
Message Storage
Duplicate Detection
Incremental Import
Conversation Viewer

                 ↓

M1: RELIABLE DATA FOUNDATION


WEEK 2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BUSINESS INTELLIGENCE

LLM Extraction
English/Sinhala/Singlish
Business Relevance
Customers
Inquiries
Orders
Feedback
Analytics

                 ↓

M2: CONVERSATION → BUSINESS KNOWLEDGE


WEEK 3 — FIRST HALF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AI ASSISTANT + INTEGRATION

Agent Tools
LangGraph
Natural Language Questions
Evidence
Dashboard Integration
End-to-End Flow

                 ↓

M3: WORKING MVP


WEEK 3 — SECOND HALF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FREEZE + VALIDATE

Testing
Bug Fixing
Evaluation
UI Refinement
Demo Dataset
Documentation
Presentation
```

---

# 56. Final Development Principle

The project should follow one central rule throughout the three weeks:

> **Finish the complete path before expanding the path.**

Do not build:

```text
Advanced video processing
Advanced RAG
Advanced customer matching
Advanced forecasting
Advanced dashboards
```

while the fundamental flow is incomplete.

Instead, prioritize:

```text
Import
 ↓
Understand
 ↓
Structure
 ↓
Store
 ↓
Analyse
 ↓
Ask
 ↓
Answer
```

Once that works reliably, add improvements only where time permits.

---

# 57. SRS Approval Baseline

This document shall be considered the **MVP baseline specification**.

Any new feature introduced during development should be evaluated against:

1. Does it directly support the core MVP?
2. Can it be completed within the remaining time?
3. Does it introduce significant architectural complexity?
4. Does it improve the final demonstration?
5. Can it be tested within the three-week period?

If the answer is no, the feature should be moved to the future-scope list.

**Target:** Functional MVP completed by the **first half of Week 3**, with the remainder of Week 3 reserved for validation, refinement, and demonstration preparation.
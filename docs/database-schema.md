# Blueprint BI / ChatInsights

# Formal MVP Database Schema Specification

**Project:** AI LaunchPad Rapid MVP  
**Technical Name:** Blueprint BI  
**Product Name:** ChatInsights  
**Database:** SQLite  
**ORM:** SQLAlchemy 2.x  
**Specification Basis:** Blueprint BI / ChatInsights MVP SRS v2.0  
**Development Methodology:** Specification-Driven Development (OpenSpec)  
**Status:** MVP Database Baseline — Revised  
**Version:** 1.1  
**Date:** 11 August 2026

---

# 1. Purpose

This document defines the formal database schema for the **Blueprint BI / ChatInsights MVP**.

The database provides the persistent foundation for the following workflow:

```text
WhatsApp Export ZIP
        ↓
Data Ingestion
        ↓
Message Parsing
        ↓
Normalized Raw Data
        ↓
Business Relevance Detection
        ↓
AI Information Extraction
        ↓
Validation / Human Review
        ↓
Structured Business Data
        ↓
SQLite
        ↓
Analytics / Agent Tools
        ↓
AI Business Assistant
```

The schema is designed for the three-week MVP and prioritizes:

- Reliable WhatsApp export ingestion
- Incremental imports
- Preservation of raw conversation data
- Structured business information
- Evidence-based AI extraction
- Conservative customer identity handling
- Basic analytics
- AI business-assistant queries

The schema is intentionally generic enough to support different small and independent businesses rather than being limited to the initial home-bakery demonstration.

---

# 2. Database Design Goals

The database shall:

1. Preserve the original imported WhatsApp data.
2. Separate raw data from AI-derived business information.
3. Support repeated and incremental WhatsApp exports.
4. Prevent duplicate message records.
5. Maintain traceability from derived information to source messages.
6. Support multiple WhatsApp identities for a logical customer.
7. Avoid automatically merging customers based only on names.
8. Support uncertain AI-derived information and human review.
9. Support business analytics through deterministic queries.
10. Support the MVP AI-agent tools.
11. Remain simple enough for SQLite and rapid MVP development.
12. Avoid unnecessary CRM, accounting, RAG, payment, and real-time messaging infrastructure.

---

# 3. Core Design Principles

## 3.1 Raw Data Must Be Preserved

The original imported message, timestamp, sender information, message type, and media references must remain available.

AI-derived information must never replace the original message.

Example:

```text
RAW MESSAGE

"Actually make it 1.5kg."


AI-DERIVED INFORMATION

Order quantity = 1.5 kg
Confidence = 0.93
```

The original message remains the source of truth.

---

# 3.2 Raw Data and Derived Data Are Separate

The database has a clear boundary between:

### Raw WhatsApp information

```text
Conversation
Participant
Message
Media
ImportBatch
```

and:

### AI-derived business information

```text
Inquiry
Order
OrderItem
Feedback
ExtractedFact
```

The AI should interpret raw information rather than overwrite it.

---

# 3.3 Evidence-Based AI Data

AI-derived business records must be traceable to the original messages that support them.

A business owner should be able to ask:

> "Why does ChatInsights think this was an order?"

The system should be able to retrieve the supporting WhatsApp messages.

Because one business fact may be derived from several messages, evidence is represented as a separate relationship rather than relying only on a single `source_message_id`.

---

# 3.4 Conservative Customer Identity

A WhatsApp identity is not automatically equivalent to a customer.

The model therefore separates:

```text
Customer
    ↓
WhatsApp Identity
```

Example:

```text
Customer
   ├── WhatsApp Number A
   └── WhatsApp Number B
```

However, a new WhatsApp number should initially remain a separate identity.

The system may suggest that two identities belong to the same customer, but the owner must confirm the relationship.

Matching names alone must not automatically merge customers.

---

# 3.5 Idempotent Imports

A business owner may export their WhatsApp data repeatedly.

For example:

```text
August 1 export
    ↓
100 messages

August 8 export
    ↓
120 messages

August 15 export
    ↓
150 messages
```

The database must prevent the same messages from being inserted repeatedly.

The import process therefore uses:

- Import batches
- Conversation identification
- Message fingerprints
- Unique constraints

---

# 3.6 Database vs LLM Responsibilities

The database/backend shall handle deterministic operations such as:

- Filtering
- Sorting
- Counting
- Aggregation
- Date calculations
- Conversion calculations

The LLM shall handle:

- Language understanding
- Conversation interpretation
- Information extraction
- Summarization
- Natural-language explanation

The LLM should not be responsible for performing reliable numerical business calculations when the database can perform them.

---

# 4. Schema Architecture

The database is divided into four logical areas.

## Layer 1 — Business and Identity

```text
businesses
customers
whatsapp_identities
```

## Layer 2 — Import and Raw WhatsApp Data

```text
import_batches
conversations
participants
messages
media
```

## Layer 3 — Derived Business Intelligence

```text
inquiries
orders
order_items
feedback
extracted_facts
```

## Layer 4 — Evidence / Provenance

```text
extraction_evidence
```

Overall:

```text
                         BUSINESS
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
         CUSTOMER      IMPORT_BATCH   CONVERSATION
             │              │              │
             ▼              │              ▼
   WHATSAPP_IDENTITY        │         PARTICIPANT
             │              │              │
             └──────────────┴──────────────┤
                                           ▼
                                        MESSAGE
                                           │
                                           ▼
                                         MEDIA
                                           │
                                           │
                                    AI EXTRACTION
                                           │
                         ┌─────────────────┼─────────────────┐
                         ▼                 ▼                 ▼
                      INQUIRY            ORDER           FEEDBACK
                                           │
                                           ▼
                                      ORDER_ITEM

                         AI-DERIVED BUSINESS FACTS
                                   │
                                   ▼
                           EXTRACTION_EVIDENCE
                                   │
                                   ▼
                                MESSAGE
```

---

# 5. Entity Catalogue

| Entity | Layer | Purpose |
|---|---|---|
| Business | Identity | Business/account represented by the imported data |
| Customer | Identity | Logical customer record |
| WhatsAppIdentity | Identity | WhatsApp contact/number associated with a customer |
| ImportBatch | Import | One uploaded/imported WhatsApp export |
| Conversation | Raw | Imported WhatsApp conversation |
| Participant | Raw | Identity participating in a conversation |
| Message | Raw | Original normalized WhatsApp message |
| Media | Raw | Media associated with a message |
| Inquiry | Derived | Customer business inquiry extracted from messages |
| Order | Derived | Confirmed/identified business order |
| OrderItem | Derived | Individual product/service within an order |
| Feedback | Derived | Customer feedback extracted from messages |
| ExtractedFact | Derived | General AI-derived business fact |
| ExtractionEvidence | Evidence | Links derived information to supporting messages |

---

# 6. `businesses`

## Purpose

Represents the business whose WhatsApp data is being analyzed.

The initial demonstration may use a Sri Lankan home bakery, but the schema should support other small businesses.

## Columns

| Column | SQLite Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PK | Internal business identifier |
| `name` | VARCHAR(255) | NOT NULL | Business name |
| `business_type` | VARCHAR(100) | NULL | Business category |
| `created_at` | DATETIME | NOT NULL | Creation timestamp |
| `updated_at` | DATETIME | NOT NULL | Last modification timestamp |

## Relationships

```text
Business 1 ──── * Customer
Business 1 ──── * WhatsAppIdentity
Business 1 ──── * ImportBatch
Business 1 ──── * Conversation
Business 1 ──── * Inquiry
Business 1 ──── * Order
Business 1 ──── * Feedback
Business 1 ──── * ExtractedFact
```

---

# 7. `customers`

## Purpose

Represents a logical customer.

A customer is deliberately separated from a WhatsApp identity because the same real-world customer may use more than one WhatsApp number.

## Columns

| Column | SQLite Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PK | Customer identifier |
| `business_id` | INTEGER | FK, NOT NULL | Owning business |
| `display_name` | VARCHAR(255) | NULL | Customer name if known |
| `created_at` | DATETIME | NOT NULL | Creation timestamp |
| `updated_at` | DATETIME | NOT NULL | Last modification timestamp |

## Relationships

```text
Business
   ↓
Customer
   ├── WhatsApp identities
   ├── Inquiries
   ├── Orders
   └── Feedback
```

Conversations are reached through the customer's WhatsApp identities and participants.

---

# 8. `whatsapp_identities`

## Purpose

Represents an individual WhatsApp contact/identity.

This table supports conservative customer matching and multiple WhatsApp numbers.

## Columns

| Column | SQLite Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PK | Identity identifier |
| `business_id` | INTEGER | FK, NOT NULL | Owning business |
| `customer_id` | INTEGER | FK, NULL | Associated logical customer |
| `phone_number` | VARCHAR(50) | NOT NULL | WhatsApp number/identity |
| `display_name` | VARCHAR(255) | NULL | Name appearing in export |
| `identity_link_status` | VARCHAR(30) | NOT NULL | Identity/customer relationship state |
| `created_at` | DATETIME | NOT NULL | Creation timestamp |
| `updated_at` | DATETIME | NOT NULL | Last modification timestamp |

## Identity link statuses

```text
unverified
confirmed
rejected
```

### Interpretation

```text
unverified
    ↓
System has not confirmed relationship

confirmed
    ↓
Owner/system has confirmed identity belongs
to the customer

rejected
    ↓
Suggested relationship was rejected
```

## Constraint

```text
UNIQUE(business_id, phone_number)
```

A customer may have multiple WhatsApp identities.

---

# 9. `import_batches`

## Purpose

Represents one WhatsApp export/import operation.

This entity is required to track repeated exports and maintain import provenance.

Example:

```text
Import Batch #1
    WhatsApp_2026_08_01.zip

Import Batch #2
    WhatsApp_2026_08_08.zip

Import Batch #3
    WhatsApp_2026_08_15.zip
```

## Columns

| Column | SQLite Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PK | Import batch identifier |
| `business_id` | INTEGER | FK, NOT NULL | Business |
| `source_filename` | VARCHAR(512) | NULL | Uploaded ZIP filename |
| `file_hash` | VARCHAR(128) | NULL | Hash of imported ZIP/file |
| `status` | VARCHAR(30) | NOT NULL | Import state |
| `message_count` | INTEGER | NOT NULL | Messages processed |
| `new_message_count` | INTEGER | NOT NULL | Newly inserted messages |
| `duplicate_count` | INTEGER | NOT NULL | Duplicate messages detected |
| `error_count` | INTEGER | NOT NULL | Import errors |
| `started_at` | DATETIME | NULL | Processing start |
| `completed_at` | DATETIME | NULL | Processing completion |
| `created_at` | DATETIME | NOT NULL | Record creation |

## Import statuses

```text
processing
completed
partially_completed
failed
```

## Relationships

```text
Business
    ↓
ImportBatch
    ↓
Conversation / Message
```

An import batch provides provenance for imported data.

---

# 10. `conversations`

## Purpose

Represents an imported WhatsApp conversation/chat.

## Columns

| Column | SQLite Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PK | Conversation identifier |
| `business_id` | INTEGER | FK, NOT NULL | Owning business |
| `external_identifier` | VARCHAR(512) | NOT NULL | Stable source identifier |
| `chat_name` | VARCHAR(255) | NULL | Exported chat name |
| `source_file` | VARCHAR(512) | NULL | Original source file |
| `started_at` | DATETIME | NULL | Earliest known message |
| `ended_at` | DATETIME | NULL | Latest known message |
| `imported_at` | DATETIME | NOT NULL | Import timestamp |
| `created_at` | DATETIME | NOT NULL | Creation timestamp |
| `updated_at` | DATETIME | NOT NULL | Last modification timestamp |

## Constraint

```text
UNIQUE(business_id, external_identifier)
```

This allows repeated imports to identify the same conversation.

---

# 11. `participants`

## Purpose

Associates WhatsApp identities with conversations.

A conversation may contain multiple participants.

## Columns

| Column | SQLite Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PK | Participant record |
| `conversation_id` | INTEGER | FK, NOT NULL | Conversation |
| `whatsapp_identity_id` | INTEGER | FK, NOT NULL | WhatsApp identity |
| `role` | VARCHAR(50) | NULL | Participant role |

## Constraints

```text
UNIQUE(conversation_id, whatsapp_identity_id)
```

## Possible roles

```text
customer
business
other
unknown
```

The exact role handling can remain simple for the MVP.

---

# 12. `messages`

## Purpose

The `messages` table is the primary raw-data table.

It stores the normalized representation of an original WhatsApp message.

The original content must remain available even after AI processing.

## Columns

| Column | SQLite Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PK | Internal message ID |
| `conversation_id` | INTEGER | FK, NOT NULL | Parent conversation |
| `import_batch_id` | INTEGER | FK, NOT NULL | Import that introduced/processed the message |
| `participant_id` | INTEGER | FK, NULL | Sender/participant |
| `external_message_id` | VARCHAR(512) | NULL | Source-specific message identifier |
| `timestamp` | DATETIME | NOT NULL | Original message timestamp |
| `message_type` | VARCHAR(30) | NOT NULL | Message type |
| `content` | TEXT | NULL | Original text/content |
| `source_filename` | VARCHAR(512) | NULL | Original source reference |
| `message_fingerprint` | VARCHAR(128) | NOT NULL | Deterministic duplicate identifier |
| `business_relevance` | VARCHAR(30) | NULL | Business/personal/uncertain |
| `created_at` | DATETIME | NOT NULL | Database insertion timestamp |

## Supported message types

```text
text
image
audio
video
document
system
```

## Business relevance

```text
business_relevant
personal
uncertain
```

A single conversation may contain both business and personal messages.

## Duplicate constraint

```text
UNIQUE(conversation_id, message_fingerprint)
```

---

# 13. `media`

## Purpose

Stores metadata and processing information for media attached to messages.

The MVP primarily needs to identify and preserve media. Advanced video processing is outside the core MVP.

## Columns

| Column | SQLite Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PK | Media identifier |
| `message_id` | INTEGER | FK, NOT NULL | Parent message |
| `media_type` | VARCHAR(30) | NOT NULL | Image/audio/video/document |
| `filename` | VARCHAR(512) | NULL | Original filename |
| `file_path` | VARCHAR(1024) | NULL | Local stored path |
| `mime_type` | VARCHAR(100) | NULL | MIME type |
| `file_size` | INTEGER | NULL | Size in bytes |
| `processing_status` | VARCHAR(30) | NOT NULL | Media processing state |
| `processing_error` | TEXT | NULL | Error information if processing fails |
| `transcription` | TEXT | NULL | Speech-to-text result if available |
| `created_at` | DATETIME | NOT NULL | Creation timestamp |
| `updated_at` | DATETIME | NOT NULL | Last processing update |

## Processing statuses

```text
pending
processing
completed
failed
not_applicable
```

### Important rule

Media-processing failure must not prevent raw text messages from being stored.

For example:

```text
Message imported ✓
      ↓
Voice note detected ✓
      ↓
Transcription failed ✗
      ↓
Original message/media remains stored ✓
```

---

# 14. `inquiries`

## Purpose

Stores AI-derived customer inquiries.

The MVP supports inquiries involving:

- Price
- Availability
- Product
- Service
- Delivery
- General business questions

## Columns

| Column | SQLite Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PK | Inquiry identifier |
| `business_id` | INTEGER | FK, NOT NULL | Business |
| `customer_id` | INTEGER | FK, NULL | Customer |
| `source_message_id` | INTEGER | FK, NULL | Primary/source message |
| `inquiry_type` | VARCHAR(50) | NOT NULL | Inquiry category |
| `product_or_service` | VARCHAR(255) | NULL | Requested product/service |
| `quantity` | VARCHAR(100) | NULL | Requested quantity |
| `requested_date` | DATETIME | NULL | Requested date |
| `requirements` | TEXT | NULL | Relevant requirements |
| `status` | VARCHAR(30) | NOT NULL | Inquiry state |
| `confidence` | FLOAT | NULL | AI confidence |
| `extraction_status` | VARCHAR(30) | NOT NULL | Processing/review state |
| `model_name` | VARCHAR(100) | NULL | Model used for extraction |
| `model_version` | VARCHAR(100) | NULL | Model/version identifier |
| `extracted_at` | DATETIME | NULL | Extraction timestamp |
| `created_at` | DATETIME | NOT NULL | Creation timestamp |
| `updated_at` | DATETIME | NOT NULL | Last modification |

## Inquiry statuses

```text
new
pending
converted
not_converted
unknown
```

## Extraction statuses

```text
pending
processed
needs_review
confirmed
rejected
failed
```

---

# 15. `orders`

## Purpose

Stores AI-derived orders where sufficient evidence exists.

An order may be derived from multiple messages in a conversation.

## Columns

| Column | SQLite Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PK | Order identifier |
| `business_id` | INTEGER | FK, NOT NULL | Business |
| `customer_id` | INTEGER | FK, NULL | Customer |
| `source_message_id` | INTEGER | FK, NULL | Primary/supporting source message |
| `inquiry_id` | INTEGER | FK, NULL | Related inquiry |
| `order_date` | DATETIME | NULL | Order date |
| `delivery_date` | DATETIME | NULL | Delivery/service date |
| `status` | VARCHAR(30) | NOT NULL | Order status |
| `total_amount` | NUMERIC | NULL | Order total |
| `requirements` | TEXT | NULL | Delivery/customization/etc. |
| `confidence` | FLOAT | NULL | AI confidence |
| `extraction_status` | VARCHAR(30) | NOT NULL | Processing/review state |
| `model_name` | VARCHAR(100) | NULL | Model used |
| `model_version` | VARCHAR(100) | NULL | Model/version |
| `extracted_at` | DATETIME | NULL | Extraction timestamp |
| `created_at` | DATETIME | NOT NULL | Creation timestamp |
| `updated_at` | DATETIME | NOT NULL | Last modification |

## Order statuses

```text
inquiry
confirmed
completed
cancelled
unknown
```

## Important relationship

An order may be supported by multiple messages.

The `source_message_id` is therefore treated as the primary/source message for convenience, while the complete supporting evidence is represented through `extraction_evidence`.

---

# 16. `order_items`

## Purpose

Represents individual products/services belonging to an order.

## Columns

| Column | SQLite Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PK | Order-item identifier |
| `order_id` | INTEGER | FK, NOT NULL | Parent order |
| `product_name` | VARCHAR(255) | NOT NULL | Product/service |
| `quantity` | VARCHAR(100) | NULL | Quantity |
| `unit_price` | NUMERIC | NULL | Unit price |
| `total_price` | NUMERIC | NULL | Item total |
| `requirements` | TEXT | NULL | Item-specific requirements |
| `created_at` | DATETIME | NOT NULL | Creation timestamp |
| `updated_at` | DATETIME | NOT NULL | Last modification |

## Relationship

```text
Order 1 ──── * OrderItem
```

---

# 17. `feedback`

## Purpose

Stores AI-derived customer feedback.

Feedback may occur after an order or independently.

## Columns

| Column | SQLite Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PK | Feedback identifier |
| `business_id` | INTEGER | FK, NOT NULL | Business |
| `customer_id` | INTEGER | FK, NULL | Customer |
| `order_id` | INTEGER | FK, NULL | Related order |
| `source_message_id` | INTEGER | FK, NULL | Primary/source message |
| `sentiment` | VARCHAR(30) | NOT NULL | Sentiment |
| `topic` | VARCHAR(50) | NULL | Feedback topic |
| `content` | TEXT | NULL | Extracted feedback |
| `confidence` | FLOAT | NULL | AI confidence |
| `extraction_status` | VARCHAR(30) | NOT NULL | Processing/review state |
| `model_name` | VARCHAR(100) | NULL | Model used |
| `model_version` | VARCHAR(100) | NULL | Model/version |
| `extracted_at` | DATETIME | NULL | Extraction timestamp |
| `created_at` | DATETIME | NOT NULL | Creation timestamp |
| `updated_at` | DATETIME | NOT NULL | Last modification |

## Sentiment values

```text
positive
negative
mixed
neutral
unknown
```

## Topic values

```text
product
taste_quality
delivery
price
service
design_customization
```

---

# 18. `extracted_facts`

## Purpose

Stores general AI-derived business facts that do not necessarily fit into the specialized Inquiry, Order, or Feedback entities.

Examples could include:

```text
Customer prefers Sunday delivery.

Customer usually orders chocolate products.

Customer requested a specific customization.

Customer mentioned a recurring requirement.
```

## Columns

| Column | SQLite Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PK | Fact identifier |
| `business_id` | INTEGER | FK, NOT NULL | Business |
| `customer_id` | INTEGER | FK, NULL | Related customer |
| `conversation_id` | INTEGER | FK, NULL | Related conversation |
| `source_message_id` | INTEGER | FK, NULL | Primary/source message |
| `fact_type` | VARCHAR(100) | NOT NULL | Type of fact |
| `fact_value` | TEXT | NOT NULL | Extracted value |
| `confidence` | FLOAT | NULL | AI confidence |
| `status` | VARCHAR(30) | NOT NULL | Review state |
| `model_name` | VARCHAR(100) | NULL | Model used |
| `model_version` | VARCHAR(100) | NULL | Model/version |
| `extracted_at` | DATETIME | NULL | Extraction timestamp |
| `created_at` | DATETIME | NOT NULL | Creation timestamp |
| `updated_at` | DATETIME | NOT NULL | Last modification |

## Proposed statuses

```text
pending_review
confirmed
rejected
```

These are implementation-level statuses representing the SRS requirement for reviewable AI-derived information.

---

# 19. `extraction_evidence`

## Purpose

Stores the relationship between AI-derived business information and the raw messages that support it.

This entity is important because a single inquiry, order, feedback item, or extracted fact may be derived from multiple messages.

## Example

```text
Customer:
"Can I get a 1kg chocolate cake?"

Business:
"Yes, Rs. 4,500."

Customer:
"Can you deliver Sunday?"

Business:
"Yes."

Customer:
"Okay confirmed."
```

The resulting order may be supported by all four messages.

```text
Order #25
    │
    ├── Message #101
    ├── Message #102
    ├── Message #103
    └── Message #104
```

## Columns

| Column | SQLite Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PK | Evidence record |
| `message_id` | INTEGER | FK, NOT NULL | Supporting message |
| `entity_type` | VARCHAR(50) | NOT NULL | Derived entity type |
| `entity_id` | INTEGER | NOT NULL | Derived entity identifier |
| `evidence_role` | VARCHAR(50) | NULL | Role of message in supporting the entity |
| `created_at` | DATETIME | NOT NULL | Creation timestamp |

## Entity types

```text
inquiry
order
feedback
extracted_fact
```

## Example

```text
entity_type = order
entity_id = 25
message_id = 101
evidence_role = product_request
```

and:

```text
entity_type = order
entity_id = 25
message_id = 104
evidence_role = confirmation
```

### Important implementation note

`entity_type + entity_id` is a polymorphic reference. SQLite cannot enforce a conventional foreign key to multiple possible tables for this design.

Therefore, the application/service layer must validate that the referenced derived record actually exists.

For the MVP, this is acceptable because the main purpose is evidence/provenance.

---

# 20. Foreign-Key Relationship Map

The primary relationships are:

```text
BUSINESS
│
├── CUSTOMER
│    │
│    └── WHATSAPP_IDENTITY
│              │
│              └── PARTICIPANT
│                       │
│                       └── CONVERSATION
│                                │
│                                └── MESSAGE
│                                      │
│                                      └── MEDIA
│
├── IMPORT_BATCH
│        │
│        └── MESSAGE
│
├── INQUIRY
│
├── ORDER
│      │
│      └── ORDER_ITEM
│
├── FEEDBACK
│
└── EXTRACTED_FACT


MESSAGE
   │
   └── EXTRACTION_EVIDENCE
          │
          ├── INQUIRY
          ├── ORDER
          ├── FEEDBACK
          └── EXTRACTED_FACT
```

---

# 21. Cardinality Summary

| Relationship | Cardinality |
|---|---|
| Business → Customer | 1 : Many |
| Business → WhatsAppIdentity | 1 : Many |
| Customer → WhatsAppIdentity | 1 : Many |
| Business → ImportBatch | 1 : Many |
| Business → Conversation | 1 : Many |
| ImportBatch → Message | 1 : Many |
| Conversation → Participant | 1 : Many |
| Conversation → Message | 1 : Many |
| Participant → Message | 1 : Many |
| Message → Media | 1 : Many |
| Business → Inquiry | 1 : Many |
| Customer → Inquiry | 1 : Many / optional |
| Inquiry → Order | 1 : Many / optional |
| Business → Order | 1 : Many |
| Customer → Order | 1 : Many / optional |
| Order → OrderItem | 1 : Many |
| Business → Feedback | 1 : Many |
| Customer → Feedback | 1 : Many / optional |
| Order → Feedback | 1 : Many / optional |
| Business → ExtractedFact | 1 : Many |
| Message → ExtractionEvidence | 1 : Many |
| Derived entity → Evidence | 1 : Many |

---

# 22. Evidence and Provenance Model

The evidence model is:

```text
                  RAW MESSAGE
                       │
                       ▼
              EXTRACTION_EVIDENCE
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       INQUIRY        ORDER       FEEDBACK
                                   
                       │
                       ▼
                EXTRACTED_FACT
```

The system should preserve:

```text
Original message
        ↓
AI interpretation
        ↓
Confidence
        ↓
Supporting evidence
```

This enables explainable AI behavior.

---

# 23. Raw vs Derived Data Boundary

## Raw tables

These represent information directly obtained from the WhatsApp export:

```text
import_batches
conversations
participants
messages
media
```

## Business/identity tables

```text
businesses
customers
whatsapp_identities
```

## AI-derived tables

```text
inquiries
orders
order_items
feedback
extracted_facts
```

## Evidence

```text
extraction_evidence
```

The fundamental rule is:

```text
RAW DATA IS NEVER REPLACED BY AI INTERPRETATION.
```

---

# 24. Duplicate Detection Specification

Repeated WhatsApp imports must be idempotent.

The proposed message fingerprint uses:

```text
conversation identity
+
timestamp
+
sender identity
+
normalized message content
+
message type
```

Conceptually:

```text
fingerprint =
SHA-256(
    conversation_identifier
    + timestamp
    + sender
    + normalized_content
    + message_type
)
```

This is an implementation proposal rather than a literal SRS requirement.

The database shall enforce:

```text
UNIQUE(conversation_id, message_fingerprint)
```

Expected behavior:

```text
Import 1
100 messages
     ↓
Database = 100


Import 2
120 messages
     ↓
100 existing
20 new
     ↓
Database = 120
```

The exact fingerprint implementation shall be validated against the actual WhatsApp export format before being finalized.

---

# 25. Import Provenance

Each import should be identifiable.

Example:

```text
ImportBatch #1
    source = export_2026_08_01.zip

ImportBatch #2
    source = export_2026_08_08.zip
```

The import batch provides:

- Source filename
- File hash
- Processing status
- Number of messages
- Number of new messages
- Number of duplicates
- Number of errors
- Processing timestamps

This makes incremental ingestion observable and debuggable.

---

# 26. AI Extraction Metadata

AI-derived records should retain sufficient metadata to support debugging and reprocessing.

At minimum:

```text
confidence
extraction_status
model_name
model_version
extracted_at
```

Example:

```text
Order #25

confidence:
0.93

extraction_status:
confirmed

model_name:
<model>

model_version:
<version>

extracted_at:
2026-08-11 14:30
```

This allows the system to distinguish:

```text
Raw WhatsApp data
        ↓
Extraction attempt
        ↓
AI-derived result
        ↓
Human review
```

---

# 27. AI Data Integrity

The LLM must not directly manipulate the database.

The intended flow is:

```text
LLM
 ↓
Structured output
 ↓
Pydantic / schema validation
 ↓
Business validation
 ↓
SQLAlchemy
 ↓
SQLite
```

For uncertain information:

```text
AI extraction
      ↓
Confidence / validation
      ↓
needs_review
      ↓
Business owner
      ↓
Confirm / Reject
```

This protects the database from malformed or unsupported AI output.

---

# 28. Failure Isolation

Raw data ingestion and AI processing must be sufficiently independent.

Example:

```text
WhatsApp import
      ↓
RAW MESSAGE STORED ✓
      ↓
AI extraction
      ↓
Extraction failure ✗
      ↓
Raw message remains available ✓
```

Similarly:

```text
Text import ✓
Media processing ✗

Result:

Text remains stored.
Media failure is recorded.
```

The system must not delete or invalidate successfully imported raw data because a later AI/media-processing step fails.

---

# 29. Indexing Strategy

The following indexes are recommended for the MVP.

## Businesses

```text
PRIMARY KEY businesses.id
```

## Customers

```text
INDEX customers.business_id
INDEX customers.display_name
```

## WhatsApp identities

```text
UNIQUE(business_id, phone_number)
INDEX whatsapp_identities.customer_id
INDEX whatsapp_identities.business_id
```

## Import batches

```text
INDEX import_batches.business_id
INDEX import_batches.imported/created_at
INDEX import_batches.status
```

## Conversations

```text
UNIQUE(business_id, external_identifier)
INDEX conversations.business_id
INDEX conversations.started_at
INDEX conversations.ended_at
```

## Participants

```text
UNIQUE(conversation_id, whatsapp_identity_id)
INDEX participants.whatsapp_identity_id
```

## Messages

```text
INDEX messages.conversation_id
INDEX messages.import_batch_id
INDEX messages.timestamp
INDEX messages.business_relevance
UNIQUE(conversation_id, message_fingerprint)
```

## Media

```text
INDEX media.message_id
INDEX media.processing_status
```

## Inquiries

```text
INDEX inquiries.business_id
INDEX inquiries.customer_id
INDEX inquiries.status
INDEX inquiries.extraction_status
INDEX inquiries.source_message_id
```

## Orders

```text
INDEX orders.business_id
INDEX orders.customer_id
INDEX orders.status
INDEX orders.order_date
INDEX orders.extraction_status
INDEX orders.source_message_id
INDEX orders.inquiry_id
```

## Order items

```text
INDEX order_items.order_id
INDEX order_items.product_name
```

## Feedback

```text
INDEX feedback.business_id
INDEX feedback.customer_id
INDEX feedback.sentiment
INDEX feedback.extraction_status
INDEX feedback.source_message_id
INDEX feedback.order_id
```

## Extracted facts

```text
INDEX extracted_facts.business_id
INDEX extracted_facts.customer_id
INDEX extracted_facts.conversation_id
INDEX extracted_facts.status
INDEX extracted_facts.source_message_id
```

## Evidence

```text
INDEX extraction_evidence.message_id
INDEX extraction_evidence.entity_type
INDEX extraction_evidence.entity_id
```

These indexes are intended to support customer search, analytics, conversation inspection, incremental import, and agent-tool queries.

---

# 30. Foreign-Key and Delete Behavior

The application should avoid destructive cascading deletes for raw conversation data during the MVP.

Recommended conceptual behavior:

```text
Business
   ↓
Raw data
```

should not be silently deleted through unrelated AI-derived operations.

For example:

Deleting/rejecting an extracted order should **not** delete:

```text
Conversation
Message
Media
```

Likewise:

```text
AI extraction failure
```

must not delete the underlying message.

Exact SQLAlchemy `ondelete` behavior should be specified in the implementation change after the schema is approved.

---

# 31. MVP Schema Scope

## Included

```text
businesses
customers
whatsapp_identities
import_batches
conversations
participants
messages
media
inquiries
orders
order_items
feedback
extracted_facts
extraction_evidence
```

## Explicitly excluded from initial MVP schema

```text
users
authentication_sessions
payments
accounting_records
crm_pipeline
vector_documents
embeddings
webhook_events
real_time_whatsapp_messages
advanced forecasting tables
```

These may become relevant to future versions but are outside the three-week MVP.

---

# 32. RAG and Vector Database

No vector database is required for the initial MVP schema.

For a question such as:

```text
How many inquiries became orders?
```

the expected path is:

```text
SQLite
 ↓
SQL query / analytics
 ↓
LLM explanation
```

rather than:

```text
Vector database
 ↓
RAG
```

The MVP prioritizes structured database querying and evidence retrieval.

RAG can be considered later for:

- Semantic conversation search
- Business documents
- Policies
- Product catalogs
- FAQs
- Other unstructured knowledge

---

# 33. Initial Analytics Supported by the Schema

The schema shall support:

```text
Total customers
New customers
Returning customers
Total inquiries
Confirmed orders
Inquiry-to-order conversion
Top products/services
Frequently asked questions
Customer feedback summary
```

## Customer metrics

```text
customers
+
whatsapp_identities
+
conversations
```

## Inquiry metrics

```text
inquiries
```

## Order metrics

```text
orders
+
order_items
```

## Conversion

```text
inquiries
+
orders
```

## Product popularity

```text
inquiries.product_or_service
+
order_items.product_name
```

## Feedback

```text
feedback
```

## Customer history

```text
customer
 ↓
whatsapp_identities
 ↓
participants
 ↓
conversations
 ↓
messages
 ↓
inquiries / orders / feedback
```

The database/backend should perform the underlying calculations reliably.

---

# 34. Agent Tool Compatibility

The schema directly supports the MVP agent tools.

## `search_customers`

```text
customers
+
whatsapp_identities
```

## `get_customer_history`

```text
customers
 ↓
whatsapp_identities
 ↓
conversations
 ↓
messages
 ↓
inquiries / orders / feedback
```

## `search_conversations`

```text
conversations
+
messages
```

## `get_order`

```text
orders
+
order_items
+
extraction_evidence
```

## `search_orders`

```text
orders
+
order_items
```

## `get_feedback`

```text
feedback
+
extraction_evidence
+
source messages
```

## `query_business_metrics`

```text
SQLAlchemy queries
+
aggregations
```

---

# 35. Example End-to-End Data Flow

Consider:

```text
Customer:
"Hi akka, 1kg chocolate cake eka kiyada?"

Business:
"Rs. 4500."

Customer:
"Sunday delivery puluwanda?"

Business:
"Ow."

Customer:
"Okay confirm karanna."
```

The system stores the raw messages:

```text
Conversation
    │
    ├── Message 101
    ├── Message 102
    ├── Message 103
    ├── Message 104
    └── Message 105
```

AI extraction produces:

```text
Inquiry
    product = chocolate cake
    quantity = 1kg
    type = price_inquiry
```

and eventually:

```text
Order
    product = chocolate cake
    quantity = 1kg
    delivery = Sunday
    status = confirmed
```

Evidence:

```text
Order
  │
  └── ExtractionEvidence
          ├── Message 101
          ├── Message 103
          └── Message 105
```

The business owner can therefore ask:

> "What happened to this customer's cake order?"

The agent can retrieve:

```text
Customer
   ↓
Order
   ↓
Evidence
   ↓
Original messages
```

---

# 36. Customer Identity Example

Suppose the business has:

```text
WhatsApp Identity A
+94 77 111 1111
Name: Nethmi
```

Later:

```text
WhatsApp Identity B
+94 71 222 2222
Name: Nethmi
```

The system should initially represent:

```text
Customer A
    └── +94 77 111 1111

Customer B
    └── +94 71 222 2222
```

It may suggest:

```text
Possible same customer
```

The owner can then confirm:

```text
Confirm
```

resulting in:

```text
Customer A
    ├── +94 77 111 1111
    └── +94 71 222 2222
```

This prevents incorrect automatic merging when multiple customers have the same name.

---

# 37. Business-Type Generalization

The schema must not be designed specifically around cakes.

The same entities should support:

```text
Home bakery
Catering service
Freelance designer
Handyman
Tutor
Small retailer
Beauty service
Photographer
Other independent businesses
```

Therefore, the schema uses generic concepts such as:

```text
product_or_service
product_name
requirements
order
inquiry
customer
```

rather than business-specific tables such as:

```text
cakes
cake_orders
cake_customers
```

---

# 38. Open-Closed Principle and Schema Design

The database does not need a complex implementation of the Open-Closed Principle.

The schema should instead provide **stable generic boundaries**.

For example:

```text
Business
   ↓
Conversation
   ↓
Inquiry
Order
Feedback
```

can support different business types without changing the fundamental schema.

Avoid creating:

```text
BakeryOrder
HandymanOrder
DesignerOrder
CateringOrder
```

during the MVP.

The system should be:

```text
Generic at the data-model level
Simple at the implementation level
Extensible when real requirements appear
```

OCP should primarily guide the application/service architecture rather than forcing unnecessary database abstractions.

---

# 39. Schema Implementation Strategy

The complete schema is defined now, but implementation should proceed incrementally.

## Stage 1 — Database Foundation

Implement:

```text
database connection
SQLAlchemy Base
SQLite configuration
foreign-key enforcement
migration/schema initialization
```

---

## Stage 2 — Raw Data Models

Implement:

```text
Business
Customer
WhatsAppIdentity
ImportBatch
Conversation
Participant
Message
Media
```

This corresponds primarily to Week 1.

---

## Stage 3 — Constraints and Indexes

Implement:

```text
Primary keys
Foreign keys
Unique constraints
Indexes
Message fingerprint
```

---

## Stage 4 — Schema Verification

Verify:

```text
Tables created
Relationships work
Foreign keys work
Unique constraints work
Duplicate detection works
Incremental import works
```

---

## Stage 5 — Import Pipeline

```text
WhatsApp ZIP
      ↓
Parser
      ↓
ImportBatch
      ↓
Raw models
      ↓
SQLite
```

---

## Stage 6 — Derived Business Models

Implement:

```text
Inquiry
Order
OrderItem
Feedback
ExtractedFact
ExtractionEvidence
```

This corresponds primarily to Week 2.

---

## Stage 7 — AI Extraction

```text
Message
 ↓
LLM structured output
 ↓
Pydantic/schema validation
 ↓
Business validation
 ↓
Derived models
 ↓
Evidence
```

---

## Stage 8 — Analytics and Agent

```text
SQLite
 ↓
Analytics queries
 ↓
Agent tools
 ↓
LangGraph
 ↓
AI Business Assistant
```

This corresponds primarily to Week 3.

---

# 40. Schema Acceptance Criteria

The schema is considered ready for implementation when:

- [x] Business entity is defined.
- [x] Customer entity is defined.
- [x] WhatsApp identity is separated from customer.
- [x] Import batch is defined.
- [x] Conversation is defined.
- [x] Participant is defined.
- [x] Message is defined.
- [x] Media is defined.
- [x] Inquiry is defined.
- [x] Order is defined.
- [x] OrderItem is defined.
- [x] Feedback is defined.
- [x] ExtractedFact is defined.
- [x] ExtractionEvidence is defined.
- [x] Every entity has a primary key.
- [x] Required foreign keys are identified.
- [x] Raw and derived data are separated.
- [x] Multiple WhatsApp identities per customer are supported.
- [x] Conservative customer identity resolution is supported.
- [x] Incremental imports are supported.
- [x] Duplicate message detection has a defined strategy.
- [x] AI-derived data has extraction metadata.
- [x] AI-derived information can be traced to evidence.
- [x] Human review states are supported.
- [x] Required indexes are identified.
- [x] MVP analytics are supported.
- [x] MVP agent tools are supported.
- [x] Unnecessary RAG/CRM/accounting infrastructure is excluded.

---

# 41. MVP Entity Summary

The revised MVP schema contains **14 entities**:

```text
1.  Business
2.  Customer
3.  WhatsAppIdentity
4.  ImportBatch
5.  Conversation
6.  Participant
7.  Message
8.  Media
9.  Inquiry
10. Order
11. OrderItem
12. Feedback
13. ExtractedFact
14. ExtractionEvidence
```

The first eight primarily support the **data ingestion and raw-data foundation**.

The next five represent **business intelligence derived from conversations**.

`ExtractionEvidence` provides the **provenance layer** connecting AI-derived information back to raw messages.

---

# 42. Final Baseline Architecture

```text
┌─────────────────────────────────────────────────────┐
│                 BUSINESS / IDENTITY                 │
│                                                     │
│  businesses                                         │
│  customers                                          │
│  whatsapp_identities                                │
└──────────────────────────┬──────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────┐
│                 IMPORT / RAW DATA                   │
│                                                     │
│  import_batches                                     │
│  conversations                                      │
│  participants                                       │
│  messages                                            │
│  media                                               │
└──────────────────────────┬──────────────────────────┘
                           │
                           │ AI extraction
                           ▼
┌─────────────────────────────────────────────────────┐
│             BUSINESS KNOWLEDGE                      │
│                                                     │
│  inquiries                                           │
│  orders                                              │
│  order_items                                         │
│  feedback                                            │
│  extracted_facts                                    │
└──────────────────────────┬──────────────────────────┘
                           │
                           │ evidence
                           ▼
┌─────────────────────────────────────────────────────┐
│                PROVENANCE                           │
│                                                     │
│  extraction_evidence                                │
│          │                                          │
│          └──────────────► messages                   │
└──────────────────────────┬──────────────────────────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
        Analytics Tools         Agent Tools
                │                     │
                └──────────┬──────────┘
                           ▼
                  AI Business Assistant
                           │
                           ▼
                    Business Owner
```

---

# 43. Final Design Decision

This document is the **Database Schema Specification baseline for the ChatInsights MVP**.

The database should be designed completely at this level before implementation, but the models should be implemented incrementally according to the three-week development milestones.

The next implementation artifact should therefore be:

```text
Database Schema Specification v1.1
                ↓
OpenSpec change:
database-foundation
                ↓
SQLAlchemy 2.x models
                ↓
SQLite schema
                ↓
Schema verification tests
```

The SQLAlchemy implementation should be derived from this specification rather than allowing the coding agent to invent database entities and relationships ad hoc during development.
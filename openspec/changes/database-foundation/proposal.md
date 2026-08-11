# Database Foundation

## Why

Blueprint BI currently has a working LangGraph/Gemini conversational prototype, but it does not yet have persistent structured storage for the business information that will be extracted from WhatsApp conversations.

The MVP requires a stable database foundation before implementing WhatsApp ingestion, AI extraction, analytics, and agent tools.

This change establishes the SQLite/SQLAlchemy data model and persistence layer required by those future capabilities.

The goal of this change is to create a **stable database contract**, not to implement the complete WhatsApp ingestion or AI processing pipeline.

---

## What Changes

* Introduce SQLite as the MVP persistence layer.
* Introduce SQLAlchemy 2.x for database access.
* Establish the core business-data schema.
* Create persistent storage for:

  * Business
  * Customer
  * WhatsApp identity/contact
  * Import batch
  * Conversation
  * Participant
  * Message
  * Media
  * Inquiry
  * Order
  * Order item
  * Feedback
  * Extracted fact
  * Extraction evidence
* Preserve raw conversation/message data separately from AI-derived business information.
* Establish relationships between customers, conversations, messages, inquiries, orders, feedback, and extracted facts.
* Establish source-message references for AI-derived information.
* Add appropriate primary keys, foreign keys, uniqueness constraints, and indexes required by the MVP.
* Support business-level ownership relationships so business data can be isolated.
* Provide database connection and session management.
* Provide the persistence foundation required by future ingestion, extraction, analytics, and LangGraph agent tools.

---

## Capabilities

### New Capabilities

#### `business-data-foundation`

Provides the persistent SQLite/SQLAlchemy data model for ChatInsights.

The capability shall support:

* Business ownership relationships
* Customer/contact records
* WhatsApp identities
* Conversations
* Participants
* Messages
* Media metadata
* Inquiries
* Orders and order items
* Customer feedback
* AI-derived facts
* Extraction evidence
* Source-message traceability

### Modified Capabilities

None.

---

## Scope Boundary

This change establishes the **database foundation only**.

The following are explicitly outside the scope of this change:

* WhatsApp ZIP parsing
* WhatsApp chat ingestion
* Incremental import processing
* Duplicate message detection logic
* AI information extraction
* Multilingual processing
* Business/personal relevance classification
* Analytics calculations
* LangGraph agent tools
* Dashboard functionality
* WhatsApp Business API integration
* RAG/vector database infrastructure
* Advanced video processing
* Production-scale database infrastructure

These capabilities will be implemented through subsequent OpenSpec changes using this database foundation.

---

## Data Integrity Requirements

The database shall:

1. Maintain referential integrity between related entities.
2. Prevent invalid references to non-existing records.
3. Preserve the relationship between derived information and its source message where applicable.
4. Prevent duplicate identities where a uniqueness rule is explicitly defined.
5. Support efficient retrieval of messages by conversation.
6. Support efficient retrieval of business data by business.
7. Store timestamps required for conversation and import history.

The database design should remain simple enough for the three-week MVP.

---

## Raw vs Derived Data

The database shall distinguish between:

### Raw conversation data

Examples:

* Original message content
* Sender
* Timestamp
* Message type
* Media reference

### AI-derived business data

Examples:

* Intent
* Inquiry
* Order
* Product
* Quantity
* Feedback
* Extracted facts

AI-derived information should reference its source message where possible.

Example:

```text
Raw message
    ↓
"Actually make it 1.5kg."
    ↓
Extracted fact
    ↓
Order quantity = 1.5kg
    ↓
source_message_id = 123
```

---

## Technology

The MVP shall use:

* Python
* SQLAlchemy 2.x
* SQLite

The design should avoid introducing infrastructure that is unnecessary for the MVP.

The schema should remain reasonably portable to PostgreSQL in the future.

---

## Backend Impact

The database foundation will be implemented under:

```text
backend/app/database/
```

The implementation should provide:

```text
database/
├── connection/session management
├── models
├── initialization
└── database utilities
```

The exact internal structure may be determined during the design phase.

---

## Future Dependencies

Subsequent OpenSpec changes will depend on this capability:

```text
database-foundation
        ↓
whatsapp-export-ingestion
        ↓
business-data-extraction
        ↓
business-analytics
        ↓
business-agent
        ↓
dashboard
```

The database foundation should therefore expose a clean persistence interface that can be reused by these components.

---

## Non-Goals

This change does not attempt to:

* Build a complete CRM.
* Implement real-time WhatsApp synchronization.
* Automatically merge customer identities.
* Implement AI extraction.
* Implement business analytics.
* Implement the AI assistant.
* Implement frontend functionality.
* Build production-scale infrastructure.

---

## Acceptance Summary

The change is complete when:

* SQLite can be initialized successfully.
* SQLAlchemy models for the required MVP entities exist.
* Relationships between entities are defined.
* Foreign-key constraints are enforced where appropriate.
* Required indexes and uniqueness constraints exist.
* Raw messages can be persisted.
* Media metadata can be persisted.
* AI-derived records can reference source messages.
* Business ownership relationships are represented.
* Database sessions/connections can be created reliably.
* Basic database tests pass.
* The schema is ready to be consumed by the subsequent WhatsApp ingestion change.

---

## Expected Outcome

After this change, the project should have a stable database foundation that allows the next OpenSpec change to implement:

```text
WhatsApp Export ZIP
        ↓
Ingestion
        ↓
Database
```

without requiring another major database redesign.

The database foundation should be considered an **enabling capability**, not the complete business intelligence implementation.

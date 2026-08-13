## Context

Blueprint BI currently has a working Python/LangGraph backend and a validated SQLite connection through SQLAlchemy. The `business-data-foundation` specification defines the persistent data contract for the MVP, including 14 entities covering business identity, raw WhatsApp data, derived business information, and extraction evidence.

The implementation must provide a stable persistence layer for subsequent capabilities without implementing WhatsApp ingestion, AI extraction, analytics, or LangGraph tools in this change.

The revised database schema defines the following entities:

1. Business
2. Customer
3. WhatsApp Identity
4. Import Batch
5. Conversation
6. Participant
7. Message
8. Media
9. Inquiry
10. Order
11. Order Item
12. Feedback
13. Extracted Fact
14. Extraction Evidence

See `proposal.md` for the motivation and `specs/business-data-foundation/spec.md` for the required behavior.

## Goals / Non-Goals

**Goals:**

- Implement the complete MVP database schema defined by the database specification.
- Use SQLAlchemy 2.x as the application's ORM and persistence layer.
- Use SQLite as the MVP database.
- Provide a centralized database engine and managed session mechanism.
- Organize the 14 entities into maintainable SQLAlchemy model modules.
- Implement primary keys, foreign keys, uniqueness constraints, indexes, and required relationships.
- Preserve the separation between raw WhatsApp data and AI-derived business data.
- Support evidence relationships between derived records and source messages.
- Enforce business ownership relationships at the persistence layer.
- Enable SQLite foreign-key enforcement.
- Provide deterministic database initialization for a new development environment.
- Provide automated database tests covering schema creation, relationships, constraints, isolation, and transaction behavior.

**Non-Goals:**

- WhatsApp ZIP parsing or ingestion.
- Incremental import processing.
- Message duplicate-detection workflow.
- AI extraction or LLM integration.
- Business/personal relevance classification.
- Analytics implementation.
- LangGraph tools.
- Dashboard functionality.
- WhatsApp Business API integration.
- RAG or vector database infrastructure.
- Advanced media interpretation.
- Production database deployment or scaling.
- Authentication and authorization.

## Decisions

### 1. Use SQLite for the MVP database

**Decision:** Use SQLite as the persistent database for the MVP.

**Rationale:**

The MVP is a three-week development project and currently requires a local, persistent relational database rather than a production-scale database service. SQLite provides relational constraints, transactions, indexing, and SQL querying without requiring a separate database server.

The existing backend already has a working SQLite connection, so continuing with SQLite avoids unnecessary infrastructure during the MVP.

**Alternative considered: PostgreSQL**

PostgreSQL would provide stronger production-oriented capabilities and easier future multi-user scaling, but introducing a database server during the MVP would add operational complexity that is not required by the current specification.

The application should keep database access behind SQLAlchemy so that migration to PostgreSQL can be considered later without coupling business logic directly to SQLite.

---

### 2. Use SQLAlchemy 2.x as the ORM

**Decision:** Implement the persistence layer using SQLAlchemy 2.x declarative models.

**Rationale:**

SQLAlchemy is already installed and the backend has a verified SQLAlchemy-to-SQLite connection. SQLAlchemy provides typed model definitions, relationships, constraints, sessions, transactions, and database abstraction while keeping application code independent from SQLite-specific SQL.

**Alternative considered: raw SQLite queries**

Direct SQLite queries would reduce ORM abstraction but would make relationship management, model consistency, and future database migration more difficult.

**Alternative considered: another ORM**

Introducing another ORM would provide no benefit for the current project because SQLAlchemy is already established in the backend.

---

### 3. Use a shared declarative model base

**Decision:** All database entities SHALL derive from a single shared SQLAlchemy declarative base.

The base will be responsible for collecting the application's metadata so that the complete schema can be initialized consistently.

The model layer will be separate from connection/session configuration.

Conceptually:

    database/
    ├── connection.py
    ├── base.py
    └── models/
        ├── business.py
        ├── customer.py
        ├── whatsapp_identity.py
        ├── import_batch.py
        ├── conversation.py
        ├── participant.py
        ├── message.py
        ├── media.py
        ├── inquiry.py
        ├── order.py
        ├── order_item.py
        ├── feedback.py
        ├── extracted_fact.py
        └── extraction_evidence.py

**Rationale:**

Fourteen entities are large enough that placing every model in one file would reduce maintainability. Separate model modules make relationships and future changes easier to understand.

**Alternative considered: one `models.py` file**

A single model file would initially be simpler but would become difficult to navigate as the schema and relationships grow.

---

### 4. Separate database connection, models, and session management

**Decision:** Database infrastructure will be separated into:

- Connection/engine configuration
- Declarative base
- Model definitions
- Session management

The existing `connection.py` will remain responsible for the database engine and connection configuration.

A dedicated session mechanism will provide managed database access to application components.

**Rationale:**

This separation prevents application components from creating database engines or sessions independently and provides one consistent database access pattern.

**Alternative considered: create sessions directly throughout the application**

This would make connection lifecycle management inconsistent and increase the risk of leaked or incorrectly managed sessions.

---

### 5. Organize models according to the revised schema layers

**Decision:** Models will be organized around the three conceptual areas of the database specification.

Business and identity:

    Business
    Customer
    WhatsAppIdentity

Import and raw WhatsApp data:

    ImportBatch
    Conversation
    Participant
    Message
    Media

Derived business information:

    Inquiry
    Order
    OrderItem
    Feedback
    ExtractedFact
    ExtractionEvidence

The database itself remains relational; this organization is for maintainability only.

**Rationale:**

This structure makes the raw-versus-derived boundary visible in the codebase and aligns implementation with the database specification.

---

### 6. Preserve raw data independently from derived data

**Decision:** Raw WhatsApp entities will not be overwritten by AI-derived information.

Raw information will be persisted through:

    ImportBatch
    Conversation
    Participant
    Message
    Media

Derived information will be persisted through:

    Inquiry
    Order
    OrderItem
    Feedback
    ExtractedFact
    ExtractionEvidence

**Rationale:**

The original message is the evidence source. AI-derived information can be corrected, reviewed, or replaced without destroying the original conversation data.

This also allows future extraction logic to be improved without requiring re-import of the original source data.

---

### 7. Model evidence as a separate relationship

**Decision:** `ExtractionEvidence` will be implemented as a dedicated entity that links a derived business record to one source message.

The evidence model SHALL support evidence for the following derived record types:

- Inquiry
- Order
- Feedback
- Extracted Fact

A single derived record SHALL be able to reference multiple source messages.

A single source message SHALL be able to support multiple derived records.

The implementation SHALL use explicit relationships rather than relying on unvalidated string identifiers.

Conceptually:

    Inquiry ─────────────┐
    Order ──────────────┤
    Feedback ───────────┤
    ExtractedFact ──────┤
                         ▼
                 ExtractionEvidence
                         │
                         ▼
                      Message

The exact relational implementation may use explicit nullable foreign-key relationships for the supported derived record types, provided that the design enforces that each evidence record refers to the intended derived record and source message.

An evidence record SHALL NOT be allowed to reference multiple derived record types simultaneously.

**Rationale:**

A business conclusion may depend on multiple messages.

For example:

    Message 101: "I need a chocolate cake."
    Message 102: "For 10 people."
    Message 103: "Can you deliver Saturday?"

These messages may collectively support one order.

A separate evidence entity provides a flexible provenance model without duplicating source-message content.

Explicit relationships also preserve database-level referential integrity and make evidence retrieval predictable for future analytics and agent tools.

**Alternative considered: store only `source_message_id` on every derived table**

This would support only a simple evidence relationship and would not adequately represent derived information supported by multiple messages.

**Alternative considered: generic `derived_type` + `derived_id` fields**

A polymorphic identifier could support multiple derived entity types, but it would weaken database-level referential integrity because the database could not directly enforce that the referenced derived record exists.

For the MVP, explicit relationships are preferred because correctness and traceability are more important than minimizing the number of columns.

---

### 8. Represent customer identity separately from WhatsApp identity

**Decision:** `Customer` and `WhatsAppIdentity` will remain separate entities.

A WhatsApp identity may reference a logical customer, while a customer may have multiple WhatsApp identities.

A WhatsApp identity will be unique within the applicable business scope according to the database specification.

**Rationale:**

A WhatsApp number represents an observed communication identity, not necessarily a confirmed real-world customer identity.

Separating the two prevents unsafe automatic customer merging and allows future identity resolution.

**Alternative considered: store phone number directly on Customer**

This would prevent representing multiple WhatsApp identities for one customer and would make future identity resolution harder.

---

### 9. Preserve business ownership through explicit relationships

**Decision:** Business-owned entities will maintain a determinable relationship to `Business`.

Where appropriate, entities will have a direct `business_id` foreign key. Where ownership can be determined through a parent relationship, the relationship will remain explicit and testable.

The implementation will not rely solely on application convention to determine ownership.

**Rationale:**

Business isolation is a required behavioral property. Explicit ownership relationships make it possible for downstream queries and services to restrict data correctly.

The database foundation establishes the ownership relationships; application-level authentication and authorization are outside the scope of this change.

---

### 10. Use foreign keys and enforce them in SQLite

**Decision:** Foreign-key constraints will be declared in SQLAlchemy models and SQLite foreign-key enforcement will be explicitly enabled for database connections.

**Rationale:**

SQLite does not provide the desired referential-integrity behavior unless foreign-key enforcement is enabled for the connection.

Enabling it at the database infrastructure level prevents orphaned relationships.

**Alternative considered: application-only validation**

Application validation alone is insufficient because another code path could bypass the validation and create invalid relationships.

---

### 11. Use database constraints for uniqueness and integrity

**Decision:** Uniqueness requirements defined by the database specification will be represented using database-level unique constraints or unique indexes.

Examples include business-scoped WhatsApp identity uniqueness and stable message/source identifiers where applicable.

**Rationale:**

Uniqueness is a database integrity rule and should not depend solely on application-level checks.

Application checks can still provide user-friendly validation, but the database remains the final integrity boundary.

---

### 12. Use indexes based on expected MVP access patterns

**Decision:** Indexes will be created for frequently queried foreign keys and fields required by expected customer, conversation, message, order, feedback, and evidence lookups.

At minimum, indexes will cover the major business ownership and relationship fields, message timestamps, message identity/fingerprint fields, and relevant order/feedback lookup fields defined by the database specification.

**Rationale:**

The database will later support analytics and LangGraph tools that repeatedly query customer history, conversations, orders, feedback, and business metrics.

Indexes should therefore support expected access patterns without prematurely indexing every column.

**Alternative considered: index every column**

This would increase write/storage overhead without providing proportional benefit.

---

### 13. Store application timestamps consistently in UTC

**Decision:** Application-managed timestamps SHALL be generated and stored consistently using UTC.

The implementation SHALL distinguish between:

- Source timestamps from WhatsApp data
- Database creation/update timestamps
- Import timestamps
- Extraction timestamps

Source timestamps SHALL be preserved as the time represented by the original WhatsApp data and SHALL NOT be replaced by database insertion time.

Database-managed timestamps SHALL represent application processing events and SHALL use UTC consistently.

Where the SQLite representation does not preserve timezone metadata directly, the application layer SHALL treat stored application timestamps as UTC according to the project's timestamp convention.

**Rationale:**

The system needs to distinguish when an event actually occurred from when the record was imported or processed.

This is important for future analytics such as:

- Order dates
- Customer activity
- Conversation history
- Import history
- AI extraction timing

Using a single UTC convention also avoids ambiguity when data is later moved to a production database such as PostgreSQL.

---

### 14. Store monetary values using numeric database types

**Decision:** Monetary fields such as order totals and item prices will use SQLAlchemy numeric/decimal-compatible types rather than floating-point values.

**Rationale:**

Floating-point representation can introduce rounding errors for monetary values.

Using numeric values provides deterministic storage for future business analytics.

---

### 15. Use explicit relationship loading rather than relying on implicit application behavior

**Decision:** SQLAlchemy relationships will be explicitly declared for the schema relationships, while query loading strategies will be selected based on actual access patterns.

The database foundation will avoid unnecessary eager-loading behavior by default.

**Rationale:**

Customer history and conversation queries may involve multiple related entities. Loading everything automatically could create unnecessary queries or large object graphs.

Query-specific loading can be introduced by the services that consume the database.

---

### 16. Use transactions for related persistence operations

**Decision:** Related records that must succeed or fail together will be persisted within a single transaction.

For example, creating an order and its order items should be atomic.

If a transaction fails, the session will roll back so that partially persisted relationships are not left behind.

**Rationale:**

The specification explicitly requires transaction integrity.

**Alternative considered: commit each record independently**

Independent commits could leave incomplete business records, such as an order without all required order items.

---

### 17. Use metadata-based initialization for the initial MVP schema

**Decision:** The database foundation will provide a repeatable initialization mechanism that creates the complete schema from the SQLAlchemy metadata for a new development database.

Initialization must be safe to execute against an already initialized development database without attempting to recreate existing tables.

**Rationale:**

The MVP currently requires a reliable local development setup rather than a production migration system.

This keeps initial setup simple while maintaining a clear schema contract.

**Alternative considered: introduce a migration framework immediately**

A migration framework would be useful for production schema evolution, but it introduces additional tooling and workflow complexity that is not required for the initial database foundation.

Future schema evolution can introduce a migration capability when the project requires persistent database migrations.

---

### 18. Keep the database file outside source-controlled code

**Decision:** The SQLite database file will be stored under the backend data directory and excluded from Git.

The database schema and initialization logic will be version-controlled; generated database state will not be committed.

Expected development structure:

    backend/
    ├── app/
    │   └── database/
    └── data/
        └── blueprint.db

**Rationale:**

The SQLite file is generated application state rather than source code and may contain business/customer conversation data.

Keeping it out of Git also prevents accidental publication of potentially sensitive business information.

---

### 19. Keep database access independent of LangGraph and the LLM

**Decision:** The database layer will not import LangGraph, LangChain, Gemini, or other LLM-specific components.

Future LangGraph tools will depend on database service/query functions rather than embedding LLM behavior inside database models.

**Rationale:**

The database is a foundational capability that should remain independent of the AI orchestration layer.

This preserves the architectural boundary:

    Database
        ↓
    Application services
        ↓
    LangGraph tools
        ↓
    Agent / LLM

rather than:

    Database
        ↕
    LLM / LangGraph

This also supports the SRS requirement that deterministic database operations remain separate from LLM reasoning.

---

## Risks / Trade-offs

- **[Risk] SQLite has limited production concurrency compared with server databases.**
  → **Mitigation:** Keep database access behind SQLAlchemy and avoid SQLite-specific business logic so a future PostgreSQL migration remains possible.

- **[Risk] Database schema changes during the three-week MVP may require schema recreation.**
  → **Mitigation:** Treat the finalized database specification and OpenSpec change as the schema baseline. Introduce a migration framework in a future capability if persistent schema evolution becomes necessary.

- **[Risk] Incorrect relationship definitions could create orphaned or incorrectly scoped records.**
  → **Mitigation:** Enforce foreign keys at the database level and add integration tests for all critical relationships.

- **[Risk] Business data could accidentally cross business boundaries through incorrect queries.**
  → **Mitigation:** Preserve explicit business ownership relationships and test cross-business access scenarios. Application-level authentication and authorization are outside this change.

- **[Risk] AI-derived records may be stored without sufficient evidence.**
  → **Mitigation:** Model extraction evidence explicitly and require source-message references for supported derived information.

- **[Risk] Over-indexing could increase write overhead.**
  → **Mitigation:** Add indexes only for defined relationship and MVP query patterns.

- **[Risk] The database may contain sensitive customer conversation data.**
  → **Mitigation:** Keep generated SQLite files out of Git, avoid storing secrets in the database, and restrict database access to the backend application.

- **[Risk] The model structure may become too tightly coupled to the current bakery MVP.**
  → **Mitigation:** Use generic business entities such as Business, Customer, Inquiry, Order, Feedback, and ExtractedFact rather than bakery-specific table names.

- **[Risk] Ambiguous evidence relationships could weaken provenance.**
  → **Mitigation:** Use explicit foreign-key relationships from `ExtractionEvidence` to the supported derived entity types and validate that each evidence record identifies exactly one derived record and one source message.

## Migration Plan

This is an initial database foundation rather than a migration of an existing production database.

### Initial setup

1. Configure the SQLite database path under the backend data directory.
2. Initialize the SQLAlchemy engine and managed session mechanism.
3. Register all 14 SQLAlchemy models with the shared metadata.
4. Enable SQLite foreign-key enforcement.
5. Initialize the complete MVP schema for a new development database.
6. Run database integration tests.
7. Verify that all required tables, relationships, constraints, and indexes exist.

### Existing local development database

If an existing local database was created from an earlier experimental schema and is not required as persistent data, it may be recreated from the finalized schema during this MVP stage.

No production-data migration is required for this change.

### Rollback

If implementation tests fail or the schema implementation is rejected before dependent capabilities are built:

1. Remove the generated local SQLite database.
2. Revert the database-foundation implementation changes.
3. Recreate the database from the validated schema after corrections.

Once real imported business data exists, destructive recreation SHALL NOT be used as a production migration strategy. A future migration capability will be required before persistent schema changes are applied to retained business data.

## Open Questions

None at this stage.

The database technology, entity scope, raw/derived boundary, evidence model, ownership model, initialization approach, timestamp convention, and persistence architecture are sufficiently defined to create the implementation task breakdown without changing the validated specification.
## Context

The extraction capability converts relevance-eligible WhatsApp conversation content into
structured business data (Order, OrderItem, Inquiry, Feedback, ExtractedFact) and records
evidence linkage via ExtractionEvidence.

Pipeline flow:
  WhatsApp ingestion -> relevance detection -> context-aware AI extraction -> structured business data -> analytics

The business-data-foundation SQLAlchemy models already exist. The business-relevance-detection
capability provides RelevanceAssessment records that determine extraction eligibility.
Extraction must not modify any upstream record.

**Database reality (confirmed from models.py):**

- ExtractionEvidence has a CHECK constraint: exactly one of inquiry_id / order_id /
  feedback_id / extracted_fact_id must be non-null per row.
- ExtractionEvidence.message_id is the evidence message — NOT necessarily the target message.
  The target message is not automatically recorded as evidence.
- Order.status defaults to 'inquiry'; no DB CHECK constraint; application enforces valid values.
- OrderItem.quantity is Numeric(12,3), NOT NULL.
- OrderItem.unit_price is Numeric(12,2), NOT NULL in the current schema.
  This MUST be made nullable — see Decision 13 (Schema Change).
- Inquiry has inquiry_type (String 100, non-nullable) and summary (Text, non-nullable).
- Feedback has sentiment, topic, and comment — all non-nullable.
- ExtractedFact has model_name and model_version fields already, which can record provenance.
- ExtractedFact.status exists as String(50), NOT NULL, default='pending'.
- WhatsAppIdentity.customer_id is nullable — the reliable association path already exists.
- There is NO extraction target processing table — one MUST be added (see Decision 10).

---

## Goals / Non-Goals

**Goals:**
- Convert relevant WhatsApp messages into validated, structured business records.
- Preserve full evidence traceability (target -> context -> evidence -> derived record).
- Keep extraction independent from ingestion and relevance layers.
- Support uncertainty, human review, and incremental/idempotent processing.

**Non-Goals:**
- RAG, embeddings, vector databases, semantic retrieval.
- LangGraph multi-step agents or autonomous orchestration.
- Customer identity resolution from LLM output.
- Real-time/streaming extraction.
- Advanced analytics or dashboards.

---

## Decisions

---

**Decision 1: LLM Structured Output API (response_schema / JSON mode)**

- *Rationale:* We must guarantee typed fields (integers for quantities, ISO dates, Decimal-
  compatible strings for prices). Structured output APIs enforce schema at the provider level
  before the response reaches the application.
- *Alternatives rejected:* Free-form prompt engineering — too brittle, frequent JSON decode
  errors in practice.

---

**Decision 2: Dedicated ExtractionService**

- *Rationale:* Extraction must be transaction-isolated from ingestion and relevance. An LLM
  API failure must not crash the ingestion pipeline. A dedicated service manages its own
  session scope and rollback boundary.
- *Alternatives rejected:* Embedding extraction logic inside IngestionService or
  RelevanceService — violates separation of concerns, increases blast radius of failures.

---

**Decision 3: Pydantic extraction schemas as the LLM contract**

Pydantic models define the expected LLM output shape for each entity type:

  CandidateOrderItem  — product_name (str), quantity (Decimal > 0), unit_price (Decimal | None), evidence_message_ids (list[int])
  CandidateOrder      — status (str), total_amount (Decimal | None), items (list[CandidateOrderItem]), evidence_message_ids (list[int])
  CandidateInquiry    — inquiry_type (str), summary (str), status (str), confidence (Decimal | None), evidence_message_ids (list[int])
  CandidateFeedback   — sentiment (str), topic (str), comment (str), confidence (Decimal | None), evidence_message_ids (list[int])
  CandidateFact       — fact_type (str), fact_value (str), confidence (Decimal | None), evidence_message_ids (list[int])
  ExtractionResult    — orders, inquiries, feedbacks, facts, target_message_id (int), context_message_ids (list[int])

unit_price is Optional/nullable in the Pydantic schema. The DB column is also nullable
after the schema migration (Decision 13). Zero is never used as a sentinel for unknown price.

These are DTOs, NOT SQLAlchemy models.

- *Rationale:* Pydantic provides automatic type coercion and validation as the first gate.
- *Alternatives rejected:* Raw JSON schemas — harder to maintain, no automatic Python validation.

---

**Decision 4: LLM Provider Abstraction**

The ExtractionService calls a thin provider interface:

  class LLMProvider(Protocol):
      def extract(self, prompt: str, schema: dict) -> dict: ...

The MVP implementation wraps google-genai (Gemini). Tests use a FakeLLMProvider that returns
pre-built dicts without making real API calls.

- *Rationale:* Decouples domain schemas and ExtractionService from provider-specific response
  objects. Allows test isolation and future provider swap.
- *Scope:* No elaborate abstraction beyond the single extract() method for the MVP.

---

**Decision 5: Deterministic Bounded Context Window**

Context is selected as follows:

  1. Query the same Conversation ordered by sent_at ASC.
  2. Find the target message position in the ordered list.
  3. Take up to CONTEXT_WINDOW_BEFORE messages immediately preceding the target.
  4. Take up to CONTEXT_WINDOW_AFTER messages immediately following the target.
  5. Filter: include only messages with relevance_state IN ('relevant', 'needs_review').
     Exclude 'pending' and 'not_relevant'.
  6. The target message is always included and explicitly marked in the LLM prompt.

Default: CONTEXT_WINDOW_BEFORE = 5, CONTEXT_WINDOW_AFTER = 2 (configurable).

- *Rationale:* Simple, deterministic, testable, chronologically correct. Does not require
  token counting, embeddings, or semantic retrieval for the MVP.
- *Trade-off:* A fixed window may miss distant context in very long conversations. Acceptable
  for MVP; a smarter strategy can be introduced in a future change.
- *Alternatives rejected:* Full-conversation extraction (noise, token limits, cost);
  semantic/embedding-based retrieval (out of scope).

---

**Decision 6: Target / Context / Evidence Separation**

The LLM prompt explicitly marks the target message and labels context messages.
The ExtractionResult Pydantic model carries:
  - target_message_id: the ID of the target message
  - context_message_ids: IDs sent as context
  - evidence_message_ids: per-candidate, the IDs the LLM claims as evidence

After receiving the result, the application validates evidence_message_ids:
  - Each ID must exist in the message table.
  - Each ID must belong to the same conversation and business.
  - If any evidence ID is invalid, the candidate entity is rejected.

Context messages are NOT automatically recorded as ExtractionEvidence unless the LLM
also cites them as evidence for a specific entity.
The target message is NOT automatically recorded as ExtractionEvidence. It must be explicitly
cited in the evidence_message_ids for an entity if it supports that entity.

---

**Decision 7: Two-Level Validation Pipeline**

  Level A — ExtractionResult validation (response-level):
    Pydantic parsing of the full LLM response into ExtractionResult.
    If this fails: reject the entire response; no DB writes; mark attempt retryable.

  Level B — Per-candidate validation (entity-level, runs after Level A passes):
    For each candidate entity independently:
      B1. Evidence ID validation   (IDs exist, same conversation/business)
      B2. Business consistency     (e.g. confirmed Order must have >= 1 item)
      B3. Uncertainty/review       (confidence threshold -> status assignment)
    If B1 fails for a candidate: reject the entire candidate (any invalid evidence ID
      rejects the whole entity; do not silently filter and continue with remaining IDs).
    If B2 fails for a candidate: reject that candidate; continue with others.

  Level C — Transactional persistence of the accepted candidate set:
    All accepted entities + child records + ExtractionEvidence persisted in one transaction.
    DB failure rolls back the entire accepted set. No partial state is left.

Pydantic alone is NOT the trust boundary. Level B catches schema-valid but semantically
invalid output (hallucinated message IDs, confirmed Order with no items, etc.).

---

**Decision 8: Order / Inquiry / Tentative Intent Semantics**

Confirmed order rule: a confirmed Order requires:
  (a) at least one identifiable product or service (product_name supported by evidence),
  (b) quantity > 0 satisfying the non-nullable OrderItem quantity schema, supported by evidence, AND
  (c) an explicit purchase commitment supported by evidence.
Price is NOT required. Unknown price remains unit_price = NULL, line_total = NULL.
If quantity cannot be reliably established, do not create an Order candidate requiring
an OrderItem. Represent the available business meaning as Inquiry or ExtractedFact,
as appropriate to the evidence.

Order.status represents the BUSINESS STATE of the order, not extraction uncertainty.
A confirmed purchase commitment -> Order.status = 'confirmed' regardless of whether price is known.
Do not downgrade Order.status to 'needs_review' merely because unit_price is NULL.
Provenance that price was unavailable at extraction time is recorded in
ExtractionEvidence.evidence_text, not in ExtractionTarget.failure_reason.
ExtractionTarget.failure_reason is used only for actual failed extraction attempts.

The LLM prompt instructs the model to:
  - Return an Inquiry (status='open') when the conversation contains a question or interest
    without a confirmed purchase commitment.
  - Return an Order with status='pending' when signals are partial or uncertain (but quantity is known).
  - Return an Order with status='confirmed' when an identifiable product, quantity > 0, and
    explicit purchase commitment are all supported by evidence. Price may be null.
  - Return an ExtractedFact for tentative future intent without creating an Order.
  - Leave unit_price null when price is not stated; do NOT invent a price.
  - Return an Inquiry or ExtractedFact when quantity cannot be established from
    conversation evidence; do NOT invent a quantity, and do NOT create an incomplete Order.

Level B business consistency enforces:
  - An Order with status='confirmed' MUST have at least one CandidateOrderItem.
  - A CandidateOrderItem MUST have product_name (non-empty) and quantity > 0.
  - A CandidateOrderItem.unit_price = None is valid and must NOT cause rejection.
  - line_total is computed only when unit_price is known; when unit_price is NULL,
    line_total is also NULL (after the schema migration makes both nullable).
  - An Inquiry MUST have inquiry_type and summary.

Valid application-layer Order.status values: 'inquiry', 'pending', 'confirmed', 'cancelled'.
(Do not use 'needs_review' on Order.status for extraction uncertainty.)

---

**Decision 9: Customer Association**

Customer association uses the existing database relationship:

  Participant.whatsapp_identity_id
    -> WhatsAppIdentity.customer_id   (nullable)
      -> Customer.id

Algorithm:
  1. From the target message, get Participant.whatsapp_identity_id.
  2. If present, load WhatsAppIdentity.customer_id.
  3. If customer_id is non-null, set it on the derived record.
  4. Otherwise, set customer_id = null.

The LLM does NOT participate in this lookup. No new Customer record is created.
No WhatsAppIdentity records are merged or modified.

---

**Decision 10: Idempotency Strategy — ExtractionTarget Table**

ExtractionEvidence.message_id records the evidence message, NOT the processing target.
The target message is not guaranteed to become an evidence message. Therefore
ExtractionEvidence cannot reliably serve as the idempotency ledger.

A minimal new table ExtractionTarget is required:

  extraction_target
    id                  INTEGER PRIMARY KEY
    message_id          INTEGER NOT NULL FK(message.id)
    business_id         INTEGER NOT NULL FK(business.id)
    status              VARCHAR(50) NOT NULL DEFAULT 'pending'
                        -- values: 'pending', 'succeeded', 'failed'
    attempted_at        DATETIME WITH TIMEZONE nullable
    completed_at        DATETIME WITH TIMEZONE nullable
    failure_reason      TEXT nullable
    created_at          DATETIME WITH TIMEZONE NOT NULL
    UNIQUE (message_id, business_id)

Algorithm:
  Before extraction:
    1. Look up ExtractionTarget WHERE message_id = target.id AND business_id = business.id.
    2. If status = 'succeeded': skip (idempotency guard).
    3. If status = 'failed': allow retry (update status to 'pending', clear failure_reason).
    4. If no row: create with status = 'pending'.

  On success: UPDATE ExtractionTarget SET status='succeeded', completed_at=now.
  On failure: UPDATE ExtractionTarget SET status='failed', failure_reason=<reason>.

This correctly handles:
  - Retry of same target without duplicates.
  - Multiple evidence messages per derived record.
  - Target message not being an evidence message.
  - Incremental imports (new messages get new ExtractionTarget rows).
  - Failed attempts are retryable.
  - Succeeded vs failed is distinguishable.

- *Alternatives rejected:* ExtractionEvidence as processing ledger — semantically incorrect;
  the target is not necessarily a piece of evidence.

---

**Decision 11: Transaction Boundary**

Each extraction of a single target message uses two transactions:

  Transaction 1 — Create/update ExtractionTarget (status='pending'):
    Committed before LLM call so the target is visible as in-progress.

  Transaction 2 — Persist accepted candidates:
    BEGIN
      INSERT Order(s), OrderItem(s)
      INSERT Inquiry/Feedback/ExtractedFact
      INSERT ExtractionEvidence rows
      UPDATE ExtractionTarget SET status='succeeded'
    COMMIT  (or ROLLBACK on any failure)

Raw Message, Conversation, RelevanceAssessment records are NEVER written within either
transaction.

---

**Decision 12: Failure Handling**

| Failure type | Behaviour |
|---|---|
| LLM provider unavailable / timeout | Mark ExtractionTarget failed; log; no derived DB writes |
| ExtractionResult Pydantic failure | Mark ExtractionTarget failed; log; entire response rejected |
| Any evidence_message_id invalid (missing/wrong conv/wrong biz) | Reject the entire candidate; log; continue with other valid candidates |
| Candidate business consistency failure | Reject that candidate; log; continue with valid candidates |
| All candidates rejected | Mark ExtractionTarget failed (not succeeded); log; no derived DB writes |
| DB persistence failure | Rollback Transaction 2; mark ExtractionTarget failed; log |

ExtractionTarget status = 'succeeded' ONLY when at least one candidate was accepted and persisted.
Retries: re-queue the target message_id. ExtractionTarget status='failed' allows retry.

---

**Decision 13: Schema Changes (Minimal, Scoped to this Change)**

The project does NOT use Alembic (no alembic.ini exists). Schema is managed via
Base.metadata.create_all() in app.database.init_db(). SQLite does not support
ALTER COLUMN. Two changes are required:

  Change A: Make OrderItem.unit_price and line_total nullable

    Current: unit_price Numeric(12,2) NOT NULL, line_total Numeric(12,2) NOT NULL.
    Required: both must accept NULL when price is unknown at extraction time.

    Migration strategy: SQLite-native recreate-table Python script.

    The script must:
      1. Back up the current database file (blueprint_before_extraction_migration.db)
         before applying any changes — consistent with the existing
         blueprint_before_relevance_migration.db backup pattern.
      2. Create a new order_item table with nullable unit_price and line_total.
      3. Copy all existing rows exactly, preserving primary keys, foreign keys,
         indexes, constraints, and all existing non-null values.
      4. Drop the old table and rename the new one.
      5. Verify row count is unchanged and no non-null values were altered.
      6. Be idempotent: inspect sqlite_master DDL first; if unit_price is already
         nullable, exit without modification.

    Rollback: restore from the backup file.
    Existing non-null unit_price and line_total values are preserved exactly.
    NULL is only a newly permitted value for new extraction-sourced rows.

  Change B: Add ExtractionTarget table

    The ExtractionTarget SQLAlchemy model is added to models.py.
    Base.metadata.create_all() will create extraction_target in new and
    in-memory test databases automatically — no migration script needed.
    For the existing blueprint.db, the Change A migration script also calls
    Base.metadata.create_all() after the recreate-table step so the new
    table is created in the same migration run.

    Model columns: id (PK), message_id (FK message.id NOT NULL),
      business_id (FK business.id NOT NULL), status (String 50 NOT NULL,
      default 'pending'), attempted_at (DateTime TZ nullable),
      completed_at (DateTime TZ nullable), failure_reason (Text nullable),
      created_at (DateTime TZ NOT NULL).
    Unique constraint on (message_id, business_id).
    Valid status values: 'pending', 'succeeded', 'failed'.

No other schema changes are required.

---

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| LLM hallucinates schema-valid but unsupported values | Level B evidence ID validation; null for missing fields; no zero sentinel |
| Context window too small — misses key messages | Configurable window; human review for uncertain extractions |
| Context window too large — adds noise | Relevance filter (exclude pending/not_relevant); default window is narrow |
| Duplicate extraction on retry | ExtractionTarget status='succeeded' prevents re-processing |
| Provider failure causes data loss | No derived data is written on failure; ExtractionTarget records failure as retryable |
| Tentative intent becomes confirmed order | Prompt constraints + Level B business consistency (no price required, but commitment required) |
| LLM confidence scores are not inherently trustworthy | Confidence used as a hint only; Level B validation is the actual gate |
| unit_price / line_total NOT NULL in existing schema | SQLite-native recreate-table script; backup first; idempotent check; existing non-null values preserved; rollback via backup |
| Candidate partial rejection leaves incomplete result | Accepted candidates are persisted atomically; rejected candidates leave no trace |




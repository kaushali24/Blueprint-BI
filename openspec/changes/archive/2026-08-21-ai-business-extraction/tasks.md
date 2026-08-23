## 1. Extraction Module Foundation

- [x] 1.1 Create `backend/app/extraction/` package with `__init__.py`.
- [x] 1.2 Create `backend/app/extraction/constants.py` defining:
  - `EXTRACTION_ELIGIBLE_STATES = ('relevant',)`
  - `CONTEXT_ALLOWED_STATES = ('relevant', 'needs_review')`
  - `CONTEXT_WINDOW_BEFORE = 5`
  - `CONTEXT_WINDOW_AFTER = 2`
  - `ORDER_VALID_STATUSES = ('inquiry', 'pending', 'confirmed', 'cancelled')`
  - `CONFIDENCE_REVIEW_THRESHOLD = Decimal('0.70')`
- [x] 1.3 Create `backend/app/extraction/exceptions.py` defining:
  - `ExtractionValidationError`  (top-level response parse failure)
  - `ExtractionEvidenceError`    (candidate evidence validation failure)
  - `ExtractionProviderError`    (LLM provider failure)
  - `ExtractionConsistencyError` (candidate business consistency failure)

---

## 2. Schema Changes (Database)

Note: The project does NOT use Alembic. Schema is managed via Base.metadata.create_all()
in app.database.init_db(). SQLite does not support ALTER COLUMN. Do NOT introduce Alembic.

### 2a. SQLite Migration Script (unit_price and line_total)

- [x] 2.1 Create `backend/scripts/migrate_extraction_schema.py`:
  - Before any change: copy `backend/data/blueprint.db` to
    `backend/data/blueprint_before_extraction_migration.db` (backup).
  - Idempotency check: inspect sqlite_master DDL for `order_item`; if
    `unit_price` column definition does NOT include `NOT NULL`, skip and exit.
  - Recreate `order_item` with nullable `unit_price` and `line_total`:
    a. CREATE TABLE `order_item_new` with same columns but unit_price/line_total nullable.
    b. INSERT INTO `order_item_new` SELECT * FROM `order_item` (preserves all existing rows).
    c. Verify: `SELECT COUNT(*) FROM order_item_new` == `SELECT COUNT(*) FROM order_item`.
    d. DROP TABLE `order_item`.
    e. ALTER TABLE `order_item_new` RENAME TO `order_item`.
    f. Re-create all indexes that existed on `order_item`.
  - After recreate-table: call `Base.metadata.create_all(bind=engine)` to create the
    new `extraction_target` table in the existing `blueprint.db`.
  - Print row counts for verification.
- [x] 2.2 Verify the migration script is idempotent: running it twice does not alter the schema
  or data on the second run.

### 2b. ExtractionTarget SQLAlchemy Model

- [x] 2.3 Add `ExtractionTarget` SQLAlchemy model to `backend/app/database/models.py`:
  - id (Integer PK), message_id (FK message.id NOT NULL), business_id (FK business.id NOT NULL),
    status (String 50 NOT NULL DEFAULT 'pending'), attempted_at (DateTime TZ nullable),
    completed_at (DateTime TZ nullable), failure_reason (Text nullable),
    created_at (DateTime TZ NOT NULL).
  - UniqueConstraint on (message_id, business_id).
  - Valid status values enforced by application: 'pending', 'succeeded', 'failed'.
- [x] 2.4 `Base.metadata.create_all()` will create `extraction_target` automatically in
  new databases and in-memory test databases — no additional migration needed for these.

### 2c. Migration Tests

- [x] 2.5 Write `tests/test_extraction_schema_migration.py`:
  - Test A: Existing OrderItem data survives the migration.
    Create a pre-migration in-memory DB (with NOT NULL unit_price), insert OrderItem rows
    with known values, run migration logic, verify all rows present and values unchanged.
  - Test B: unit_price becomes nullable after migration.
  - Test C: line_total becomes nullable after migration.
  - Test D: Existing non-null unit_price / line_total values are unchanged post-migration.
  - Test E: Migration does not duplicate or destroy OrderItem rows.
  - Test F: Re-running the migration script (idempotent run) does not corrupt the database.
  - Test G: A newly created database (via create_all) receives the correct final schema
    (unit_price and line_total nullable; extraction_target table present).
  - Test H: ExtractionTarget table is created correctly by create_all in a new database.

---

## 3. Structured Extraction Schemas (Pydantic DTOs)

- [x] 3.1 Create `backend/app/extraction/schemas.py` with Pydantic models:
  - `CandidateOrderItem` — product_name (str), quantity (Decimal, > 0), unit_price (Decimal | None), evidence_message_ids (list[int])
  - `CandidateOrder` — status (str), total_amount (Decimal | None), items (list[CandidateOrderItem]), evidence_message_ids (list[int])
  - `CandidateInquiry` — inquiry_type (str), summary (str), status (str, default='open'), confidence (Decimal | None), evidence_message_ids (list[int])
  - `CandidateFeedback` — sentiment (str), topic (str), comment (str), confidence (Decimal | None), evidence_message_ids (list[int])
  - `CandidateFact` — fact_type (str), fact_value (str), confidence (Decimal | None), evidence_message_ids (list[int])
  - `ExtractionResult` — target_message_id (int), context_message_ids (list[int]), orders (list[CandidateOrder]), inquiries (list[CandidateInquiry]), feedbacks (list[CandidateFeedback]), facts (list[CandidateFact])
- [x] 3.2 Validate: CandidateOrder.status must be in ORDER_VALID_STATUSES.
- [x] 3.3 Validate: CandidateOrderItem.quantity must be > 0.
- [x] 3.4 `CandidateOrderItem.unit_price` MUST be `Optional[Decimal]` (None is valid, zero is NOT a substitute for None).
- [x] 3.5 Write unit tests for all schema validation rules:
  - Valid order with unit_price = None is accepted.
  - Valid order with unit_price = 0 is accepted (0 may be a valid price in some contexts; absence of price = None).
  - Missing required fields (product_name, quantity) are rejected.
  - Invalid status values are rejected.
  - Negative or zero quantity is rejected.

---

## 4. LLM Provider Integration

- [x] 4.1 Create `backend/app/extraction/provider.py` defining:
  - `LLMProvider` Protocol with `extract(prompt: str, schema: dict) -> dict`
  - `GeminiProvider` implementing LLMProvider using google-genai structured output API
  - `FakeLLMProvider` for testing — accepts a pre-configured response dict; raises on demand
- [x] 4.2 GeminiProvider must NOT be instantiated during test runs; use FakeLLMProvider instead.
- [x] 4.3 Write unit tests for FakeLLMProvider (happy path, provider error simulation).

---

## 5. Context Selection

- [x] 5.1 Create `backend/app/extraction/context.py` with `select_context_window(session, target_message, business_id)`:
  - Queries messages from the same conversation ordered by sent_at ASC.
  - Takes up to CONTEXT_WINDOW_BEFORE messages before the target.
  - Takes up to CONTEXT_WINDOW_AFTER messages after the target.
  - Filters: include only messages with current RelevanceAssessment in CONTEXT_ALLOWED_STATES.
  - Excludes messages with relevance_state = 'pending' or 'not_relevant'.
  - Always includes the target message; marks it distinctly in the prompt payload.
  - Returns: (target_message, context_messages_ordered_by_sent_at)
- [x] 5.2 Write unit tests for context selection:
  - Target is correctly identified in result.
  - Window does not exceed configured size.
  - pending and not_relevant messages are excluded.
  - needs_review messages may be included.
  - Messages from other conversations are excluded.
  - Context is chronologically ordered.

---

  11. Set ExtractionTarget.status='succeeded', completed_at=now; commit
- [x] 6.3 Write unit tests for ExtractionService.is_eligible() (all four relevance states).
- [x] 6.4 Write unit tests for ExtractionTarget idempotency:
  - First call: ExtractionTarget created, extraction runs.
  - Second call with status='succeeded': extraction skipped, no duplicates.
  - Previous call with status='failed': extraction retried.

---

## 7. Output and Evidence Validation

- [x] 7.1 Create `backend/app/extraction/validation.py`:
  - `validate_evidence_ids(session, candidate, conversation_id, business_id) -> None`
    - Check that ALL evidence_message_ids exist in the DB.
    - Check that ALL belong to the correct `conversation_id`.
    - Check that ALL belong to the correct `business_id` (via Conversation.business_id).
    - Raise `ExtractionEvidenceError` if invalid.
  - `check_business_consistency(candidate) -> list[str]`
    Returns list of error strings. Rules:
    - CandidateOrder with status='confirmed' must have >= 1 item.
    - CandidateOrderItem must have non-empty product_name.
    - CandidateOrderItem quantity > 0.
    - CandidateOrderItem.unit_price = None is valid (not an error; price may be unknown).
    - CandidateOrderItem.line_total = None when unit_price = None (valid; not an error).
    - CandidateInquiry must have non-empty inquiry_type and summary.
    - CandidateFeedback must have non-empty sentiment, topic, comment.
- [x] 7.2 Write unit tests for validate_evidence_ids:
  - All valid IDs: passes without error.
  - One non-existent ID among otherwise valid IDs: raises ExtractionEvidenceError for entire candidate.
  - One ID from wrong conversation among otherwise valid IDs: raises ExtractionEvidenceError for entire candidate.
  - One ID from wrong business among otherwise valid IDs: raises ExtractionEvidenceError for entire candidate.
  - All IDs invalid: raises ExtractionEvidenceError.
  - Empty evidence list: raises ExtractionEvidenceError.
  - Verify: invalid ID is never silently filtered; partial evidence is never accepted.
- [x] 7.3 Write unit tests for check_business_consistency:
  - Confirmed order with no items fails.
  - OrderItem with quantity=0 fails.
  - OrderItem with unit_price=None passes (price unknown is valid).
  - Valid Order passes with product + quantity but no price passes.
  - Inquiry with empty summary fails.
  - Valid inputs pass.

---

## 8. Customer Identity Resolution

- [x] 8.1 Create `backend/app/extraction/customer.py` with `resolve_customer(session, target_message) -> int | None`:
  - Queries `WhatsAppIdentity` where `Participant.id == target_message.participant_id`.
  - Returns `customer_id` if found, else `None`.
- [x] 8.2 Write unit tests verifying customer identity matches and None returns.
  - Full chain present and customer_id non-null -> returns customer_id.
  - WhatsAppIdentity.customer_id is null -> returns None.
  - Participant has no whatsapp_identity_id -> returns None.
  - Message has no participant -> returns None.

---

## 9. Derived Record Persistence

- [x] 9.1 Create `backend/app/extraction/persistence.py` with `persist_extraction_results`:
  - Input: session, conversation_id, business_id, customer_id (optional), list of accepted Candidate entities.
  - For each candidate, insert DB model + corresponding ExtractionEvidence records.
  - OrderItem.line_total should be calculated as quantity * unit_price if unit_price is provided, else None.
  - ExtractionEvidence must link every message ID provided in evidence_message_ids to the newly created entity.
- [x] 9.2 Write unit tests verifying atomicity and correct mapping to SQLAlchemy models.
  - Sets conversation_id and business_id.
  - For ExtractedFact: sets model_name and model_version from provider metadata.
  - OrderItem.unit_price is set to None (not zero) when price is unknown.
  - OrderItem.line_total is set to None when unit_price is None; computed when price is known.
- [x] 9.2 Implement uncertainty escalation for candidate types whose status represents
  extraction/review state: if an Inquiry or ExtractedFact has
  confidence < CONFIDENCE_REVIEW_THRESHOLD, set status = 'needs_review'.
  Do NOT override Order.status based on extraction confidence because Order.status
  represents the business state.
- [x] 9.3 Write unit tests for persist_accepted_candidates:
  - Order + OrderItems created together.
  - Order with no items raises ExtractionConsistencyError (not persisted).
  - customer_id applied correctly (null when not resolved).
  - Order.status remains 'confirmed' even when unit_price is None (business state not overridden).
  - Order with unit_price=None and line_total=None is persisted correctly.
  - No Order is persisted with unit_price=0 as a sentinel for unknown price.
  - Inquiry/ExtractedFact status overridden to needs_review when confidence < threshold.
  - Order.status NOT overridden to needs_review by the persistence layer for confidence reasons alone.

---

## 10. Evidence and Provenance

- [x] 10.1 Implement ExtractionEvidence creation inside persist_accepted_candidates:
  - For each derived record, create one ExtractionEvidence row per validated evidence_message_id.
  - Set evidence_text to the relevant portion of the source message content.
  - Enforce the CHECK constraint: exactly one of inquiry_id / order_id / feedback_id /
    extracted_fact_id is non-null per row.
  - The target message_id is NOT automatically added as an evidence row.
  - Only message IDs explicitly in the candidate's evidence_message_ids (and validated) are recorded.
- [x] 10.2 Write unit tests:
  - Multiple evidence rows created for one Order (one per supporting message).
  - Evidence rows link to correct derived record type.
  - Evidence rows reference real message IDs only.
  - Context messages not in evidence_message_ids do NOT get ExtractionEvidence rows.
  - Target message is NOT automatically an ExtractionEvidence row unless cited in evidence_message_ids.

---

## 11. Uncertainty / Review Handling

- [x] 11.1 Apply needs_review status in persistence layer for Inquiry and ExtractedFact when confidence < CONFIDENCE_REVIEW_THRESHOLD.
  - Do NOT apply needs_review to Order.status solely because unit_price is None or confidence is low.
  - Order.status represents business state; extraction uncertainty is provenance, not business state.
  - When unit_price is None, record provenance via ExtractionEvidence.evidence_text noting price was unavailable at extraction time.
  - Do NOT use ExtractionTarget.failure_reason to record successful-extraction provenance; failure_reason is reserved for actual failed attempts.
- [x] 11.2 Write unit tests for needs_review escalation logic:
  - Low-confidence Inquiry -> status overridden to needs_review.
  - Low-confidence ExtractedFact -> status overridden to needs_review.
  - Low-confidence confirmed Order -> Order.status remains 'confirmed'.
  - Confirmed Order with unit_price=None -> Order.status remains 'confirmed'.

---

## 12. Idempotency

- [x] 12.1 Implement ExtractionTarget lookup in ExtractionService.extract():
  - Query ExtractionTarget WHERE message_id = target.id AND business_id = business.id.
  - If status = 'succeeded': skip, return.
  - If status = 'failed': reset to 'pending' for retry.
  - If not found: create with status = 'pending'.
- [x] 12.2 Write unit tests:
  - First extraction with at least one accepted candidate: ExtractionTarget.status = 'succeeded'.
  - All candidates rejected: ExtractionTarget.status = 'failed', not 'succeeded'; no derived records.
  - Second extraction of same message with status='succeeded' is skipped; no new Order/Inquiry/etc. created.
  - Failed ExtractionTarget is retried; extraction runs again.
  - Incremental import: only new (unprocessed) messages are extracted; old ones skipped.
  - ExtractionEvidence rows for a previous extraction do NOT prevent retry of a failed attempt.

---

## 13. Transaction and Failure Handling

- [x] 13.1 Transaction 1: Create/update ExtractionTarget to status='pending'; commit before LLM call.
- [x] 13.2 Transaction 2: Persist all accepted candidates + ExtractionEvidence + update
  ExtractionTarget to status='succeeded' atomically. Full rollback on any DB failure.
- [x] 13.3 On LLM provider error: set ExtractionTarget.status='failed', failure_reason=error; no derived DB writes.
- [x] 13.4 On ExtractionResult Pydantic parse failure: set ExtractionTarget.status='failed'; entire response rejected.
- [x] 13.5 On candidate evidence failure (any invalid evidence_message_id): reject that entire candidate, log; continue with other valid candidates. Do NOT partially accept a candidate by filtering out the invalid IDs.
  On candidate business consistency failure: reject that candidate, log; continue with valid candidates.
  If ALL candidates are rejected: mark ExtractionTarget.status='failed' with reason; no DB writes.
- [x] 13.6 On DB persistence failure: rollback Transaction 2; set ExtractionTarget.status='failed'.
- [x] 13.7 Verify raw Message, Conversation, RelevanceAssessment are not written in any transaction.
- [x] 13.8 Write unit tests:
  - Provider failure -> ExtractionTarget.status='failed'; no derived DB writes.
  - Pydantic parse failure -> ExtractionTarget.status='failed'; no derived DB writes.
  - DB failure -> Transaction 2 rolled back; ExtractionTarget.status='failed'; no partial records.
  - One invalid candidate rejected; valid candidates from same response still persisted.
  - Raw Message unchanged after failed extraction.
  - RelevanceAssessment unchanged after failed extraction.

---

## 14. Pipeline Integration

- [x] 14.1 Identify the correct integration point in the existing pipeline (after RelevanceService writes assessments) — NOT inside IngestionService or RelevanceService directly.
- [x] 14.2 Implement pipeline trigger: after relevance assessment, call ExtractionService.extract() for each newly assessed 'relevant' message.
- [x] 14.3 Ensure extraction failures do not propagate and crash the ingestion/relevance pipeline.
- [x] 14.4 Write integration test: end-to-end ingestion -> relevance -> extraction for a multi-message conversation, verifying derived records and ExtractionTarget.status='succeeded'.

---

## 15. Testing

All tests use FakeLLMProvider. No real Gemini API calls in the normal test suite.

### 15.1 Extraction Target Boundary Tests
- [x] relevant message initiates extraction.
- [x] pending message is skipped (not extracted).
- [x] not_relevant message is skipped (not extracted).
- [x] needs_review message is skipped as a standalone target.
- [x] needs_review message appears in context window for a relevant target.
- [x] needs_review context message alone cannot confirm a derived business fact.

### 15.2 Bounded Context Tests
- [x] Context window bounded to CONTEXT_WINDOW_BEFORE / CONTEXT_WINDOW_AFTER.
- [x] Context messages from same conversation only.
- [x] Context is chronologically ordered.
- [x] pending and not_relevant messages excluded from context.

### 15.3 Multi-Message and Entity Tests
- [x] Multi-message order extraction (multiple supporting messages -> one Order, multiple ExtractionEvidence rows).
- [x] Inquiry extraction (question without purchase -> Inquiry, not Order).
- [x] Tentative intent does not become a confirmed Order.
- [x] Confirmed order with product_name + quantity + commitment but NO price:
  - Order persisted with status='confirmed', unit_price=None, line_total=None.
  - Order NOT rejected merely because price is unknown.
  - Order.status NOT downgraded to 'needs_review' merely because price is unknown.
  - Zero is NOT stored for unknown price or line_total.
- [x] Confirmed commitment present but quantity cannot be established:
  - System does NOT persist a confirmed Order.
  - System does NOT persist a pending Order requiring an OrderItem.
  - System does NOT invent a quantity.
  - Business meaning represented as Inquiry or ExtractedFact since OrderItem cannot be satisfied.
- [x] Confirmed order with all fields present including price.
- [x] Partially supported intent with product + quantity known but commitment unclear -> Order.status='pending'; optional unsupported fields remain null. If required product/quantity cannot be established -> Inquiry or ExtractedFact; no incomplete Order.
- [x] Multiple OrderItems from one extraction.

### 15.4 Validation Tests
- [x] Malformed LLM structured output (fails ExtractionResult parse) -> entire response rejected, no DB write.
- [x] Hallucinated but schema-valid output rejected by evidence ID validation.
- [x] Invalid evidence message IDs (non-existent) -> candidate rejected; valid candidates from same response continue.
- [x] Evidence from wrong conversation -> candidate rejected.
- [x] Evidence from wrong business -> candidate rejected.
- [x] Missing optional fields remain null (not invented, not zeroed).
- [x] All candidates invalid -> no derived records persisted; ExtractionTarget.status='failed'.

### 15.5 Customer Association Tests
- [x] Existing WhatsAppIdentity.customer_id applied to derived record.
- [x] No customer_id -> derived record has customer_id = null.
- [x] LLM output cannot override customer resolution.
- [x] No Customer record created or merged.

### 15.6 Idempotency Tests
- [x] First extraction: ExtractionTarget created and set to 'succeeded'; derived records created.
- [x] Second extraction of same message: ExtractionTarget already 'succeeded'; skipped; no duplicates.
- [x] Failed ExtractionTarget retried: extraction runs again.
- [x] Incremental import: previously succeeded targets skipped; new messages extracted.
- [x] ExtractionEvidence rows alone do NOT determine idempotency (target != evidence).

### 15.7 Failure and Safety Tests
- [x] Provider failure -> ExtractionTarget.status='failed'; no derived DB writes; raw Message unchanged; RelevanceAssessment unchanged.
- [x] DB failure -> Transaction 2 rolled back; ExtractionTarget.status='failed'; no partial records.
- [x] Order without OrderItems not persisted.
- [x] Order + OrderItems + ExtractionEvidence persisted atomically.

### 15.8 Raw-Data Protection Tests
- [x] Raw Message record unchanged after successful extraction.
- [x] Raw Message record unchanged after failed extraction.
- [x] RelevanceAssessment record unchanged after extraction.
- [x] Conversation record unchanged after extraction.

### 15.9 Regression Suite
- [x] Run complete backend test suite: `pytest backend/ -v`

---

## 16. OpenSpec / Final Verification

- [x] 16.1 Run `openspec validate ai-business-extraction` and confirm zero errors.
- [x] 16.2 Run complete backend test suite: `pytest backend/ -v --tb=short`
- [x] 16.3 Confirm no extraction code modifies Message, Conversation, Participant, Media,
  ImportBatch, RelevanceAssessment, or RelevanceAssessmentHistory.
- [x] 16.4 Confirm FakeLLMProvider is used for all automated tests (no real API calls in CI).
- [x] 16.5 Confirm no code uses zero (Decimal('0.00') or 0) as a sentinel for unknown unit_price.
- [x] 16.6 Confirm ExtractionTarget is the idempotency ledger, not ExtractionEvidence.





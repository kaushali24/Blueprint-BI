## Purpose
Provides an AI-driven extraction boundary for converting relevance-eligible WhatsApp conversation
content into validated, structured business information while preserving source traceability,
uncertainty, and raw-data integrity.

---

## ADDED Requirements

---

### Requirement: Extraction Target Boundary

Only messages whose current RelevanceAssessment has relevance_state = 'relevant' SHALL
independently initiate automatic extraction. All other relevance states SHALL NOT
independently initiate extraction.

#### Scenario: Relevant message is eligible as an extraction target
- **WHEN** the current RelevanceAssessment for a message has relevance_state = 'relevant'
- **THEN** the system SHALL treat that message as an eligible extraction target

#### Scenario: pending message does not initiate extraction
- **WHEN** the current RelevanceAssessment for a message has relevance_state = 'pending'
- **THEN** the system SHALL NOT initiate extraction for that message

#### Scenario: not_relevant message does not initiate extraction
- **WHEN** the current RelevanceAssessment for a message has relevance_state = 'not_relevant'
- **THEN** the system SHALL NOT initiate extraction for that message

#### Scenario: needs_review message does not independently initiate extraction
- **WHEN** the current RelevanceAssessment for a message has relevance_state = 'needs_review'
- **THEN** the system SHALL NOT independently initiate extraction for that message
- **AND** SHALL NOT change its relevance_state

#### Scenario: needs_review message may appear as bounded context
- **WHEN** a needs_review message is within the bounded context window of a relevant target
- **THEN** the system MAY include it as a contextual message to aid interpretation
- **AND** the system SHALL NOT treat the needs_review message alone as sufficient evidence
  for confirming a derived business fact
- **AND** the system SHALL preserve the relevance_state of the contextual message unchanged

---

### Requirement: Bounded Conversation Context

The extraction service SHALL gather bounded conversation context to interpret a relevant target
message, because business meaning often emerges across multiple messages.

#### Scenario: Context comes from the same conversation
- **WHEN** gathering context for a relevant target message
- **THEN** the system SHALL only include messages from the same Conversation
- **AND** SHALL NOT include messages from a different conversation or business

#### Scenario: Context is chronologically ordered and deterministically bounded
- **WHEN** assembling the context window for a target message
- **THEN** the system SHALL order messages chronologically by sent_at
- **AND** SHALL apply a deterministic, configurable window (N messages before/after the target)
- **AND** SHALL NOT use semantic retrieval, embeddings, or RAG to select context

#### Scenario: Context excludes ineligible relevance states
- **WHEN** assembling the context window
- **THEN** messages with relevance_state = 'pending' SHALL be excluded from the context window
- **AND** messages with relevance_state = 'not_relevant' SHALL be excluded from the context window
- **AND** messages with relevance_state = 'relevant' or 'needs_review' MAY be included

#### Scenario: Target remains identifiable within the context
- **WHEN** the context window is submitted to the LLM
- **THEN** the target message SHALL be explicitly identified as the extraction target
- **AND** context messages SHALL be clearly distinguished from the target

#### Scenario: Context messages are not automatically treated as evidence
- **WHEN** a message is included in the context window
- **THEN** its inclusion in the context alone SHALL NOT cause it to be recorded as
  an ExtractionEvidence entry

---

### Requirement: Multi-Message Evidence and Traceability

Every persisted derived business record SHALL have at least one supporting ExtractionEvidence
record. Multiple messages may support a single derived record.

Terminology:

  Target message   - The relevant message that initiated the extraction
  Context message  - A nearby message supplied to the LLM to aid interpretation
  Evidence message - A message that directly supports a specific extracted business fact

A context message may also be an evidence message if it directly supports the extracted fact.
Not every context message is automatically an evidence message.
The target message is not automatically an evidence message; it must be explicitly cited.

#### Scenario: Extracted entity is linked to supporting messages
- **WHEN** an Order, Inquiry, Feedback, or ExtractedFact is successfully persisted
- **THEN** the system SHALL create one or more ExtractionEvidence records linking the derived
  record to the Message rows that support it

#### Scenario: Multiple messages support a single derived record
- **WHEN** business meaning is established from multiple messages in the context window
- **THEN** the system SHALL create one ExtractionEvidence row per supporting message
- **AND** each row SHALL reference the same derived record

#### Scenario: Evidence message IDs refer to real messages
- **WHEN** the LLM identifies message IDs as evidence for an extracted entity
- **THEN** the system SHALL verify that every ID exists in the message table
- **AND** every ID belongs to the same Conversation and Business as the extraction target
- **AND** if ANY evidence_message_id fails any of these checks, the system SHALL reject
  the entire candidate entity
- **AND** the system SHALL NOT silently remove the invalid ID and persist the candidate
  using the remaining valid IDs
- **AND** other independently valid candidates from the same ExtractionResult MAY continue

#### Scenario: Distinction between target, context, and evidence is preserved
- **WHEN** recording extraction provenance
- **THEN** the system SHALL record which message was the extraction target
- **AND** which messages were included as context
- **AND** which messages are actual evidence for each derived record
- **AND** the target message SHALL NOT be automatically treated as an evidence message
  merely because it initiated extraction

---

### Requirement: Unknown Attribute Values Remain Unknown

When information cannot be established from the conversation evidence, extracted attributes
SHALL remain null rather than being represented by a sentinel or fabricated value.

#### Scenario: Unknown price remains null
- **WHEN** the conversation does not contain sufficient evidence to determine a price
- **THEN** the system SHALL persist unit_price as NULL
- **AND** SHALL NOT substitute zero, a placeholder, or any invented value

#### Scenario: Unknown optional attributes do not block persistence
- **WHEN** an entity has optional attributes that cannot be established from evidence
- **THEN** those attributes SHALL remain null
- **AND** the entity SHALL still be persisted if required attributes are satisfied
- **AND** the extraction SHALL be flagged for review if optional but important fields are missing

---

### Requirement: Structured-Output Validation Pipeline

LLM structured output SHALL NOT be persisted merely because it is syntactically valid.

The following validation sequence MUST be applied:

  LLM structured output
    -> 1. ExtractionResult Pydantic validation  (if fails: reject entire response, no DB write)
    -> 2. Per-candidate entity validation:
         a. Evidence ID validation              (if fails: reject that candidate, continue others)
         b. Business consistency check          (if fails: reject that candidate, continue others)
         c. Uncertainty/review decision         (determines status of accepted candidate)
    -> 3. Transactional persistence of the accepted candidate set

#### Scenario: ExtractionResult fails Pydantic validation
- **WHEN** the LLM returns output that cannot be parsed as a valid ExtractionResult
- **THEN** the system SHALL NOT persist any derived record from that response
- **AND** SHALL log the failure and mark the extraction attempt as failed or retryable
- **AND** the entire response SHALL be rejected

#### Scenario: Individual candidate fails evidence or consistency validation
- **WHEN** a specific candidate entity fails evidence ID validation or business consistency check
- **THEN** the system SHALL reject that candidate entity
- **AND** SHALL log the rejection reason
- **AND** SHALL continue processing other independently valid candidates from the same response

#### Scenario: Accepted candidate set is persisted atomically
- **WHEN** a set of individually validated candidate entities is ready for persistence
- **THEN** all accepted entities, their child records, and their ExtractionEvidence rows
  SHALL be persisted in a single transaction
- **AND** a DB failure during persistence SHALL roll back the entire accepted set
- **AND** no partial Order, OrderItem, or ExtractionEvidence record SHALL remain

#### Scenario: Unsupported fields remain null
- **WHEN** the LLM cannot determine a value from the available evidence
- **THEN** the corresponding field SHALL remain null
- **AND** the system SHALL NOT invent or guess values not present in the conversation

#### Scenario: Invalid evidence IDs cause candidate rejection
- **WHEN** the LLM provides message IDs that do not exist or are from the wrong conversation
- **THEN** the system SHALL reject the candidate entity with invalid evidence references
- **AND** SHALL NOT persist that candidate

---

### Requirement: Inquiry vs Order vs Tentative Intent

Extraction SHALL NOT convert every commercial discussion into a confirmed order.

#### Scenario: Pure inquiry — no purchase intent
- **WHEN** the conversation contains a request for information with no indication of purchase
- **THEN** the system SHALL extract an Inquiry, NOT an Order
- **AND** the Inquiry.status SHALL be 'open'

#### Scenario: Tentative or uncertain purchase intent
- **WHEN** the conversation contains language expressing potential future intent without commitment
- **THEN** the system SHALL NOT persist a confirmed Order
- **AND** MAY persist an Inquiry or ExtractedFact with an appropriate uncertain status
- **AND** SHALL NOT promote tentative language into a confirmed business event

#### Scenario: Sufficiently supported order — price unknown
- **WHEN** the conversation contains sufficient evidence of:
  (a) an identifiable product or service (product_name supported by evidence), AND
  (b) a quantity > 0 supported by evidence, AND
  (c) an explicit purchase commitment supported by evidence
- **AND** price is not stated in the conversation
- **THEN** the system MAY persist a confirmed Order with OrderItem.unit_price = NULL
  and OrderItem.line_total = NULL
- **AND** Order.status SHALL remain 'confirmed' because the purchase commitment is supported
- **AND** the system SHALL NOT invent a price or a quantity
- **AND** provenance that price was unavailable SHALL be recorded in ExtractionEvidence
  metadata, not in ExtractionTarget.failure_reason

#### Scenario: Quantity cannot be established
- **WHEN** a purchase commitment is supported by evidence
- **AND** quantity cannot be reliably established from the conversation
- **THEN** the system SHALL NOT persist a confirmed Order
- **AND** the system SHALL NOT invent a quantity
- **AND** because OrderItem.quantity is NOT NULL in the database schema,
  no OrderItem SHALL be created with a fabricated or default quantity value
- **AND** the available business meaning SHALL be represented as an Inquiry or
  ExtractedFact as appropriate to the evidence
- **AND** a pending Order without a valid OrderItem is also not permitted under the
  current schema; the evidence should be represented without creating an incomplete Order

#### Scenario: Sufficiently supported order — all information present
- **WHEN** the conversation provides sufficient evidence of an identifiable product,
  explicit purchase commitment, and price
- **THEN** the system MAY persist an Order with status = 'confirmed'
- **AND** the evidence supporting each order item SHALL be traceable to specific messages

#### Scenario: Partially supported order — insufficient commitment evidence
- **WHEN** some but not all required information can be established from the evidence,
  such that a confirmed purchase commitment cannot be established
- **THEN** the system SHALL NOT invent the missing information
- **AND** the system SHALL represent the business state accurately using the available
  evidence: a pending Order MAY be persisted only when the required Order/OrderItem
  structure can still be satisfied, including an identifiable product or service and
  quantity > 0
- **AND** if the required product/service or quantity cannot be established, the system
  SHALL represent the available business meaning as an Inquiry or ExtractedFact rather
  than creating an incomplete Order
- **AND** Order.status SHALL NOT be set to 'needs_review'; extraction uncertainty/provenance
  SHALL be recorded separately and SHALL NOT modify the Order business status

---

### Requirement: Customer Association Boundary

The LLM SHALL NOT perform customer identity resolution.

Customer association SHALL rely exclusively on the existing WhatsAppIdentity -> Customer
relationship already recorded in the database.

#### Scenario: Reliable Customer association exists
- **WHEN** the Participant of the target message has a WhatsAppIdentity with a non-null customer_id
- **THEN** the extraction layer MAY associate derived records with that Customer.id

#### Scenario: No reliable Customer association
- **WHEN** the WhatsAppIdentity has no customer_id, or the participant has no WhatsAppIdentity
- **THEN** the derived record SHALL be persisted with customer_id = null
- **AND** the system SHALL NOT attempt to infer, create, or merge a Customer from the
  conversation content

#### Scenario: LLM-suggested customer identity is ignored
- **WHEN** the LLM output includes or implies a customer identity
- **THEN** the system SHALL NOT use that output to resolve or create a Customer record
- **AND** SHALL derive customer_id solely from the existing database relationship

#### Scenario: LLM does not merge WhatsApp identities
- **THEN** the system SHALL NOT infer that two WhatsAppIdentity records refer to the
  same logical Customer based on LLM interpretation

---

### Requirement: Idempotency and Deduplication

Repeated extraction of the same extraction target SHALL NOT create unintended duplicate
derived business records. The idempotency mechanism SHALL be based on an explicit
processing record for each extraction target, not on ExtractionEvidence rows,
because the target message is not necessarily an evidence message.

#### Scenario: Retrying the same target message
- **WHEN** extraction is retried for a message that was previously processed successfully
  (ExtractionTarget status = 'succeeded')
- **THEN** the system SHALL detect the existing processing record and skip
  rather than creating duplicate derived records

#### Scenario: Failed attempt is retryable
- **WHEN** a previous extraction attempt for a target message failed
  (ExtractionTarget status = 'failed')
- **THEN** the system SHALL permit a retry
- **AND** the retry SHALL NOT create duplicates of any records from the failed attempt

#### Scenario: All candidates rejected — not succeeded
- **WHEN** the LLM response is structurally valid but every candidate entity is rejected
  during candidate-level evidence or business consistency validation
- **THEN** the system SHALL NOT mark the ExtractionTarget as 'succeeded'
- **AND** the system SHALL mark the ExtractionTarget as 'failed'
  with an appropriate failure_reason
- **AND** no derived business records SHALL be persisted for this target

#### Scenario: Reprocessing a conversation
- **WHEN** a full conversation is reprocessed
- **THEN** the system SHALL NOT create new Order, Inquiry, Feedback, or ExtractedFact
  records for targets that were already successfully processed

#### Scenario: Incremental import with mixed messages
- **WHEN** new messages are added to a conversation that was previously processed
- **THEN** extraction SHALL only target messages that have not yet been successfully processed
- **AND** previously extracted derived records SHALL remain unmodified unless
  reprocessing is explicitly triggered

---

### Requirement: Failure and Transaction Safety

Extraction failures MUST NOT corrupt raw WhatsApp data, relevance assessments, or
leave partially-persisted derived records.

#### Scenario: LLM provider failure
- **WHEN** the LLM provider returns an error or is unavailable
- **THEN** the system SHALL NOT write any derived record or evidence
- **AND** SHALL NOT modify any Message, Conversation, or RelevanceAssessment record
- **AND** SHALL record the failure in the extraction target processing record as retryable

#### Scenario: ExtractionResult validation failure
- **WHEN** the LLM response fails top-level Pydantic validation
- **THEN** the system SHALL reject the entire response
- **AND** SHALL NOT partially persist derived records

#### Scenario: Database persistence failure
- **WHEN** a database error occurs during persistence of the accepted candidate set
- **THEN** the transaction SHALL be rolled back
- **AND** no derived entity, OrderItem, or ExtractionEvidence record SHALL be partially committed

#### Scenario: Partially supported order not persisted
- **WHEN** an Order cannot be persisted with at least one valid OrderItem and at least one
  ExtractionEvidence record
- **THEN** the Order SHALL NOT be persisted

---

### Requirement: Raw-Data Protection

The extraction layer SHALL NOT modify or delete any of the following records:
- Message
- Conversation
- Participant
- Media
- ImportBatch / import provenance
- RelevanceAssessment (current or history)

#### Scenario: Post-extraction state
- **WHEN** extraction completes (successfully or with failure)
- **THEN** all raw Message, Conversation, and RelevanceAssessment records
  SHALL remain identical to their pre-extraction state
- **AND** extracted data SHALL be persisted solely in derived tables:
  Order, OrderItem, Inquiry, Feedback, ExtractedFact, ExtractionEvidence,
  and the extraction target processing table
- **AND** the relevance state and evidence status of every contextual message
  SHALL remain unchanged





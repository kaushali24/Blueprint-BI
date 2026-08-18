## Purpose

Provides a controlled boundary that determines whether individual imported
WhatsApp messages are eligible for downstream business extraction while
preserving the complete raw conversation as independent source evidence.

The capability is designed to handle conversations that may contain both
business-related and personal communication, including conversations between
business owners and friends, relatives, neighbours, or other known contacts.

The relevance decision applies primarily at the message level. Conversation
context may be used to understand a message, but the presence of unrelated
messages within a conversation SHALL NOT automatically make the entire
conversation ineligible for business extraction.

## ADDED Requirements

### Requirement: Define Business Relevance

The system SHALL determine whether an individual imported WhatsApp message
contains information that may reasonably contribute to understanding,
operating, or analyzing a business interaction.

Business-relevant communication MAY include:

- product or service inquiries
- pricing or quotation discussions
- order requests or order changes
- product or service availability discussions
- delivery or collection discussions
- appointment or booking discussions
- payment-related business communication
- customer complaints or service issues
- customer feedback
- business-related follow-up communication
- other communication directly related to a business interaction

Personal or unrelated communication SHALL NOT be considered
business-relevant unless the message also contains information directly
relevant to the business interaction.

#### Scenario: Business-related message

- **WHEN** a customer asks about the price or availability of a product or
  service
- **THEN** the message SHALL be eligible to receive the `relevant` state

#### Scenario: Order-related message

- **WHEN** a customer discusses placing, changing, confirming, or cancelling
  an order
- **THEN** the message SHALL be eligible to receive the `relevant` state

#### Scenario: Customer feedback

- **WHEN** a customer provides feedback about a product, service, delivery,
  or business interaction
- **THEN** the message SHALL be eligible to receive the `relevant` state

#### Scenario: Personal message

- **WHEN** a message contains only personal or unrelated communication
- **THEN** the message SHALL be eligible to receive the `not_relevant` state

---

### Requirement: Assess Message Business Relevance

The system SHALL assess individual imported messages for business relevance
after raw ingestion persistence, using available conversation context where
necessary.

#### Scenario: Newly ingested message requires assessment

- **WHEN** a message is persisted by WhatsApp ingestion
- **THEN** the system SHALL create or schedule a relevance assessment for
  that message
- **AND** SHALL preserve the message's association with its conversation
  and business

#### Scenario: Message relevance is determined

- **WHEN** relevance assessment is successfully completed for a message
- **THEN** the system SHALL classify the message into one of the canonical
  relevance states
- **AND** SHALL persist the assessment result for downstream extraction
  control

#### Scenario: Message requires conversation context

- **WHEN** the meaning of a message cannot be reliably determined from the
  message content alone
- **THEN** the relevance assessment SHALL be able to consider available
  messages from the same conversation as contextual evidence
- **AND** SHALL preserve the assessed message as the unit to which the
  relevance decision applies

#### Scenario: Personal message in a business conversation

- **WHEN** a message is personal or unrelated even though surrounding
  messages are business-related
- **THEN** the message SHALL be independently eligible for the
  `not_relevant` state
- **AND** surrounding business-related messages SHALL remain independently
  eligible for relevance assessment

#### Scenario: Business message in a personal conversation

- **WHEN** a message contains a genuine business inquiry or transaction even
  though the conversation also contains personal communication
- **THEN** the message SHALL be eligible for the `relevant` state
- **AND** the existence of unrelated personal messages SHALL NOT
  automatically make the message `not_relevant`

---

### Requirement: Maintain Explicit Message Relevance States

The system SHALL represent each message relevance assessment using explicit
states required for controlled workflow gating.

#### Scenario: Canonical relevance states are used

- **WHEN** a relevance assessment is persisted
- **THEN** the assessment status SHALL be one of:
  `pending`, `relevant`, `not_relevant`, `needs_review`

#### Scenario: Assessment is not yet completed

- **WHEN** a message has not completed relevance evaluation
- **THEN** its relevance status SHALL remain `pending`
- **AND** the message SHALL NOT be implicitly treated as eligible for
  automatic business extraction

#### Scenario: Assessment requires human review

- **WHEN** the system cannot determine message relevance with sufficient
  confidence
- **THEN** the message SHALL be assigned the `needs_review` state
- **AND** SHALL NOT be eligible for automatic business extraction by default

---

### Requirement: Preserve Relevance Decision Traceability

The system SHALL preserve sufficient metadata to understand which source
message was assessed and how the relevance decision was produced.

#### Scenario: Relevance decision is persisted

- **WHEN** a relevance outcome is stored for a message
- **THEN** the system SHALL preserve a reference to the source message
- **AND** SHALL preserve the associated conversation and business context
- **AND** SHALL preserve assessment time
- **AND** SHALL preserve the assessment method or model/version
  information when available
- **AND** SHALL preserve a concise decision explanation or reason suitable
  for human review

#### Scenario: Supporting conversation evidence is used

- **WHEN** additional messages from the same conversation influence a
  relevance decision
- **THEN** the system SHALL preserve sufficient references or metadata to
  identify the contextual evidence used for the decision

#### Scenario: Assessment method is unavailable

- **WHEN** an assessment is produced without model or method metadata
- **THEN** the system SHALL still preserve the relevance result and source
  message reference
- **AND** SHALL not modify the original raw message

---

### Requirement: Reassess Messages After Incremental Updates

The system SHALL support reassessment when newly imported messages can change
the relevance interpretation of an existing message or provide additional
context.

#### Scenario: Existing conversation receives new messages

- **WHEN** an incremental import adds new messages to an existing
  conversation
- **THEN** the system SHALL assess the newly imported messages for relevance
- **AND** SHALL support reassessing previously assessed messages when the
  newly available context can affect their relevance interpretation

#### Scenario: Reassessment changes a previous outcome

- **WHEN** reassessment produces a different relevance outcome for an
  existing message
- **THEN** the system SHALL update or supersede the previous relevance
  assessment according to the selected persistence strategy
- **AND** SHALL preserve the source message and its original import
  provenance

#### Scenario: Reassessment is unnecessary

- **WHEN** newly imported information cannot affect the relevance
  interpretation of an existing message
- **THEN** the system MAY retain the existing relevance outcome unchanged

---

### Requirement: Enforce Message-Level Extraction Eligibility

The system SHALL provide a default boundary so downstream business
extraction operates only on messages explicitly approved as relevant.

#### Scenario: Message is relevant

- **WHEN** a message is classified as `relevant`
- **THEN** the message SHALL be eligible for downstream business extraction
  workflows

#### Scenario: Message is not relevant

- **WHEN** a message is classified as `not_relevant`
- **THEN** the message SHALL be excluded from default business extraction
  eligibility

#### Scenario: Message requires review

- **WHEN** a message is classified as `needs_review`
- **THEN** the message SHALL be excluded from default business extraction
  eligibility
- **AND** the review requirement SHALL remain observable

#### Scenario: Message assessment is pending

- **WHEN** a message has a `pending` relevance assessment
- **THEN** the message SHALL be excluded from default business extraction
  eligibility

#### Scenario: Mixed conversation contains relevant and irrelevant messages

- **WHEN** a conversation contains messages classified as both `relevant`
  and `not_relevant`
- **THEN** the relevant messages SHALL remain eligible for downstream
  extraction
- **AND** the not-relevant messages SHALL remain excluded by default
- **AND** the conversation SHALL NOT be rejected solely because it contains
  irrelevant messages

#### Scenario: Conversation contains only non-relevant messages

- **WHEN** all assessed messages in a conversation are `not_relevant`
- **THEN** the conversation SHALL contain no messages eligible for default
  downstream business extraction
- **AND** the raw conversation SHALL remain preserved in the database

---

### Requirement: Keep Relevance Detection Independent From Extraction and Analytics

The relevance-detection capability SHALL only determine message-level
business relevance and extraction eligibility and SHALL NOT perform business
entity extraction or analytics.

#### Scenario: Relevance assessment runs successfully

- **WHEN** the relevance assessment process executes
- **THEN** the system SHALL NOT create or modify business entities such as
  orders, customers, products, or other extracted business facts as part of
  this capability
- **AND** SHALL NOT produce business analytics outputs as part of relevance
  assessment

#### Scenario: Downstream extraction is unavailable

- **WHEN** downstream business extraction systems are unavailable
- **THEN** relevance assessment SHALL remain independently processable
- **AND** relevance assessment SHALL NOT depend on downstream extraction
  completing successfully

#### Scenario: Advanced AI systems are unavailable

- **WHEN** RAG, embeddings, vector databases, LangGraph, or LangChain
  workflows are unavailable
- **THEN** the relevance-detection capability SHALL NOT fail solely because
  those systems are unavailable

---

### Requirement: Preserve Raw Conversation Evidence Independently

The system SHALL preserve raw imported messages and conversation source data
independently from relevance assessment results.

#### Scenario: Relevance decision is created

- **WHEN** a relevance assessment is created for a message
- **THEN** the original raw message SHALL remain unchanged
- **AND** the message's original import provenance SHALL remain unchanged

#### Scenario: Relevance decision is updated

- **WHEN** a relevance assessment changes due to reassessment or review
- **THEN** the raw message and conversation source data SHALL remain
  unchanged as source evidence

#### Scenario: Relevance assessment fails

- **WHEN** relevance processing fails for a message
- **THEN** the failure SHALL NOT delete or corrupt the existing raw message
  or conversation data
- **AND** the failed assessment SHALL remain observable for retry or review

---

### Requirement: Preserve Business Data Isolation

The system SHALL ensure relevance assessments remain associated with the
business that owns the source conversation.

#### Scenario: Message belongs to a business

- **WHEN** a relevance assessment is created or retrieved
- **THEN** the assessment SHALL remain associated with the business context
  of its source conversation
- **AND** the assessment SHALL NOT expose or associate the message with
  another business

#### Scenario: Same WhatsApp identity exists for different businesses

- **WHEN** the same WhatsApp identity appears in conversations belonging to
  different businesses
- **THEN** relevance assessments SHALL remain isolated within their
  respective business and conversation contexts

---

### Requirement: Preserve Assessment State and Review Information

The system SHALL preserve sufficient state information to support automated
processing, reassessment, and human review.

#### Scenario: Assessment is pending

- **WHEN** a relevance assessment is created but processing has not completed
- **THEN** the system SHALL preserve the `pending` state
- **AND** SHALL make the message identifiable for subsequent processing

#### Scenario: Assessment requires review

- **WHEN** an assessment is assigned `needs_review`
- **THEN** the system SHALL preserve the reason or review information
  available for the assessment
- **AND** SHALL allow the message to be identified for human review

#### Scenario: Human review changes the outcome

- **WHEN** an authorized review process changes a relevance outcome
- **THEN** the system SHALL preserve the updated relevance state
- **AND** SHALL preserve the underlying raw message and import provenance

---

### Requirement: Support Relevance Assessment Failure and Retry

The system SHALL allow failed relevance assessments to be identified and
processed again without affecting raw conversation data.

#### Scenario: Relevance assessment fails

- **WHEN** relevance processing cannot complete for a message
- **THEN** the system SHALL preserve the raw message
- **AND** SHALL record that relevance assessment processing failed or
  requires retry
- **AND** SHALL prevent the message from becoming automatically eligible
  for downstream business extraction

#### Scenario: Failed assessment is retried

- **WHEN** a failed relevance assessment is retried
- **THEN** the system SHALL process the message again using the available
  relevance assessment mechanism
- **AND** SHALL update the relevance state according to the resulting
  assessment

---

### Requirement: Preserve Relevance Assessment History

The system SHALL preserve sufficient information to determine the current
relevance state and, where required by the selected persistence strategy,
the history of previous relevance decisions.

#### Scenario: Relevance outcome changes

- **WHEN** a message changes from one relevance state to another
- **THEN** the system SHALL preserve the current state
- **AND** SHALL preserve sufficient metadata to identify that the outcome
  was reassessed or changed

#### Scenario: Raw message is re-imported

- **WHEN** an already imported message appears in a later WhatsApp export
- **THEN** the existing raw message identity and provenance SHALL remain
  intact
- **AND** the relevance assessment SHALL NOT be duplicated unnecessarily
  unless a reassessment is required
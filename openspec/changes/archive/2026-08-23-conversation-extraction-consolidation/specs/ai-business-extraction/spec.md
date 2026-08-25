## MODIFIED Requirements

### Requirement: Extraction Target Boundary
The system SHALL operate extraction on a business episode boundary rather than independently extracting every single relevant message. A business episode represents a continuous sequence of business interaction.

#### Scenario: Relevant message initiates an episode
- **WHEN** the system encounters a message with relevance_state = 'relevant' that does not belong to an open episode
- **THEN** the system SHALL treat that message as the start of a new business episode extraction target

#### Scenario: Needs_review messages participate contextually
- **WHEN** a message with relevance_state = 'needs_review' falls within the time bounds of an active episode
- **THEN** the system SHALL include it in the episode context
- **AND** the system SHALL NOT independently initiate a new episode for a 'needs_review' message

#### Scenario: Excluded relevance states
- **WHEN** assembling the episode context
- **THEN** messages with relevance_state = 'pending' or 'not_relevant' SHALL be excluded from the context
- **AND** they SHALL NOT be used as evidence

#### Scenario: Business Episode time boundary
- **WHEN** sequential relevant or needs_review messages are separated by a time gap exceeding a deterministic threshold (e.g., 7 days of inactivity)
- **THEN** the system SHALL close the current episode at the message preceding the gap
- **AND** the subsequent relevant message SHALL start a new, distinct business episode


### Requirement: Derived-Entity Ownership and Traceability
The persistence layer MUST know exactly which derived business records belong to which extraction episode.

#### Scenario: Explicit ownership of derived records
- **WHEN** an episode extraction succeeds
- **THEN** all resulting Order, Inquiry, Feedback, and ExtractedFact records SHALL be explicitly linked to the owning ExtractionTarget via an extraction_target_id Foreign Key
- **AND** the system SHALL NOT rely on fuzzy matching, product names, or customer names to determine episode ownership


### Requirement: Re-extraction and Atomic Replacement
When an episode expands due to incremental messages, the system SHALL safely and atomically update the derived state without leaving duplicates.

#### Scenario: Safe atomic replacement of an expanded episode
- **WHEN** a previously succeeded episode is re-extracted because new messages extended its boundary
- **AND** the new LLM extraction succeeds
- **THEN** the system SHALL atomically DELETE the prior derived records (Order, Inquiry, etc.) owned by this episode's ExtractionTarget ID
- **AND** the system SHALL INSERT the newly generated records
- **AND** the target status SHALL be marked as 'succeeded'

#### Scenario: Provider failure during re-extraction
- **WHEN** an episode is being re-extracted
- **AND** the LLM provider fails, returns an invalid schema, or the database transaction fails
- **THEN** the previously successful derived records and evidence for that episode SHALL NOT be deleted
- **AND** the target SHALL revert to a safe failure or pending state without destroying prior valid state


### Requirement: Idempotency and Deduplication
Repeated extraction of the same unchanged episode SHALL NOT create unintended duplicate derived business records.

#### Scenario: Retrying the same unchanged episode
- **WHEN** extraction is triggered for an episode that was previously processed successfully and whose end boundary has not changed
- **THEN** the system SHALL detect the existing processing record and skip


## ADDED Requirements

### Requirement: Order Evolution and Consolidation
The system SHALL support the refinement of business records as new evidence emerges in the episode, ensuring that evolving states are consolidated rather than producing distinct fragmented objects.

#### Scenario: Inquiry becomes confirmed Order
- **WHEN** an initial segment establishes an Inquiry
- **AND** a later segment in the same episode confirms the purchase commitment
- **THEN** the re-extraction atomic replacement SHALL result in a single confirmed Order
- **AND** the previous Inquiry SHALL be safely removed because it was owned by the same episode

#### Scenario: Add-ons are cancelled
- **WHEN** a conversation establishes an item (e.g. cupcakes) and a later message cancels it within the same episode
- **THEN** the final consolidated Order SHALL NOT include the cancelled item in its OrderItems
- **AND** the cancellation evidence MAY be preserved as contextual provenance for the final Order

#### Scenario: Multiple genuine orders in one conversation
- **WHEN** a conversation contains an Order completed in July
- **AND** an unrelated Order begins in August (exceeding the 7-day inactivity boundary)
- **THEN** the system SHALL create two distinct business episodes
- **AND** two distinct Orders SHALL be persisted natively

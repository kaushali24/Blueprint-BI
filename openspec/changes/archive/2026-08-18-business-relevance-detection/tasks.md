# Tasks: Business Relevance Detection

## 1. Relevance Data Foundation

- [x] 1.1 Define the relevance assessment persistence model
- [x] 1.2 Add the canonical relevance states: `pending`, `relevant`, `not_relevant`, and `needs_review`
- [x] 1.3 Add source-message and business ownership references
- [x] 1.4 Add conversation reference for relevance context and traceability
- [x] 1.5 Add assessment timestamp, method/version, and rationale metadata
- [x] 1.6 Define assessment version/history handling for reassessment
- [x] 1.7 Add required database indexes and constraints
- [x] 1.8 Ensure relevance persistence is separate from raw message data

## 2. Relevance Assessment

- [x] 2.1 Create the message-level relevance assessment service
- [x] 2.2 Implement the `relevant` classification outcome
- [x] 2.3 Implement the `not_relevant` classification outcome
- [x] 2.4 Implement the `needs_review` outcome for uncertain cases
- [x] 2.5 Preserve the `pending` state for unassessed messages
- [x] 2.6 Allow available conversation context to be provided to the assessment process
- [x] 2.7 Ensure the assessment applies to the target message even when conversation context is used
- [x] 2.8 Keep assessment logic independent from business entity extraction
- [x] 2.9 Keep the classification mechanism replaceable without changing the relevance data contract

## 3. Traceability and Raw Data Protection

- [x] 3.1 Persist the source-message reference for every relevance assessment
- [x] 3.2 Persist the associated conversation and business context
- [x] 3.3 Preserve assessment provenance and method/version metadata
- [x] 3.4 Preserve decision rationale where available
- [x] 3.5 Preserve references or metadata for contextual messages used during assessment
- [x] 3.6 Preserve raw message records during relevance assessment
- [x] 3.7 Preserve original import provenance
- [x] 3.8 Enforce business ownership isolation
- [x] 3.9 Verify relevance updates do not modify raw evidence

## 4. Extraction Eligibility Boundary

- [x] 4.1 Define the extraction eligibility rule based on the current relevance state
- [x] 4.2 Implement a controlled data-access/service boundary for retrieving extraction-eligible messages
- [x] 4.3 Allow only `relevant` messages to become eligible by default
- [x] 4.4 Exclude `pending` messages from default extraction eligibility
- [x] 4.5 Exclude `not_relevant` messages from default extraction eligibility
- [x] 4.6 Exclude `needs_review` messages from default extraction eligibility
- [x] 4.7 Ensure eligibility is evaluated within the correct business scope
- [x] 4.8 Prevent downstream extraction from bypassing the relevance boundary
- [x] 4.9 Verify mixed conversations allow relevant messages while excluding unrelated messages

## 5. Reassessment and Assessment History

- [x] 5.1 Detect newly imported messages requiring relevance assessment
- [x] 5.2 Identify existing messages that may require reassessment when new conversation context becomes available
- [x] 5.3 Support reassessment of previously assessed messages
- [x] 5.4 Preserve the original raw message and import provenance during reassessment
- [x] 5.5 Implement the selected assessment update/versioning strategy
- [x] 5.6 Preserve previous assessment information where required for traceability
- [x] 5.7 Ensure the current assessment determines extraction eligibility
- [x] 5.8 Avoid unnecessary reassessment when newly imported information cannot affect the existing decision

## 6. Ingestion Integration

- [x] 6.1 Integrate relevance assessment after successful WhatsApp ingestion persistence
- [x] 6.2 Ensure newly imported messages enter the relevance workflow
- [x] 6.3 Ensure existing conversations can trigger reassessment when appropriate
- [x] 6.4 Keep WhatsApp ingestion responsibilities separate from relevance assessment responsibilities
- [x] 6.5 Ensure ingestion does not contain business relevance classification logic
- [x] 6.6 Verify relevance processing failure does not corrupt or remove imported raw messages

## 7. Existing Data and Migration

- [x] 7.1 Define handling of existing imported messages using the approved migration strategy
- [x] 7.2 Initialize unassessed existing messages as `pending` where applicable
- [x] 7.3 Ensure existing unassessed messages are not automatically extraction-eligible
- [x] 7.4 Verify existing database records remain valid after relevance schema changes
- [x] 7.5 Verify existing WhatsApp ingestion continues to function after the schema change

## 8. Failure Handling and Recovery

- [x] 8.1 Handle relevance assessment failures without modifying raw messages
- [x] 8.2 Keep failed assessments observable for retry or review
- [x] 8.3 Verify assessment failures do not make messages automatically extraction-eligible
- [x] 8.4 Support retrying failed relevance assessments
- [x] 8.5 Verify partial relevance processing does not corrupt successfully assessed messages

## 9. Testing

- [x] 9.1 Test relevance state persistence
- [x] 9.2 Test message-level relevance assessment
- [x] 9.3 Test mixed personal/business conversations
- [x] 9.4 Test conversation-context-assisted assessment
- [x] 9.5 Test `pending` behavior
- [x] 9.6 Test `relevant` behavior
- [x] 9.7 Test `not_relevant` behavior
- [x] 9.8 Test `needs_review` behavior
- [x] 9.9 Test source-message traceability
- [x] 9.10 Test contextual evidence traceability
- [x] 9.11 Test business isolation
- [x] 9.12 Test raw message preservation
- [x] 9.13 Test original import provenance preservation
- [x] 9.14 Test extraction eligibility
- [x] 9.15 Test mixed-conversation extraction eligibility
- [x] 9.16 Test incremental reassessment
- [x] 9.17 Test assessment version/history behavior
- [x] 9.18 Test assessment provenance
- [x] 9.19 Test failure handling and retry/review behavior
- [x] 9.20 Test existing-message migration behavior
- [x] 9.21 Test that the relevance layer does not create business entities
- [x] 9.22 Test that the relevance layer does not depend on RAG, embeddings, or vector databases
- [x] 9.23 Test that the relevance persistence and eligibility boundary remain independent of the specific AI provider

## 10. Specification and Integration Verification

- [x] 10.1 Verify implementation satisfies all requirements and scenarios in `business-relevance-detection/spec.md`
- [x] 10.2 Verify implementation matches the approved `design.md`
- [x] 10.3 Verify raw WhatsApp evidence remains independent from derived relevance data
- [x] 10.4 Verify downstream extraction cannot automatically consume `pending`, `not_relevant`, or `needs_review` messages
- [x] 10.5 Verify only `relevant` messages are extraction-eligible by default
- [x] 10.6 Verify business-level data isolation
- [x] 10.7 Verify existing database and ingestion functionality remains operational
- [x] 10.8 Run the complete backend test suite
- [x] 10.9 Run `openspec validate business-relevance-detection`

## 11. Rollback Verification

- [x] 11.1 Verify relevance processing can be disabled without disabling raw WhatsApp ingestion
- [x] 11.2 Verify raw WhatsApp messages remain intact when relevance processing is disabled
- [x] 11.3 Verify unassessed messages remain ineligible for automatic extraction during rollback
- [x] 11.4 Verify rollback does not require deletion or modification of raw WhatsApp evidence
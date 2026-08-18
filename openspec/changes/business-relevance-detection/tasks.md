# Tasks: Business Relevance Detection

## 1. Relevance Data Foundation

- [ ] 1.1 Define the relevance assessment persistence model
- [ ] 1.2 Add the canonical relevance states: `pending`, `relevant`, `not_relevant`, and `needs_review`
- [ ] 1.3 Add source-message and business ownership references
- [ ] 1.4 Add conversation reference for relevance context and traceability
- [ ] 1.5 Add assessment timestamp, method/version, and rationale metadata
- [ ] 1.6 Define assessment version/history handling for reassessment
- [ ] 1.7 Add required database indexes and constraints
- [ ] 1.8 Ensure relevance persistence is separate from raw message data

## 2. Relevance Assessment

- [ ] 2.1 Create the message-level relevance assessment service
- [ ] 2.2 Implement the `relevant` classification outcome
- [ ] 2.3 Implement the `not_relevant` classification outcome
- [ ] 2.4 Implement the `needs_review` outcome for uncertain cases
- [ ] 2.5 Preserve the `pending` state for unassessed messages
- [ ] 2.6 Allow available conversation context to be provided to the assessment process
- [ ] 2.7 Ensure the assessment applies to the target message even when conversation context is used
- [ ] 2.8 Keep assessment logic independent from business entity extraction
- [ ] 2.9 Keep the classification mechanism replaceable without changing the relevance data contract

## 3. Traceability and Raw Data Protection

- [ ] 3.1 Persist the source-message reference for every relevance assessment
- [ ] 3.2 Persist the associated conversation and business context
- [ ] 3.3 Preserve assessment provenance and method/version metadata
- [ ] 3.4 Preserve decision rationale where available
- [ ] 3.5 Preserve references or metadata for contextual messages used during assessment
- [ ] 3.6 Preserve raw message records during relevance assessment
- [ ] 3.7 Preserve original import provenance
- [ ] 3.8 Enforce business ownership isolation
- [ ] 3.9 Verify relevance updates do not modify raw evidence

## 4. Extraction Eligibility Boundary

- [ ] 4.1 Define the extraction eligibility rule based on the current relevance state
- [ ] 4.2 Implement a controlled data-access/service boundary for retrieving extraction-eligible messages
- [ ] 4.3 Allow only `relevant` messages to become eligible by default
- [ ] 4.4 Exclude `pending` messages from default extraction eligibility
- [ ] 4.5 Exclude `not_relevant` messages from default extraction eligibility
- [ ] 4.6 Exclude `needs_review` messages from default extraction eligibility
- [ ] 4.7 Ensure eligibility is evaluated within the correct business scope
- [ ] 4.8 Prevent downstream extraction from bypassing the relevance boundary
- [ ] 4.9 Verify mixed conversations allow relevant messages while excluding unrelated messages

## 5. Reassessment and Assessment History

- [ ] 5.1 Detect newly imported messages requiring relevance assessment
- [ ] 5.2 Identify existing messages that may require reassessment when new conversation context becomes available
- [ ] 5.3 Support reassessment of previously assessed messages
- [ ] 5.4 Preserve the original raw message and import provenance during reassessment
- [ ] 5.5 Implement the selected assessment update/versioning strategy
- [ ] 5.6 Preserve previous assessment information where required for traceability
- [ ] 5.7 Ensure the current assessment determines extraction eligibility
- [ ] 5.8 Avoid unnecessary reassessment when newly imported information cannot affect the existing decision

## 6. Ingestion Integration

- [ ] 6.1 Integrate relevance assessment after successful WhatsApp ingestion persistence
- [ ] 6.2 Ensure newly imported messages enter the relevance workflow
- [ ] 6.3 Ensure existing conversations can trigger reassessment when appropriate
- [ ] 6.4 Keep WhatsApp ingestion responsibilities separate from relevance assessment responsibilities
- [ ] 6.5 Ensure ingestion does not contain business relevance classification logic
- [ ] 6.6 Verify relevance processing failure does not corrupt or remove imported raw messages

## 7. Existing Data and Migration

- [ ] 7.1 Define handling of existing imported messages using the approved migration strategy
- [ ] 7.2 Initialize unassessed existing messages as `pending` where applicable
- [ ] 7.3 Ensure existing unassessed messages are not automatically extraction-eligible
- [ ] 7.4 Verify existing database records remain valid after relevance schema changes
- [ ] 7.5 Verify existing WhatsApp ingestion continues to function after the schema change

## 8. Failure Handling and Recovery

- [ ] 8.1 Handle relevance assessment failures without modifying raw messages
- [ ] 8.2 Keep failed assessments observable for retry or review
- [ ] 8.3 Verify assessment failures do not make messages automatically extraction-eligible
- [ ] 8.4 Support retrying failed relevance assessments
- [ ] 8.5 Verify partial relevance processing does not corrupt successfully assessed messages

## 9. Testing

- [ ] 9.1 Test relevance state persistence
- [ ] 9.2 Test message-level relevance assessment
- [ ] 9.3 Test mixed personal/business conversations
- [ ] 9.4 Test conversation-context-assisted assessment
- [ ] 9.5 Test `pending` behavior
- [ ] 9.6 Test `relevant` behavior
- [ ] 9.7 Test `not_relevant` behavior
- [ ] 9.8 Test `needs_review` behavior
- [ ] 9.9 Test source-message traceability
- [ ] 9.10 Test contextual evidence traceability
- [ ] 9.11 Test business isolation
- [ ] 9.12 Test raw message preservation
- [ ] 9.13 Test original import provenance preservation
- [ ] 9.14 Test extraction eligibility
- [ ] 9.15 Test mixed-conversation extraction eligibility
- [ ] 9.16 Test incremental reassessment
- [ ] 9.17 Test assessment version/history behavior
- [ ] 9.18 Test assessment provenance
- [ ] 9.19 Test failure handling and retry/review behavior
- [ ] 9.20 Test existing-message migration behavior
- [ ] 9.21 Test that the relevance layer does not create business entities
- [ ] 9.22 Test that the relevance layer does not depend on RAG, embeddings, or vector databases
- [ ] 9.23 Test that the relevance persistence and eligibility boundary remain independent of the specific AI provider

## 10. Specification and Integration Verification

- [ ] 10.1 Verify implementation satisfies all requirements and scenarios in `business-relevance-detection/spec.md`
- [ ] 10.2 Verify implementation matches the approved `design.md`
- [ ] 10.3 Verify raw WhatsApp evidence remains independent from derived relevance data
- [ ] 10.4 Verify downstream extraction cannot automatically consume `pending`, `not_relevant`, or `needs_review` messages
- [ ] 10.5 Verify only `relevant` messages are extraction-eligible by default
- [ ] 10.6 Verify business-level data isolation
- [ ] 10.7 Verify existing database and ingestion functionality remains operational
- [ ] 10.8 Run the complete backend test suite
- [ ] 10.9 Run `openspec validate business-relevance-detection`

## 11. Rollback Verification

- [ ] 11.1 Verify relevance processing can be disabled without disabling raw WhatsApp ingestion
- [ ] 11.2 Verify raw WhatsApp messages remain intact when relevance processing is disabled
- [ ] 11.3 Verify unassessed messages remain ineligible for automatic extraction during rollback
- [ ] 11.4 Verify rollback does not require deletion or modification of raw WhatsApp evidence
## Context

The `whatsapp-ingestion` capability now provides validated and normalized WhatsApp conversation data while preserving raw messages and their source provenance.

The `business-data-foundation` capability provides the persistent data foundation required to store business-related information separately from raw imported conversation data.

See `proposal.md` for the motivation and scope of this change.

The relevance-detection stage will sit between WhatsApp ingestion and future business extraction:

```text
WhatsApp ZIP Import
        ↓
Raw Message Persistence
        ↓
Business Relevance Detection
        ↓
Extraction Eligibility
        ↓
Future Business Entity Extraction
```

The important architectural constraint is that relevance detection must not modify or reinterpret the raw WhatsApp evidence. Its output is an additional assessment associated with persisted messages.

The MVP also needs to handle mixed conversations. A single WhatsApp conversation may contain both personal and business messages. Therefore, relevance must be assessed at message level rather than treating the entire conversation as either business or personal.

## Goals / Non-Goals

Goals:

- Establish a clear boundary between raw imported messages and downstream business extraction.
- Assess business relevance at message level.
- Preserve raw messages independently from relevance assessments.
- Persist relevance decisions with source-message traceability.
- Support the states `pending`, `relevant`, `not_relevant`, and `needs_review`.
- Make only relevant messages eligible for automatic downstream extraction by default.
- Support reassessment when new messages are imported into an existing conversation.
- Preserve previous raw data and provenance when relevance decisions change.
- Keep the relevance layer independently testable.
- Allow future replacement or enhancement of the classification mechanism without changing the raw ingestion model.

Non-Goals:

- Extracting orders, customers, products, prices, or other business entities.
- Performing sentiment analysis.
- Generating analytics or dashboards.
- Implementing RAG.
- Generating embeddings.
- Introducing a vector database.
- Implementing the LangGraph/LangChain business assistant.
- Integrating directly with the WhatsApp API.
- Automatically merging WhatsApp identities.
- Modifying or deleting raw imported messages based on relevance decisions.

## Decisions

### 1. Use message-level relevance assessment

Relevance will be represented against individual imported messages rather than only against conversations.

This is necessary because a conversation can contain both business and personal communication.

For example:

- Message 1: "Hi, how are you?"
- Message 2: "Can I order a chocolate cake for Saturday?"
- Message 3: "Sure, what size would you like?"
- Message 4: "By the way, are you coming to the party?"

The same conversation may therefore contain:

- Message 1 -> `not_relevant`
- Message 2 -> `relevant`
- Message 3 -> `relevant`
- Message 4 -> `not_relevant`

The conversation itself remains intact.

Alternative considered: Conversation-level classification.

This was rejected because classifying an entire conversation as business or personal would incorrectly include unrelated messages when a conversation contains mixed communication.

### 2. Store relevance assessments separately from raw messages

Raw WhatsApp messages will remain immutable source evidence.

Relevance assessment data will be stored separately and will reference the corresponding source message.

Conceptually:

```text
RawMessage
    |
    | 1-to-many / versioned assessment relationship
    ↓
RelevanceAssessment
```

A relevance assessment should contain enough information to identify:

- the source message
- the business context
- the resulting relevance state
- when the decision was made
- the assessment method/version
- the decision rationale where available

The exact database implementation should follow the existing SQLAlchemy database foundation.

Alternative considered: Add a `relevance_status` column directly to the raw message table.

This was rejected because it mixes source evidence with derived information and makes reassessment/versioning harder to audit.

### 3. Use explicit canonical relevance states

The system will use exactly four canonical states:

- `pending`
- `relevant`
- `not_relevant`
- `needs_review`

`pending` represents a message that has not yet completed relevance assessment.

`relevant` means the message is approved for downstream automatic business extraction.

`not_relevant` means the message is considered unrelated to business activity.

`needs_review` means the system cannot safely determine relevance and the message requires review before automatic extraction.

No state other than `relevant` will be extraction-eligible by default.

Alternative considered: Use a boolean such as `is_business_related`.

This was rejected because a boolean cannot represent uncertainty or an assessment that has not yet been completed.

### 4. Treat relevance as a derived assessment, not source truth

The raw WhatsApp message remains the source of truth for what was actually imported.

The relevance result is an interpretation of that source data.

Therefore:

- Raw message = source evidence
- Relevance assessment = derived interpretation

Updating a relevance assessment MUST NOT update, delete, or rewrite the underlying raw message.

This maintains provenance and allows reassessment if classification rules change.

### 5. Preserve assessment provenance

Each relevance assessment will retain sufficient metadata to explain the origin of the decision.

At minimum, the design will support:

- source message reference
- assessment timestamp
- assessment state
- assessment method/version
- decision rationale where available

If a decision is based on particular message evidence, those source-message references should also be preserved.

This allows a future reviewer to understand why a message was considered business-relevant without relying only on the current classification result.

### 6. Support reassessment without replacing raw evidence

When new messages are imported into an existing conversation, the relevance assessment process must be able to reassess affected messages.

The system should not rewrite historical raw messages to perform this reassessment.

Instead, the derived relevance assessment may be updated or superseded according to the persistence model selected during implementation.

Conceptually:

```text
Raw Message
    ↓
Assessment v1
    ↓
Assessment v2
```

The important requirement is that the raw message remains unchanged.

Alternative considered: Permanently overwrite the original relevance decision with no assessment history.

This was rejected because it reduces auditability and makes it difficult to understand how a decision changed over time.

### 7. Establish extraction eligibility through a dedicated boundary

Downstream business extraction must not query raw messages and assume that all imported messages are business-relevant.

Instead, extraction eligibility will be derived from the relevance state.

Default rule:

- `relevant` -> eligible
- `pending` -> not eligible
- `not_relevant` -> not eligible
- `needs_review` -> not eligible

This creates an explicit safety boundary before business entity extraction.

Future extraction functionality can therefore consume only eligible messages.

### 8. Keep relevance detection independent from business extraction

The relevance layer will only determine whether messages are relevant for business processing.

It will not create structured business entities such as:

- orders
- customers
- products
- prices
- delivery information
- sentiment
- analytics metrics

Those responsibilities belong to later capabilities.

This separation allows the relevance system to be developed and tested independently from the future extraction pipeline.

### 9. Keep AI implementation replaceable

The specification defines the observable relevance behavior rather than binding the capability to a particular AI provider or framework.

The implementation may initially use deterministic rules, an AI classifier, or a hybrid approach if required by the approved implementation plan.

However, the persistence model and extraction eligibility contract must remain independent of the specific classification mechanism.

This avoids coupling the foundation to Gemini, LangChain, LangGraph, RAG, embeddings, or vector databases unnecessarily.

### 10. Handle uncertainty explicitly

When relevance cannot be determined with sufficient confidence, the system will use `needs_review` rather than silently classifying the message as relevant.

This is important because false-positive business messages can introduce incorrect information into downstream business intelligence.

The system therefore follows a conservative default:

`uncertain -> needs_review -> not automatically extracted`

### 11. Preserve business isolation

Relevance assessments must remain associated with the correct business context.

A relevance result belonging to one business must not make a message from another business extraction-eligible.

The implementation must therefore use the same business ownership boundaries established by the existing data foundation and WhatsApp ingestion model.

### 12. Integrate with ingestion without coupling responsibilities

WhatsApp ingestion and relevance detection remain separate capabilities.

The integration point is:

```text
Ingestion completes
        ↓
Messages are persisted
        ↓
Relevance assessment becomes available
```

The ingestion layer is responsible for importing and preserving raw data.

The relevance layer is responsible for assessing that persisted data.

The ingestion implementation must not contain business extraction logic or classification-specific rules.

Alternative considered: Perform relevance detection directly inside the WhatsApp parser/importer.

This was rejected because it would tightly couple raw ingestion with derived business interpretation and make independent testing and future reassessment more difficult.

## Risks / Trade-offs

- [Risk] Personal messages may be incorrectly classified as relevant.
  Mitigation: Use conservative classification behavior and the `needs_review` state. Messages that are uncertain must not become automatically extraction eligible.

- [Risk] Genuine business messages may be incorrectly classified as not relevant.
  Mitigation: Preserve the original raw messages and allow reassessment. The relevance layer must never delete source evidence.

- [Risk] Relevance decisions may change when new messages arrive.
  Mitigation: Support reassessment while preserving the raw message and assessment provenance.

- [Risk] Classification logic may evolve during the MVP.
  Mitigation: Store assessment method/version metadata so that future assessments can be distinguished from previous ones.

- [Risk] Mixed conversations may produce inconsistent conversation-level interpretation.
  Mitigation: Use message-level relevance as the primary extraction eligibility boundary instead of classifying an entire conversation as business or personal.

- [Risk] Relevance data could become coupled to a specific AI provider.
  Mitigation: Keep the specification and persistence model independent from Gemini, LangChain, LangGraph, or any other classification technology.

- [Risk] Incorrect business ownership could expose messages to the wrong business extraction workflow.
  Mitigation: Enforce the existing business ownership boundary during relevance assessment and extraction eligibility queries.

- [Risk] Large WhatsApp imports may create many relevance assessments.
  Mitigation: Keep the relevance stage bounded and independently processable. Avoid performing expensive downstream extraction during relevance assessment.

## Migration Plan

The change will be introduced after the completed WhatsApp ingestion and business-data foundations.

Step 1: Add relevance persistence.

- Introduce the required persistence structures for relevance assessments while leaving existing raw message tables and records unchanged.
- Existing imported messages must remain valid after the schema change.

Step 2: Introduce relevance assessment.

- Add the relevance assessment service and state handling.
- Existing messages that have not yet been assessed should begin in `pending`.
- They must not automatically become extraction-eligible.

Step 3: Add extraction eligibility boundary.

- Expose a controlled way for future downstream extraction to retrieve only messages whose current relevance state is `relevant`.

Step 4: Integrate with incremental ingestion.

- When new messages are imported into an existing conversation, affected messages must become available for relevance assessment or reassessment.
- Existing raw records must remain unchanged.

Step 5: Verify compatibility.

- Run the existing ingestion and database test suites together with the new relevance tests.
- The implementation must confirm that:
  - existing WhatsApp imports continue to work
  - raw messages remain unchanged
  - business ownership remains isolated
  - relevance states are persisted correctly
  - extraction eligibility is enforced

## Rollback Strategy

If the relevance implementation needs to be rolled back:

- Disable the relevance assessment processing path.
- Preserve all existing raw WhatsApp messages.
- Preserve the existing ingestion functionality.
- Prevent downstream extraction from treating unassessed messages as automatically eligible.
- Roll back relevance-specific schema changes only if doing so does not remove or corrupt existing raw data.

The raw ingestion foundation must remain independently operational.

Because relevance data is derived data, rollback must never require deleting or modifying the original WhatsApp message evidence.
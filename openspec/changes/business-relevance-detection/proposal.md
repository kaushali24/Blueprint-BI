## Why

Blueprint BI now has the database and WhatsApp ingestion foundations
required to preserve imported conversation data as raw evidence.

The next MVP boundary is to distinguish business-relevant communication
from personal or unrelated conversation content before downstream business
extraction is allowed to interpret that data.

This is particularly important because a WhatsApp conversation may contain
both personal and business communication. For example, a business owner may
communicate with a friend, neighbour, or relative through the same WhatsApp
conversation used for placing orders.

Message-level relevance assessment allows Blueprint BI to retain the full
raw conversation while preventing unrelated messages from unnecessarily
contributing to business intelligence.

## What Changes

- Introduce a new `business-relevance-detection` capability.
- Add a post-ingestion relevance assessment stage operating on persisted
  WhatsApp conversation data.
- Assess individual messages for business relevance so that mixed personal
  and business conversations can be handled safely.
- Introduce explicit relevance states:
  - `pending`
  - `relevant`
  - `not_relevant`
  - `needs_review`
- Persist relevance assessments separately from raw message records.
- Preserve references from relevance assessments to the source conversation
  and message.
- Ensure raw imported messages are never modified by relevance assessment.
- Define message-level eligibility for downstream business extraction.
- Allow conversations containing both relevant and irrelevant messages to
  remain usable for downstream extraction.
- Make only messages marked `relevant` eligible for automatic downstream
  business extraction by default.
- Exclude `pending`, `not_relevant`, and `needs_review` messages from
  automatic business extraction by default.
- Support reassessment when new messages are imported into an existing
  conversation.
- Preserve previous raw data and provenance when relevance assessments are
  updated.
- Keep relevance detection separate from business entity extraction,
  analytics, RAG, and agent workflows.
- Do not introduce direct WhatsApp API integration.

## Capabilities

### New Capabilities

- `business-relevance-detection`: Assesses imported WhatsApp messages for
  business relevance and determines message-level eligibility for
  downstream business extraction.

### Modified Capabilities

- `business-data-foundation`: Extend the persisted business-data model to
  support traceable relevance assessment results and their source
  references.

## Impact

- **Backend:** Adds a business relevance assessment layer after WhatsApp
  ingestion.
- **Database:** Adds persistence for relevance assessment results and
  source-message references.
- **Processing flow:** Establishes the eligibility boundary between raw
  imported messages and downstream business extraction.
- **Testing:** Adds tests for message-level relevance, mixed personal and
  business conversations, state transitions, reassessment, traceability,
  and extraction gating.
- **AI dependencies:** The capability defines the relevance decision
  boundary but does not require a specific AI provider or model.
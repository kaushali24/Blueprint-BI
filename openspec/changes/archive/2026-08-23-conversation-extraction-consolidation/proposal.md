## Why

The current extraction service uses a per-message context window to extract business entities, causing fragmented and duplicated representations of a single business transaction. Furthermore, because this sliding window extracts continuously across the conversation, it generates excessive requests to the LLM provider, exhausting free-tier API quotas and permanently blocking the ingestion pipeline before a conversation finishes. We need an architecture that accurately tracks evolving business state (updates, additions, cancellations) within a cohesive "business episode" while remaining highly quota-efficient.

## What Changes

- Introduce a conversation-level transaction consolidation mechanism ("business episode") instead of purely per-message extraction.
- Minimize LLM request volume by extracting transactions per episode rather than running extraction for every single relevant message.
- Modify the idempotency strategy (`ExtractionTarget`) to reflect the new boundary (stable episode identity based on `conversation_id` and `start_message_id`).
- Support stateful business entities that can be refined (e.g., Inquiry becoming an Order, price adjustments, cancelled add-ons) based on later messages, rather than creating distinct overlapping entities.
- Ensure the extraction preserves links (evidence) to all relevant source messages to maintain traceability.
- **BREAKING**: Modify the `ExtractionTarget` table to support episode-based extraction instead of per-message targets, utilizing custom python migration scripts rather than Alembic.

## Capabilities

### New Capabilities

### Modified Capabilities
- `ai-business-extraction`: Changing the boundary of extraction from per-message context windows to deterministic business episodes, introducing atomic order evolution (updates, cancellations), explicit derived-entity ownership, and optimizing quota usage.

## Impact

- **Backend**: `ExtractionService`, `ExtractionTarget` processing, and the `ImportCoordinator` pipeline.
- **Database Schema**: Update `ExtractionTarget` to act on episode boundaries with a stable identity. Introduce an `extraction_target_id` FK on derived entities (`Order`, `Inquiry`, `Feedback`, `ExtractedFact`) to track exact ownership and enable atomic replacement.
- **LLM Usage**: Significantly reduced API calls, dramatically improving quota efficiency.

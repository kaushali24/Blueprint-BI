## Context

The current architecture relies on per-message context windows. For every message marked `relevant`, it triggers a separate LLM extraction call. This generates fragmented Orders and rapidly exhausts API quotas. A single conversation can easily exceed typical free-tier limits, blocking further processing.

## Goals / Non-Goals

**Goals:**
- Dramatically reduce the number of API calls required to extract business meaning by processing full "business episodes".
- Prevent duplicate/fragmented Orders from being generated when a single real-world transaction evolves over multiple messages.
- Safely replace an existing episode's extracted records (Inquiries, Orders) when new incremental messages refine the episode.
- Establish explicit database ownership so the system knows exactly which Order/Inquiry belongs to which extraction target.
- Correctly represent cancellations, price changes, and product adjustments by persisting the final supported state of the transaction.
- Preserve explicit links (evidence) between the derived entities and their source messages.
- Use the existing python-based SQLite migration strategy to safely deploy schema changes.

**Non-Goals:**
- Full event-sourcing or complex historical versioning of Orders.
- Unlimited LLM usage; the design must assume severe quota constraints.
- Real-time streaming or background cron workers (the MVP relies on `ImportCoordinator`).

## Evaluated Solution Approaches

### A. Conversation-level extraction
- Run extraction once over the entire conversation.
- **Cons:** Breaks if a customer places an order in July and another in August. Fails to segment multiple genuine transactions.

### B. Segment-level transaction grouping (Recommended)
- Group relevant and contextual messages into "Business Episodes" based on a deterministic time-gap heuristic (e.g., > 7 days of inactivity = new episode). Run ONE extraction per episode.
- **Pros:** Lowest possible API usage without collapsing genuinely distinct orders. Solves the quota exhaustion. Natively handles updates/cancellations because the LLM processes the whole episode at once and outputs the final resolved state.

## Decisions

### 1. Business Episode Boundary Algorithm
A Business Episode begins at the first unextracted `relevant` message. It includes all subsequent `relevant` and `needs_review` messages. The episode remains open and continuous as long as the time gap between sequential messages is <= 7 days. If a gap exceeds 7 days, the current episode is closed, and the next `relevant` message will start a new episode. `pending` and `not_relevant` messages are strictly excluded from the episode context payload.

### 2. Stable Extraction Target Identity
The `ExtractionTarget` table will be repurposed to track Business Episodes. Its unique stable identity will be `(business_id, conversation_id, start_message_id)`. The `end_message_id` will be mutable, allowing the episode to "expand" as new incremental imports arrive within the 7-day window.

### 3. Derived-Entity Ownership Mechanism
To safely manage updates, `ExtractionTarget` MUST explicitly own its derived records. We will add an `extraction_target_id` Foreign Key to `Order`, `Inquiry`, `Feedback`, and `ExtractedFact`. The system will not rely on fuzzy matching or LLM inference to identify which Order to update.

### 4. Re-extraction and Atomic Replacement
When an incremental import adds new messages (e.g. 31..36) to an existing episode (10..30):
1. The `ExtractionTarget` status is marked `pending`.
2. The LLM processes the expanded episode (10..36).
3. If successful, the system atomically DELETES all prior derived records (Order, Inquiry, etc.) owned by this `extraction_target_id` and INSERTS the newly generated ones, updating their `ExtractionEvidence`.
4. The `ExtractionTarget.status` is set to `succeeded` and `end_message_id` is updated.
5. If the LLM call or validation fails, the transaction is rolled back. The previously successful Order and evidence remain fully intact.

### 5. Configurable Episode Limits (Provider Neutral)
Instead of relying on specific model contexts (e.g. Gemini 1.5), the extraction service will enforce a configurable budget (e.g., `MAX_EPISODE_MESSAGES=200`). If a single episode exceeds this bound, the extraction will fail safely with a deterministic `failure_reason`.

### 6. Pipeline Integration
The implementation will integrate directly into the existing `ImportCoordinator` and `ExtractionService` pipeline. There are no background cron workers in the MVP.

## Migration Plan

**1. Schema Changes (SQLite Scripts):**
We will create a python script `scripts/migrate_extraction_consolidation.py` consistent with existing MVP migration conventions. The script will:
- Drop the existing `extraction_target` table and recreate it with the new stable identity `(id, business_id, conversation_id, start_message_id, end_message_id, status, ...)` and a unique constraint on `(business_id, conversation_id, start_message_id)`.
- Add `extraction_target_id` FK to `Order`, `OrderItem`, `Inquiry`, `Feedback`, and `ExtractedFact`.

**2. Legacy Row Compatibility:**
Existing `message_id`-based `ExtractionTarget` rows are fundamentally incompatible with the episode-based approach. The migration script will DROP the legacy table outright. Existing derived data (fragmented Orders) will not have an `extraction_target_id`.

**3. Dilhani Recovery Plan:**
After running the migration script, a specific local demo recovery script (`scripts/audit_dilhani_recovery.py`) will PURGE all `Order`, `OrderItem`, `Inquiry`, `Feedback`, `ExtractedFact`, and `ExtractionEvidence` rows for Business 1. We will NOT delete `Message`, `Conversation`, or `RelevanceAssessment`. We will then run the new `ExtractionService` against Business 1, which will natively generate a single 17-message episode, emit 1 LLM request, and produce a single Rs. 17,300 Order.

## Risks / Trade-offs

- **[Risk]** The 7-day heuristic might occasionally group two distinct rapid-fire orders into one episode. 
  → **Mitigation:** The LLM prompt will explicitly instruct the model to output *multiple* Orders if it detects multiple separate transactions within the same episode context. The MVP favors quota-safety over complex multi-pass boundary detection.

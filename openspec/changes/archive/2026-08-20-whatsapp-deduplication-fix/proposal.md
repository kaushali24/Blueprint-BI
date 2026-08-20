# Proposal: WhatsApp Deduplication Fix

## 1. Problem Statement

The current WhatsApp ingestion system hashes the `sender`, `content`, `message_type`, `timestamp`, and `conversation_id` to generate a deduplication fingerprint. 

Because WhatsApp exports only provide timestamps at minute-level resolution, if a sender transmits identical consecutive messages within the same minute (e.g., "ok", "ok"), the parser generates identical fingerprints for both messages. During the database insertion phase, the first message is successfully persisted. When the second message is evaluated, the system queries the database, matches the fingerprint of the newly inserted first message, and incorrectly discards the second message as a "duplicate".

This results in genuine data loss. Since the AI Business Extraction layer depends on high-fidelity conversational context, losing these legitimate double-messages (which often act as confirmations) degrades extraction accuracy.

## 2. Proposed Solution

We will introduce a surgically scoped update to the deduplication fingerprinting mechanism that deterministically distinguishes identical messages without compromising exact-match deduplication across repeated incremental imports.

### A. Intra-Minute Sequencing
The parser will maintain a chronological tally of identical messages within the parsed export. For each message, it computes a key comprising `(source_timestamp, sender, content, message_type)`. The parser records how many times this exact tuple has appeared so far in the file, attaching an `intra_minute_sequence` integer (starting at 0) to the parsed record.

For the MVP, when a repeated or updated export retains the previously exported message ordering, the occurrence count for an identical message tuple is deterministic across imports. The mechanism does not attempt to provide a globally stable WhatsApp message identifier when the available export itself does not provide one.

### B. Fingerprint V2
The `IngestionService._make_fingerprint` function will be updated to include the `intra_minute_sequence` value in its hash generation, creating a V2 fingerprint. This ensures that the first "ok" (`seq=0`) and the second "ok" (`seq=1`) generate distinct, deterministic fingerprints.

### C. Targeted Legacy Fallback
To ensure backward compatibility without re-introducing the data-loss bug, the duplicate-checking query will implement a conditional fallback:
*   If `seq == 0`, the query searches the database for BOTH the `v2_fingerprint` and the `legacy_fingerprint` (which lacks the sequence number).
*   If `seq > 0`, the query searches ONLY for the `v2_fingerprint`.

This precise logic guarantees that already-imported messages (which are all `seq=0` since the legacy system dropped subsequent ones) are correctly skipped, while simultaneously allowing the system to naturally **recover** previously lost duplicate messages upon the next incremental re-import.

## 3. Strict Invariants Preserved

*   **No Unrelated Refactoring**: This change does NOT introduce contact renaming heuristics, conversation merging, or relevance reassessment.
*   **Immutable Evidence**: Raw Message records, their original `import_batch_id`, sender strings, and source timestamps remain strictly unchanged.
*   **Customer Identity Logic**: Completely untouched.

## 4. Risks/Trade-offs

*   **Export-window limitation**: If a later export omits or changes earlier history used to establish occurrence ordering, sequence-based identity may not correspond perfectly to the earlier export. The MVP does not attempt to reconstruct unavailable WhatsApp message IDs.

## 5. MVP Assessment

This fix is **safe and highly recommended** to implement before proceeding to AI Business Extraction. 
The code changes are minimal (localized to `parser.py` sequence tracking and a minor query update in `service.py`), but the payoff is absolute data integrity for identical chronological messages. It removes a silent data-loss failure mode before downstream AI models begin relying on the transcript.

# System Design: WhatsApp Deduplication Fix

## 1. Architectural Impact
This change is localized strictly to the ingestion parsing and orchestration logic (`backend/app/ingestion/parser.py` and `backend/app/ingestion/service.py`). No database schema changes or new models are required. The legacy `message_fingerprint` column continues to operate as an opaque string hash.

## 2. Component Design

### 2.1 Parser Sequence Tracking (`parser.py`)
*   **Mechanism:** `parse_whatsapp_chat_text` will maintain a `collections.Counter` instance.
*   **Key Generation:** For each successfully parsed message line, it creates a tuple key: `(source_timestamp, sender, content, message_type)`.
*   **Assignment:** The parser queries the counter for the current tally of this key, assigns it to a new dictionary field `intra_minute_sequence`, and increments the counter.
*   **Stability:** For the MVP, when a repeated or updated export retains the previously exported message ordering, the occurrence count for an identical message tuple is deterministic across imports. The mechanism does not attempt to provide a globally stable WhatsApp message identifier when the available export itself does not provide one.

### 2.2 Deduplication Fingerprint V2 (`service.py`)
*   **Current State:** `_make_fingerprint` hashes: `conversation_id`, `timestamp_key`, `sender`, `content`, `message_type`.
*   **New State:** `_make_fingerprint_v2` hashes: `conversation_id`, `timestamp_key`, `sender`, `content`, `message_type`, and `intra_minute_sequence`.
*   **Legacy Fallback Fingerprint:** The system will also maintain a `_make_legacy_fingerprint` function (identical to the old `_make_fingerprint`) to compute hashes without the sequence number.

### 2.3 Conditional Deduplication Query (`service.py`)
*   In `IngestionService.import_package()`, the `existing_message` query will be updated to intelligently handle legacy fallbacks to prevent duplicating older records while recovering lost ones.
*   **Logic:**
    ```python
    fingerprint_v2 = self._make_fingerprint_v2(..., sequence)
    
    if sequence == 0:
        # Check for both V2 and Legacy fingerprints
        legacy_fingerprint = self._make_legacy_fingerprint(...)
        existing_message = session.execute(
            select(Message).where(
                Message.conversation_id == conversation.id,
                Message.message_fingerprint.in_([fingerprint_v2, legacy_fingerprint])
            )
        ).scalar_one_or_none()
    else:
        # Only check V2 fingerprint. Do NOT fallback to legacy.
        # This prevents the second identical message (seq=1) from matching 
        # the legacy fingerprint of the first message, allowing it to be inserted.
        existing_message = session.execute(
            select(Message).where(
                Message.conversation_id == conversation.id,
                Message.message_fingerprint == fingerprint_v2
            )
        ).scalar_one_or_none()
    ```

## 3. Database Updates
*   **No Schema Changes Required.** 

## 4. Security & Isolation Considerations
*   No impact. Business isolation parameters (`conversation_id` scoped to `business_id`) remain deeply embedded in the deduplication hashes and database constraints.

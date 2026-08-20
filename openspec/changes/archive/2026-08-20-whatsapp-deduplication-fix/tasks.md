# Tasks: WhatsApp Deduplication Fix

## 1. Test-Driven Setup
- [x] Add `test_identical_messages_in_same_minute_are_preserved` to `tests/test_whatsapp_ingestion_integrity.py`.
  - Provide an export payload with two exact consecutive identical messages (e.g., "ok", "ok").
  - Import the payload and assert that 2 distinct `Message` rows are inserted.
  - Re-import the exact same payload in a second batch.
  - Assert that the database still contains only 2 total `Message` rows for that content/timestamp, verifying no duplicate leakage on re-import.
- [x] Add `test_legacy_message_recovery_preserves_compatibility` to `tests/test_whatsapp_ingestion_integrity.py`.
  - Simulate a "legacy" database state by manually inserting a single `Message` with a V1 legacy fingerprint (without a sequence number).
  - Provide an export payload containing *two* occurrences of that identical message.
  - Import the payload.
  - Assert that the system skips the first message (matching the legacy fingerprint) but successfully inserts the second message, resulting in exactly 2 rows in the database.

## 2. Parser Enhancements
- [x] Modify `parse_whatsapp_chat_text` in `backend/app/ingestion/parser.py`.
  - Import `collections.Counter`.
  - Instantiate a counter for the current parse session.
  - For each parsed message, generate a key: `(source_timestamp, sender, content, message_type)`.
  - Assign `intra_minute_sequence = counter[key]` to the record.
  - Increment the counter.

## 3. Fingerprint V2 Logic
- [x] In `backend/app/ingestion/service.py`, rename the existing `_make_fingerprint` to `_make_legacy_fingerprint` (leaving its signature and logic exactly as is).
- [x] Create `_make_fingerprint_v2` that accepts an additional `intra_minute_sequence` parameter.
- [x] Append the sequence to the raw string used for SHA-256 hashing in `_make_fingerprint_v2`.

## 4. Deduplication Orchestration
- [x] In `IngestionService.import_package()`, extract `intra_minute_sequence` from the parsed record.
- [x] Compute `fingerprint_v2 = self._make_fingerprint_v2(...)`.
- [x] Implement conditional `existing_message` lookup logic:
  - If `sequence == 0`, compute `legacy_fingerprint` and query `Message.message_fingerprint.in_([fingerprint_v2, legacy_fingerprint])`.
  - If `sequence > 0`, query `Message.message_fingerprint == fingerprint_v2`.
## 5. Regression and Specification Verification
- [x] Run the complete WhatsApp ingestion test suite and confirm all tests pass.
- [x] Run the complete backend test suite and confirm no regressions.
- [x] Verify unchanged export re-import still creates zero duplicate messages.
- [x] Verify incremental import with additional messages still adds only new messages.
- [x] Verify existing message import provenance remains unchanged.
- [x] Run `openspec validate whatsapp-deduplication-fix`.

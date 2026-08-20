# Specification: WhatsApp Deduplication Fix

## Overview
This specification addresses a data-loss bug in the initial WhatsApp ingestion release where legitimate identical messages sent in the same minute are incorrectly discarded as duplicates during initial ingestion.

## MODIFIED Requirements

### Requirement: 1. Identical Message Preservation
* The ingestion parser MUST deterministically distinguish identical sequential messages.
* The system MUST safely insert and persist all legitimate identical messages present in an export file.
* The raw `sender` string MUST remain in the deduplication fingerprint to preserve basic backwards compatibility.
* The solution MUST NOT use non-deterministic identifiers (e.g., random UUIDs) or globally mutable properties (like arbitrary row indices that shift if older history is prepended).

#### Scenario: Initial Import of Identical Messages
* **Given** a chat file contains two identical messages at the exact same minute: `10:32 Customer: ok` and `10:32 Customer: ok`.
* **When** the file is imported.
* **Then** the database MUST contain exactly two `Message` records for "ok" at `10:32`.

### Requirement: 2. Stable Sequencing Mechanism
* For the MVP, when a repeated or updated export retains the previously exported message ordering, the occurrences of identical messages are chronologically fixed.
* The parser MUST calculate an `intra_minute_sequence` integer representing the occurrence count of a specific `(source_timestamp, sender, content, message_type)` tuple from the start of the parsed file.
* The first occurrence receives `seq=0`, the second `seq=1`, etc.
* This sequence integer MUST be incorporated into the generation of the deduplication fingerprint (V2 fingerprint).

#### Scenario: Exact Re-Import Deduplication
* **Given** the database already contains the two identical `Message` records from Scenario A.
* **When** the exact same chat file is re-imported.
* **Then** the system MUST skip both messages (due to V2 fingerprint matches).
* **And** no new duplicate rows are inserted.

### Requirement: 3. Targeted Backward Compatibility
* Re-importing a previously imported chat MUST NOT duplicate any legacy messages.
* The database deduplication query MUST conditionally check for legacy fingerprints.
* If a parsed message has `intra_minute_sequence == 0`, the query MUST check if `Message.message_fingerprint` matches EITHER the V2 fingerprint OR the legacy fingerprint. (This catches legacy messages).
* If a parsed message has `intra_minute_sequence > 0`, the query MUST check ONLY the V2 fingerprint. (This allows previously lost identical messages to be successfully recovered upon re-import).

#### Scenario: Legacy Data Re-Import and Recovery
* **Given** the database contains a chat imported prior to this fix, where only ONE `10:32 Customer: ok` message exists (the legacy system dropped the second one).
* **When** the same chat file (containing both "ok" messages) is re-imported under the new logic.
* **Then** the first "ok" (`seq=0`) MUST match the legacy fingerprint in the database and be skipped.
* **And** the second "ok" (`seq=1`) MUST NOT match the legacy fingerprint in the database, and MUST be successfully inserted as a new message, recovering the previously lost data.

## 3. Strict Out of Scope Restrictions
*   This change MUST NOT modify how `WhatsAppIdentity` or `Customer` records are resolved.
*   This change MUST NOT attempt to merge `Conversation` records across filename changes.
*   This change MUST NOT trigger relevance reassessments for older messages.

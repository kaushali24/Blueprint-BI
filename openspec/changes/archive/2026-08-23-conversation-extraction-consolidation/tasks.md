## 1. Schema Updates and Migrations

- [ ] 1.1 Create migration script `scripts/migrate_extraction_consolidation.py` to drop the legacy `extraction_target` table and recreate it with the new stable identity: `(business_id, conversation_id, start_message_id)`.
- [ ] 1.2 Update `scripts/migrate_extraction_consolidation.py` to add `extraction_target_id` FK to `Order`, `OrderItem`, `Inquiry`, `Feedback`, and `ExtractedFact` tables using SQLite-compatible migration commands.
- [ ] 1.3 Update SQLAlchemy models in `backend/app/database/models.py` to reflect the new `ExtractionTarget` schema and the new `extraction_target_id` foreign keys on derived entities.

## 2. LLM Extraction Prompt & Config Adjustments

- [ ] 2.1 Update LLM system prompts in `ExtractionProvider` to instruct the model to analyze a full business episode and emit the final consolidated state (handling cancellations natively and omitting them from the final output).
- [ ] 2.2 Add `MAX_EPISODE_MESSAGES` (e.g., 200) to application configuration to safely bound context size without assuming a specific provider's token limits.
- [ ] 2.3 Verify that Pydantic validation handles multi-message episodes correctly.

## 3. Extraction Service Refactoring

- [ ] 3.1 Implement business episode boundary algorithm: group relevant and needs_review messages into an episode, closing it only when a time gap exceeds 7 days. Exclude pending/not_relevant messages.
- [ ] 3.2 Refactor `extract_from_message` into `extract_episode` within `ExtractionService`.
- [ ] 3.3 Implement Atomic Replacement logic: when re-extracting an expanded episode, use a DB transaction to delete old derived records belonging to the `extraction_target_id` and insert new ones. If the provider fails, explicitly rollback to preserve the prior valid state.
- [ ] 3.4 Integrate the new episode-based extraction directly into `ImportCoordinator` and `ExtractionService` (avoiding nonexistent background cron workers).

## 4. Testing

- [ ] 4.1 Write test: long transaction with >24h gaps remains one episode when still unresolved (e.g., 2-day gap).
- [ ] 4.2 Write test: two genuine orders in one conversation (e.g., July order, August order with 14-day gap) become two distinct episodes generating two LLM calls.
- [ ] 4.3 Write test: relevant + needs_review context inclusion, pending/not_relevant exclusion.
- [ ] 4.4 Write test: unchanged incremental re-import creates zero LLM calls.
- [ ] 4.5 Write test: incremental extension of an existing episode triggers exactly one re-extraction call.
- [ ] 4.6 Write test: failed re-extraction (provider error) leaves previous successful Order and evidence unchanged.
- [ ] 4.7 Write test: successful re-extraction replaces old episode-owned Order/Items atomically (Inquiry becomes Order without duplicates, cancelled add-ons removed).

## 5. Database Cleanup & Dilhani Recovery

- [ ] 5.1 Write local demo recovery script `scripts/audit_dilhani_recovery.py` to safely purge fragmented records (Orders, OrderItems, Inquiries, ExtractedFacts, ExtractionEvidence) ONLY for Business 1, explicitly preserving raw `Message`, `Conversation`, and `RelevanceAssessment`.
- [ ] 5.2 Execute the migration script and the Dilhani purge script locally.
- [ ] 5.3 Trigger the updated extraction pipeline on the existing Dilhani conversation to generate the single consolidated transaction (expected 1 API call).
- [ ] 5.4 Verify analytics endpoint returns a single, correct Order record.

# Tasks: WhatsApp Ingestion Foundation

## 1. Ingestion Module Foundation

- [x] 1.1 Create WhatsApp ingestion module structure.
- [x] 1.2 Add upload/input handling.
- [x] 1.3 Add import batch lifecycle tracking.
- [x] 1.4 Define the processing-unit boundary used to isolate independently processable import work.

## 2. ZIP Validation and Extraction

- [x] 2.1 Validate uploaded ZIP files.
- [x] 2.2 Safely extract supported export contents into a controlled temporary workspace.
- [x] 2.3 Identify supported WhatsApp chat export files within the extracted package.
- [x] 2.4 Handle invalid archives and unsupported export structures.
- [x] 2.5 Clean up temporary extraction files after processing.

## 3. WhatsApp Chat Parsing

- [x] 3.1 Implement WhatsApp export message parsing.
- [x] 3.2 Normalize timestamps and message content.
- [x] 3.3 Extract participant and WhatsApp identity information.
- [x] 3.4 Capture media references and metadata.
- [x] 3.5 Preserve original source information required for provenance and deduplication.
- [x] 3.6 Handle malformed or partially parseable chat records without terminating unrelated processing units.

## 4. Conversation and Identity Handling

- [x] 4.1 Implement deterministic conversation identification using stable source information available in the export.
- [x] 4.2 Associate messages with existing conversations when a deterministic match exists.
- [x] 4.3 Create new conversations when no deterministic conversation match exists.
- [x] 4.4 Preserve newly observed WhatsApp identities independently.
- [x] 4.5 Prevent automatic merging of uncertain WhatsApp identities.

## 5. Persistence and Incremental Imports

- [x] 5.1 Persist normalized records using the existing database foundation.
- [x] 5.2 Implement deterministic message identity/fingerprinting.
- [x] 5.3 Implement message deduplication using source identity/fingerprint.
- [x] 5.4 Preserve original message import provenance.
- [x] 5.5 Support incremental re-imports containing both existing and newly observed messages.
- [x] 5.6 Maintain transaction integrity during persistence.
- [x] 5.7 Commit independently successful processing units atomically.
- [x] 5.8 Roll back failed processing units without unnecessarily affecting successful processing units.

## 6. Import Results and Error Handling

- [x] 6.1 Implement import status transitions.
- [x] 6.2 Record validation, parsing, normalization, and persistence errors.
- [x] 6.3 Distinguish complete, partial, and failed import results.
- [x] 6.4 Preserve successfully processed records when individual processing units fail.
- [x] 6.5 Record warnings for unsupported media or other non-fatal conditions.
- [x] 6.6 Return safe application-facing error information without exposing internal stack traces.

## 7. API Boundary

- [x] 7.1 Add an application upload endpoint for WhatsApp ZIP files.
- [x] 7.2 Validate API inputs and upload constraints.
- [x] 7.3 Create an ImportBatch for each accepted import.
- [x] 7.4 Return import status and processing results.
- [x] 7.5 Ensure the API does not require AI/LLM services for ingestion.

## 8. Testing

- [x] 8.1 Test ZIP validation.
- [x] 8.2 Test safe ZIP extraction and temporary workspace cleanup.
- [x] 8.3 Test WhatsApp message parsing.
- [x] 8.4 Test timestamp and message-content normalization.
- [x] 8.5 Test participant and WhatsApp identity extraction.
- [x] 8.6 Test media metadata preservation.
- [x] 8.7 Test conversation identity across repeated imports.
- [x] 8.8 Test deterministic message fingerprinting.
- [x] 8.9 Test incremental imports and message deduplication.
- [x] 8.10 Test identity isolation and prevention of automatic identity merging.
- [x] 8.11 Test persistence against the database foundation.
- [x] 8.12 Test partial and failed imports.
- [x] 8.13 Test transaction commit behavior.
- [x] 8.14 Test transaction rollback behavior.
- [x] 8.15 Test upload API behavior.
- [x] 8.16 Test complete, partial, and failed ImportBatch outcomes.

## 9. Specification Verification

- [x] 9.1 Verify implementation satisfies all requirements and scenarios in `whatsapp-ingestion/spec.md`.
- [x] 9.2 Verify implementation matches the approved `whatsapp-ingestion/design.md`.
- [x] 9.3 Verify ingestion has no dependency on Gemini, LangChain, LangGraph, RAG, embeddings, or vector databases.
- [x] 9.4 Verify raw imported message data remains independent from AI-derived business information.
- [x] 9.5 Run `openspec validate whatsapp-ingestion-foundation`.
- [x] 9.6 Run the complete ingestion test suite and confirm all tests pass.
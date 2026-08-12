## 1. Database Infrastructure

- [ ] 1.1 Create the database package structure for connection, base, session management, and models.
- [ ] 1.2 Configure the SQLite database path under the backend data directory.
- [ ] 1.3 Configure the SQLAlchemy 2.x database engine and managed session mechanism.
- [ ] 1.4 Enable SQLite foreign-key enforcement for database connections.
- [ ] 1.5 Create the shared SQLAlchemy declarative base and metadata configuration.

## 2. Business and Identity Models

- [ ] 2.1 Implement the Business model with its required fields, timestamps, and constraints.
- [ ] 2.2 Implement the Customer model and its relationship to Business.
- [ ] 2.3 Implement the WhatsAppIdentity model and its relationships to Customer and Business.
- [ ] 2.4 Add business-scoped uniqueness constraints for WhatsApp identities.
- [ ] 2.5 Add and verify indexes for business and customer identity lookups.

## 3. Import and Raw Conversation Models

- [ ] 3.1 Implement the ImportBatch model and its relationship to Business.
- [ ] 3.2 Implement the Conversation model and its relationships to Business and ImportBatch.
- [ ] 3.3 Implement the Participant model and its relationship to Conversation.
- [ ] 3.4 Implement the Message model and its relationships to Conversation and Participant.
- [ ] 3.5 Implement message identity and fingerprint fields required by the database specification.
- [ ] 3.6 Implement the Media model and its relationship to Message.
- [ ] 3.7 Add and verify indexes for conversation, participant, message timestamp, and message identity lookups.

## 4. Derived Business Models

- [ ] 4.1 Implement the Inquiry model and its business, customer, and conversation relationships.
- [ ] 4.2 Implement the Order model and its business, customer, and conversation relationships.
- [ ] 4.3 Implement the OrderItem model and its relationship to Order.
- [ ] 4.4 Implement the Feedback model and its business, customer, order, and conversation relationships.
- [ ] 4.5 Implement the ExtractedFact model and its business, customer, and conversation relationships.
- [ ] 4.6 Implement monetary fields using numeric/decimal-compatible database types.
- [ ] 4.7 Implement extraction status, confidence, model metadata, and extraction timestamps required by the specification.

## 5. Evidence and Provenance

- [ ] 5.1 Implement the ExtractionEvidence model and its relationship to Message.
- [ ] 5.2 Implement explicit evidence relationships for Inquiry, Order, Feedback, and ExtractedFact.
- [ ] 5.3 Implement the explicit foreign-key relationships required for each supported derived record type so that every evidence record references exactly one derived record and one source message.
- [ ] 5.4 Verify that one derived record can reference multiple source messages.
- [ ] 5.5 Verify that one source message can support multiple derived records.
- [ ] 5.6 Add indexes required for efficient evidence and source-message lookups.

## 6. Relationships and Integrity Constraints

- [ ] 6.1 Complete all foreign-key relationships defined by the database specification.
- [ ] 6.2 Add required uniqueness constraints and unique indexes.
- [ ] 6.3 Add required nullable/non-nullable constraints.
- [ ] 6.4 Add applicable database-level integrity constraints defined by the schema.
- [ ] 6.5 Verify that invalid foreign-key references are rejected.
- [ ] 6.6 Verify that business ownership is determinable for all business-owned records.
- [ ] 6.7 Verify that raw message data remains independent from derived business records.
- [ ] 6.8 Define and implement appropriate relationship deletion behavior for dependent records, avoiding accidental deletion of raw conversation evidence.

## 7. Timestamp and Persistence Conventions

- [ ] 7.1 Implement the project-wide UTC convention for application-managed timestamps.
- [ ] 7.2 Preserve source timestamps separately from database creation, import, and extraction timestamps.
- [ ] 7.3 Verify timestamp persistence and retrieval behavior for the applicable entities.
- [ ] 7.4 Verify monetary value persistence without floating-point rounding behavior.

## 8. Database Initialization

- [ ] 8.1 Register and verify all 14 models with the shared SQLAlchemy metadata, ensuring all model modules are imported before schema initialization.
- [ ] 8.2 Implement repeatable development database initialization from SQLAlchemy metadata.
- [ ] 8.3 Verify initialization creates all required tables.
- [ ] 8.4 Verify repeated initialization does not recreate or corrupt existing tables.
- [ ] 8.5 Verify required indexes and constraints exist after initialization.
- [ ] 8.6 Ensure the generated SQLite database is stored outside source-controlled code.

## 9. Transaction Management

- [ ] 9.1 Implement managed transaction handling for database operations.
- [ ] 9.2 Verify successful related-record persistence commits atomically.
- [ ] 9.3 Verify failed related-record persistence rolls back completely.
- [ ] 9.4 Verify an incomplete order cannot leave partially persisted order items.

## 10. Database Integration Tests

- [ ] 10.1 Create a test database setup isolated from the development database.
- [ ] 10.2 Test database initialization and creation of all 14 entities.
- [ ] 10.3 Test Business, Customer, and WhatsAppIdentity persistence and relationships.
- [ ] 10.4 Test ImportBatch, Conversation, Participant, Message, and Media persistence.
- [ ] 10.5 Test Inquiry, Order, OrderItem, Feedback, and ExtractedFact persistence.
- [ ] 10.6 Test ExtractionEvidence relationships and provenance retrieval.
- [ ] 10.7 Test foreign-key and uniqueness constraint enforcement.
- [ ] 10.8 Test business ownership and cross-business isolation at the data-access level.
- [ ] 10.9 Test transaction commit and rollback behavior.
- [ ] 10.10 Test UTC timestamp and monetary-value persistence behavior.
- [ ] 10.11 Run the complete database test suite and confirm all tests pass.
- [ ] 10.12 Test that deletion or modification of derived business records does not remove the underlying raw message evidence.

## 11. Database Foundation Verification

- [ ] 11.1 Verify the implemented schema matches the validated database specification.
- [ ] 11.2 Verify the implementation satisfies all scenarios in `business-data-foundation/spec.md`.
- [ ] 11.3 Verify the database layer has no dependency on LangGraph, LangChain, Gemini, or other LLM components.
- [ ] 11.4 Run `openspec validate database-foundation` after implementation.
- [ ] 11.5 Mark the database-foundation implementation complete only after all database tests and specification checks pass.
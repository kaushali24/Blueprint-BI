## 1. Database Infrastructure

- [x] 1.1 Create the database package structure for connection, base, session management, and models.
- [x] 1.2 Configure the SQLite database path under the backend data directory.
- [x] 1.3 Configure the SQLAlchemy 2.x database engine and managed session mechanism.
- [x] 1.4 Enable SQLite foreign-key enforcement for database connections.
- [x] 1.5 Create the shared SQLAlchemy declarative base and metadata configuration.

## 2. Business and Identity Models

- [x] 2.1 Implement the Business model with its required fields, timestamps, and constraints.
- [x] 2.2 Implement the Customer model and its relationship to Business.
- [x] 2.3 Implement the WhatsAppIdentity model and its relationships to Customer and Business.
- [x] 2.4 Add business-scoped uniqueness constraints for WhatsApp identities.
- [x] 2.5 Add and verify indexes for business and customer identity lookups.

## 3. Import and Raw Conversation Models

- [x] 3.1 Implement the ImportBatch model and its relationship to Business.
- [x] 3.2 Implement the Conversation model and its relationships to Business and ImportBatch.
- [x] 3.3 Implement the Participant model and its relationship to Conversation.
- [x] 3.4 Implement the Message model and its relationships to Conversation and Participant.
- [x] 3.5 Implement message identity and fingerprint fields required by the database specification.
- [x] 3.6 Implement the Media model and its relationship to Message.
- [x] 3.7 Add and verify indexes for conversation, participant, message timestamp, and message identity lookups.

## 4. Derived Business Models

- [x] 4.1 Implement the Inquiry model and its business, customer, and conversation relationships.
- [x] 4.2 Implement the Order model and its business, customer, and conversation relationships.
- [x] 4.3 Implement the OrderItem model and its relationship to Order.
- [x] 4.4 Implement the Feedback model and its business, customer, order, and conversation relationships.
- [x] 4.5 Implement the ExtractedFact model and its business, customer, and conversation relationships.
- [x] 4.6 Implement monetary fields using numeric/decimal-compatible database types.
- [x] 4.7 Implement extraction status, confidence, model metadata, and extraction timestamps required by the specification.

## 5. Evidence and Provenance

- [x] 5.1 Implement the ExtractionEvidence model and its relationship to Message.
- [x] 5.2 Implement explicit evidence relationships for Inquiry, Order, Feedback, and ExtractedFact.
- [x] 5.3 Implement the explicit foreign-key relationships required for each supported derived record type so that every evidence record references exactly one derived record and one source message.
- [x] 5.4 Verify that one derived record can reference multiple source messages.
- [x] 5.5 Verify that one source message can support multiple derived records.
- [x] 5.6 Add indexes required for efficient evidence and source-message lookups.

## 6. Relationships and Integrity Constraints

- [x] 6.1 Complete all foreign-key relationships defined by the database specification.
- [x] 6.2 Add required uniqueness constraints and unique indexes.
- [x] 6.3 Add required nullable/non-nullable constraints.
- [x] 6.4 Add applicable database-level integrity constraints defined by the schema.
- [x] 6.5 Verify that invalid foreign-key references are rejected.
- [x] 6.6 Verify that business ownership is determinable for all business-owned records.
- [x] 6.7 Verify that raw message data remains independent from derived business records.
- [x] 6.8 Define and implement appropriate relationship deletion behavior for dependent records, avoiding accidental deletion of raw conversation evidence.

## 7. Timestamp and Persistence Conventions

- [x] 7.1 Implement the project-wide UTC convention for application-managed timestamps.
- [x] 7.2 Preserve source timestamps separately from database creation, import, and extraction timestamps.
- [x] 7.3 Verify timestamp persistence and retrieval behavior for the applicable entities.
- [x] 7.4 Verify monetary value persistence without floating-point rounding behavior.

## 8. Database Initialization

- [x] 8.1 Register and verify all 14 models with the shared SQLAlchemy metadata, ensuring all model modules are imported before schema initialization.
- [x] 8.2 Implement repeatable development database initialization from SQLAlchemy metadata.
- [x] 8.3 Verify initialization creates all required tables.
- [x] 8.4 Verify repeated initialization does not recreate or corrupt existing tables.
- [x] 8.5 Verify required indexes and constraints exist after initialization.
- [x] 8.6 Ensure the generated SQLite database is stored outside source-controlled code.

## 9. Transaction Management

- [x] 9.1 Implement managed transaction handling for database operations.
- [x] 9.2 Verify successful related-record persistence commits atomically.
- [x] 9.3 Verify failed related-record persistence rolls back completely.
- [x] 9.4 Verify an incomplete order cannot leave partially persisted order items.

## 10. Database Integration Tests

- [x] 10.1 Create a test database setup isolated from the development database.
- [x] 10.2 Test database initialization and creation of all 14 entities.
- [x] 10.3 Test Business, Customer, and WhatsAppIdentity persistence and relationships.
- [x] 10.4 Test ImportBatch, Conversation, Participant, Message, and Media persistence.
- [x] 10.5 Test Inquiry, Order, OrderItem, Feedback, and ExtractedFact persistence.
- [x] 10.6 Test ExtractionEvidence relationships and provenance retrieval.
- [x] 10.7 Test foreign-key and uniqueness constraint enforcement.
- [x] 10.8 Test business ownership and cross-business isolation at the data-access level.
- [x] 10.9 Test transaction commit and rollback behavior.
- [x] 10.10 Test UTC timestamp and monetary-value persistence behavior.
- [x] 10.11 Run the complete database test suite and confirm all tests pass.
- [x] 10.12 Test that deletion or modification of derived business records does not remove the underlying raw message evidence.

## 11. Database Foundation Verification

- [x] 11.1 Verify the implemented schema matches the validated database specification.
- [x] 11.2 Verify the implementation satisfies all scenarios in `business-data-foundation/spec.md`.
- [x] 11.3 Verify the database layer has no dependency on LangGraph, LangChain, Gemini, or other LLM components.
- [x] 11.4 Run `openspec validate database-foundation` after implementation.
- [x] 11.5 Mark the database-foundation implementation complete only after all database tests and specification checks pass.
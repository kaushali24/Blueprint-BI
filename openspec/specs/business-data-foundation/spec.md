# business-data-foundation Specification

## Purpose
Provides a persistent, traceable business-data foundation for Blueprint BI / ChatInsights.

This capability establishes the SQLite and SQLAlchemy persistence layer required to store imported WhatsApp conversation data and validated business information derived from those conversations.

The database foundation is intended to provide a stable data contract for subsequent capabilities including WhatsApp ingestion, AI extraction, analytics, evidence retrieval, and LangGraph agent tools.

### Scope Boundary

This capability is responsible for:

- Defining the MVP business-data schema.
- Creating and initializing the SQLite database.
- Providing SQLAlchemy models and persistence mechanisms.
- Maintaining relationships, constraints, indexes, and referential integrity.
- Preserving raw conversation data separately from AI-derived business information.
- Supporting source-message evidence relationships.
- Storing metadata required for AI extraction and human review.

The following are outside the scope of this capability and SHALL be implemented by subsequent capabilities:

- WhatsApp ZIP parsing.
- WhatsApp message ingestion.
- Incremental import processing.
- Duplicate-detection workflow.
- AI information extraction.
- Multilingual processing.
- Business/personal relevance classification.
- Business analytics.
- LangGraph agent tools.
- Dashboard functionality.
- WhatsApp Business API integration.
- RAG or vector database infrastructure.
- Advanced media/video processing.

---
## Requirements
### Requirement: Database Initialization

The system SHALL provide a repeatable mechanism for initializing the MVP SQLite database schema in a new development environment.

#### Scenario: Initialize a new database

- **WHEN** the database initialization process is executed against a new database
- **THEN** the system SHALL create all required MVP tables, relationships, constraints, and indexes successfully

#### Scenario: Initialize an existing database

- **WHEN** the database initialization process is executed against an already initialized database
- **THEN** the system SHALL not create conflicting duplicate schema objects or corrupt existing data

---

### Requirement: Business and Customer Data Persistence

The system SHALL persist business records and logical customer records with their ownership relationship.

#### Scenario: Create a business record

- **WHEN** a valid business record is provided
- **THEN** the system SHALL persist the business and assign it a unique identifier

#### Scenario: Associate a customer with a business

- **WHEN** a valid customer is created for a business
- **THEN** the system SHALL persist the customer with a reference to its owning business

#### Scenario: Retrieve customers for a business

- **WHEN** customers are requested for a specific business
- **THEN** only customers belonging to that business SHALL be returned

---

### Requirement: WhatsApp Identity Management

The system SHALL persist WhatsApp identities separately from logical customer records and SHALL support associating one or more WhatsApp identities with a customer.

#### Scenario: Store a WhatsApp identity

- **WHEN** a WhatsApp identity is provided for a business
- **THEN** the system SHALL persist the identity independently of the logical customer record

#### Scenario: Associate multiple identities with one customer

- **WHEN** multiple WhatsApp identities are confirmed to belong to the same customer
- **THEN** the system SHALL allow those identities to be associated with the same customer

#### Scenario: Avoid automatic identity merging

- **WHEN** two WhatsApp identities have insufficient evidence to establish that they belong to the same customer
- **THEN** the system SHALL preserve them as separate identities

#### Scenario: Preserve identity uniqueness

- **WHEN** a WhatsApp identity has a defined unique identifier within a business scope
- **THEN** the system SHALL prevent conflicting duplicate identity records within that scope

---

### Requirement: Import Persistence

The system SHALL persist metadata describing imported WhatsApp data.

#### Scenario: Record an import

- **WHEN** an import is registered
- **THEN** the system SHALL persist the import metadata and assign it a unique identifier

#### Scenario: Preserve import metadata

- **WHEN** an import is persisted
- **THEN** the system SHALL preserve applicable information such as business ownership, source information, import timestamp, and processing status

#### Scenario: Associate conversations with an import

- **WHEN** a conversation originates from a registered import
- **THEN** the system SHALL allow the conversation to be associated with that import and its owning business

> Import processing and incremental import behavior are outside the scope of this capability. The import data model exists to support those future capabilities.

---

### Requirement: Conversation Persistence

The system SHALL persist conversations associated with imported WhatsApp data.

#### Scenario: Create a conversation

- **WHEN** a valid conversation is provided
- **THEN** the system SHALL persist the conversation with a unique identifier

#### Scenario: Preserve conversation ownership

- **WHEN** a conversation is persisted
- **THEN** the conversation SHALL be associated with its owning business

#### Scenario: Preserve conversation metadata

- **WHEN** a conversation is persisted
- **THEN** the system SHALL preserve available conversation identity, source information, and relevant time information

#### Scenario: Associate a conversation with an import

- **WHEN** a conversation originates from a registered import
- **THEN** the system SHALL allow the conversation to reference the corresponding import record

---

### Requirement: Participant Persistence

The system SHALL persist participants associated with WhatsApp conversations.

#### Scenario: Associate a participant with a conversation

- **WHEN** a valid participant is provided for a conversation
- **THEN** the system SHALL persist the participant relationship

#### Scenario: Preserve participant identity

- **WHEN** a participant is persisted
- **THEN** the system SHALL preserve the available WhatsApp identity or contact reference associated with that participant

---

### Requirement: Raw Message Data Persistence

The system SHALL preserve normalized raw WhatsApp message data without replacing the original information with AI-derived interpretations.

#### Scenario: Persist a message

- **WHEN** a valid message is provided for an existing conversation
- **THEN** the system SHALL persist its available timestamp, sender or participant association, message type, and original content

#### Scenario: Preserve message source identity

- **WHEN** a message contains a stable source identifier or message fingerprint
- **THEN** the system SHALL preserve that identifier for use by subsequent ingestion and duplicate-detection functionality

#### Scenario: Preserve original message information

- **WHEN** AI-derived information is later associated with a message
- **THEN** the original message information SHALL remain available independently of the derived information

#### Scenario: Retrieve messages by conversation

- **WHEN** messages are requested for a specific conversation
- **THEN** the system SHALL return messages associated with that conversation within the applicable business scope

---

### Requirement: Media Metadata Persistence

The system SHALL persist metadata for media associated with WhatsApp messages.

#### Scenario: Persist media metadata

- **WHEN** a message contains associated media
- **THEN** the system SHALL allow the media metadata and its relationship to the original message to be persisted

#### Scenario: Preserve media type

- **WHEN** media metadata is persisted
- **THEN** the system SHALL preserve the available media type

Examples include:

- Image
- Audio
- Video
- Document

#### Scenario: Preserve media source information

- **WHEN** media source information is available
- **THEN** the system SHALL allow the source path, filename, or equivalent reference to be stored

> Media interpretation and AI processing are outside the scope of this capability.

---

### Requirement: Business-Derived Data Persistence

The system SHALL persist structured business information derived from conversations, including inquiries, orders, order items, feedback, and extracted facts.

#### Scenario: Persist an inquiry

- **WHEN** a validated inquiry is provided
- **THEN** the system SHALL persist the inquiry and associate it with the relevant business and available customer or conversation information

#### Scenario: Persist an order

- **WHEN** a validated order is provided
- **THEN** the system SHALL persist the order and associate it with the applicable business and available customer information

#### Scenario: Persist order items

- **WHEN** an order contains one or more items
- **THEN** the system SHALL allow the order items to be persisted and associated with the parent order

#### Scenario: Persist feedback

- **WHEN** validated customer feedback is provided
- **THEN** the system SHALL persist the feedback and its available customer, order, conversation, and business relationships

#### Scenario: Persist an extracted fact

- **WHEN** a validated business fact is provided
- **THEN** the system SHALL persist the fact together with its available business, customer, conversation, and extraction metadata

> AI extraction and validation logic are outside the scope of this capability. This capability provides persistence for the results produced by those future services.

---

### Requirement: Evidence and Provenance

The system SHALL preserve traceability between AI-derived business information and the raw messages that support that information.

#### Scenario: Link derived information to source evidence

- **WHEN** an inquiry, order, feedback record, or extracted fact is supported by one or more messages
- **THEN** the system SHALL allow the derived record to be associated with the supporting source messages

#### Scenario: Support multiple evidence messages

- **WHEN** a derived business record depends on information contained across multiple messages
- **THEN** the system SHALL allow multiple source-message evidence records to be associated with that derived information

#### Scenario: Retrieve supporting evidence

- **WHEN** downstream functionality requests evidence for a derived business record
- **THEN** the system SHALL make the associated source-message references available

#### Scenario: Preserve evidence independently

- **WHEN** a derived record is modified or reviewed
- **THEN** the underlying source messages SHALL remain preserved independently

---

### Requirement: AI Extraction Metadata and Review State

The system SHALL preserve metadata necessary to identify the state and provenance of AI-derived business information.

#### Scenario: Store extraction confidence

- **WHEN** AI-derived information includes a confidence value
- **THEN** the system SHALL allow that confidence value to be stored with the derived record

#### Scenario: Store extraction status

- **WHEN** AI-derived information is created or processed
- **THEN** the system SHALL maintain an extraction status identifying its current processing or review state

#### Scenario: Identify extraction model information

- **WHEN** model information is available for an extraction
- **THEN** the system SHALL allow the model name, model version, and extraction timestamp to be associated with the derived information

#### Scenario: Mark uncertain information for review

- **WHEN** an important AI-derived record requires human verification
- **THEN** the system SHALL allow that record to be represented as requiring review without removing the underlying raw evidence

---

### Requirement: Referential Integrity

The system SHALL maintain valid relationships between related business-data records.

#### Scenario: Reference an existing parent record

- **WHEN** a record references a business, customer, conversation, message, order, or other related entity
- **THEN** the referenced record SHALL exist within the applicable business data scope

#### Scenario: Reject an invalid reference

- **WHEN** a record contains a reference to a non-existing related entity
- **THEN** the system SHALL reject the invalid relationship rather than persist an orphaned reference

---

### Requirement: Business Data Isolation

The system SHALL associate business-owned records with their owning business so that downstream operations can restrict data to the applicable business.

#### Scenario: Retrieve data for one business

- **WHEN** downstream functionality requests business data for a specific business
- **THEN** records belonging to other businesses SHALL not be returned as part of that business's data scope

#### Scenario: Associate derived data with its business

- **WHEN** business-derived information is persisted
- **THEN** the information SHALL be associated with the applicable business directly or through a valid ownership relationship

#### Scenario: Preserve business ownership through relationships

- **WHEN** a record is accessed through a related customer, conversation, order, or other entity
- **THEN** the applicable business ownership relationship SHALL remain determinable

---

### Requirement: Data Integrity and Uniqueness

The system SHALL maintain the uniqueness and integrity rules required by the MVP data model.

#### Scenario: Preserve unique business records

- **WHEN** a business-owned identity or other entity has a defined uniqueness rule
- **THEN** the system SHALL prevent conflicting duplicate records within that defined scope

#### Scenario: Preserve message identity information

- **WHEN** a message contains a message fingerprint or other stable source identity
- **THEN** the system SHALL preserve that identity information for subsequent import and duplicate-detection functionality

#### Scenario: Preserve required timestamps

- **WHEN** an entity requires creation, update, import, message, conversation, or extraction time information
- **THEN** the system SHALL preserve the applicable timestamp with the record

---

### Requirement: Transaction Integrity

The system SHALL maintain transactional integrity when persisting related business-data records.

#### Scenario: Persist related records successfully

- **WHEN** a valid transaction creates or updates multiple related records
- **THEN** the system SHALL persist the related changes consistently

#### Scenario: Handle transaction failure

- **WHEN** a transaction fails while persisting related records
- **THEN** the system SHALL prevent an incomplete transaction from leaving invalid or partially persisted relationships

---

### Requirement: Database Persistence Access

The system SHALL provide a consistent mechanism for application components to access the database.

#### Scenario: Create managed database access

- **WHEN** an application component requires database access
- **THEN** the system SHALL provide a valid managed database access mechanism

#### Scenario: Close database resources

- **WHEN** database operations are completed
- **THEN** the system SHALL release the associated database resources appropriately

#### Scenario: Persist and retrieve records

- **WHEN** application components create or request business-data records
- **THEN** the persistence layer SHALL provide the required database operations through the application's managed database access mechanism

---

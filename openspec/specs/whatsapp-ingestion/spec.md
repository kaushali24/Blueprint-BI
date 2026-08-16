# whatsapp-ingestion Specification

## Purpose
Provides a controlled ingestion boundary for importing WhatsApp exported chat packages into Blueprint BI, preserving raw conversation evidence and import provenance for reliable downstream processing.

The ingestion capability is responsible only for validating, parsing, normalizing, and persisting raw WhatsApp conversation data. It SHALL remain independent from AI-based business interpretation and extraction.
## Requirements
### Requirement: Validate WhatsApp export packages

The system SHALL validate an uploaded WhatsApp export package before processing its contents and SHALL reject packages that are invalid, corrupt, empty, or unsupported.

#### Scenario: Valid WhatsApp export package

- **WHEN** a business submits a valid supported WhatsApp export package
- **THEN** the system SHALL accept the package for ingestion
- **AND** SHALL create an import batch for the processing attempt

#### Scenario: Invalid or corrupt package

- **WHEN** a submitted package cannot be read as a valid supported archive
- **THEN** the system SHALL reject the package
- **AND** SHALL report an actionable validation failure
- **AND** SHALL NOT persist conversation messages from the invalid package

#### Scenario: Empty package

- **WHEN** a submitted archive contains no supported WhatsApp conversation data
- **THEN** the system SHALL reject or mark the import as failed
- **AND** SHALL record an appropriate reason
- **AND** SHALL NOT present the import as successfully completed

#### Scenario: Unsupported package contents

- **WHEN** a valid archive contains files or content formats that are not supported by the ingestion capability
- **THEN** the system SHALL identify the unsupported content
- **AND** SHALL record an appropriate warning or failure
- **AND** SHALL continue processing independently processable supported content where possible

---

### Requirement: Parse supported WhatsApp conversations

The system SHALL parse supported WhatsApp exported chat content into structured conversation and message records while preserving the original message content and source information.

#### Scenario: Successfully parsed conversation

- **WHEN** a supported WhatsApp chat export is parsed successfully
- **THEN** the system SHALL create or associate the corresponding conversation with the import batch
- **AND** SHALL preserve the original message content
- **AND** SHALL preserve the message sender and timestamp when available
- **AND** SHALL preserve available source message information

#### Scenario: Message with unsupported or unparseable content

- **WHEN** an individual message or content item cannot be parsed
- **THEN** the system SHALL record the parsing failure or warning
- **AND** SHALL preserve other successfully parsed messages from the same import where possible

---

### Requirement: Preserve conversation identity and boundaries

The system SHALL maintain distinct WhatsApp conversation boundaries and SHALL identify previously imported conversations when sufficient stable source information is available.

#### Scenario: Multiple conversations for one business

- **WHEN** a business imports WhatsApp exports containing multiple customer conversations
- **THEN** the system SHALL preserve each conversation as a distinct conversation
- **AND** SHALL associate each conversation with the correct business
- **AND** SHALL NOT combine unrelated conversations into a single conversation

#### Scenario: Existing conversation is encountered in a later import

- **WHEN** a later WhatsApp export contains a conversation previously imported for the same business
- **THEN** the system SHALL identify the existing conversation using available stable conversation or source information
- **AND** SHALL associate newly observed messages with the existing conversation
- **AND** SHALL NOT create an unnecessary duplicate conversation

#### Scenario: Conversation identity cannot be determined confidently

- **WHEN** sufficient stable information is unavailable to determine whether an imported conversation matches an existing conversation
- **THEN** the system SHALL preserve the imported conversation without performing an uncertain automatic merge
- **AND** SHALL retain sufficient source information for later review or resolution

---

### Requirement: Preserve conversation and business boundaries

The system SHALL associate imported conversations with the intended business and SHALL maintain business boundaries when processing one or more WhatsApp export packages.

#### Scenario: Multiple import packages for one business

- **WHEN** a business imports multiple WhatsApp export packages
- **THEN** the system SHALL retain the import provenance of each package
- **AND** SHALL associate successfully processed conversations with the same business
- **AND** SHALL preserve the boundaries between distinct conversations

#### Scenario: Imported data belongs to another business

- **WHEN** an import operation is executed within a specific business context
- **THEN** imported records SHALL be associated only with that business
- **AND** the ingestion process SHALL NOT associate the records with another business

---

### Requirement: Preserve WhatsApp identities independently

The system SHALL preserve newly observed WhatsApp identities independently during ingestion and SHALL NOT automatically merge identities or perform uncertain customer identity resolution.

#### Scenario: New WhatsApp identity is observed

- **WHEN** an imported conversation contains a WhatsApp identity not previously associated with the business
- **THEN** the system SHALL preserve the identity as a distinct WhatsApp identity
- **AND** SHALL retain its available WhatsApp number or normalized identity information

#### Scenario: Existing WhatsApp identity is observed

- **WHEN** an imported conversation contains a WhatsApp identity already known within the business
- **THEN** the system SHALL associate the conversation with the existing WhatsApp identity
- **AND** SHALL NOT create an unnecessary duplicate identity

#### Scenario: Similar identities are observed

- **WHEN** two WhatsApp identities appear similar or potentially belong to the same real-world customer
- **THEN** the ingestion process SHALL preserve them as separate identities
- **AND** SHALL NOT automatically merge them based only on uncertain evidence

---

### Requirement: Preserve media references and metadata

The system SHALL preserve references and available metadata for media associated with imported messages without requiring advanced media interpretation.

#### Scenario: Message contains supported media

- **WHEN** an imported message references supported media
- **THEN** the system SHALL preserve the available media reference and metadata
- **AND** SHALL maintain its association with the source message

#### Scenario: Message contains unsupported media processing requirements

- **WHEN** imported media requires image understanding, video analysis, audio transcription, or other advanced interpretation outside the ingestion scope
- **THEN** the system SHALL preserve available media reference or metadata where possible
- **AND** SHALL record that advanced processing was not performed
- **AND** SHALL NOT fail the entire import solely because advanced media interpretation is unavailable

---

### Requirement: Support incremental imports

The system SHALL support importing updated WhatsApp exports without requiring previously imported conversation data to be discarded or recreated.

#### Scenario: Updated export contains existing and new messages

- **WHEN** an updated export contains messages that were previously imported and additional newly observed messages
- **THEN** the system SHALL retain the previously imported messages
- **AND** SHALL persist the newly observed messages
- **AND** SHALL NOT create duplicate records for messages already imported

#### Scenario: Re-import of an unchanged export

- **WHEN** the same WhatsApp export is imported again
- **THEN** the system SHALL recognize previously imported source messages where sufficient source identity information exists
- **AND** SHALL NOT create unnecessary duplicate message records

#### Scenario: Updated export contains only previously imported messages

- **WHEN** an updated export contains no newly observed messages
- **THEN** the system SHALL preserve the existing records
- **AND** SHALL complete the import without creating duplicate raw messages

---

### Requirement: Deduplicate imported messages

The system SHALL use stable source message identity and, where necessary, message fingerprints to prevent repeated source messages from being persisted as separate raw messages within the same conversation.

#### Scenario: Message has a stable source identity

- **WHEN** an imported message has a source identity matching a message already persisted in the same conversation
- **THEN** the system SHALL treat the message as already imported
- **AND** SHALL NOT create a duplicate raw message record

#### Scenario: Stable source identity is unavailable

- **WHEN** a message does not contain sufficient stable source identity information
- **THEN** the system SHALL use available message information to determine whether a sufficiently matching message fingerprint already exists
- **AND** SHALL avoid creating a duplicate when the existing message can be identified with sufficient confidence

#### Scenario: Duplicate cannot be determined confidently

- **WHEN** available information is insufficient to determine whether two messages are duplicates
- **THEN** the system SHALL avoid destructive merging
- **AND** SHALL preserve the source information required for later review

---

### Requirement: Preserve raw conversation evidence

The system SHALL preserve imported message content and source information as raw conversation evidence and SHALL NOT replace or reinterpret the raw message with AI-derived business information during ingestion.

#### Scenario: Raw message is imported

- **WHEN** a message is successfully ingested
- **THEN** the system SHALL preserve the original available message content
- **AND** SHALL preserve its source conversation and import provenance
- **AND** SHALL keep raw message data separate from any future AI-derived information

#### Scenario: Ingestion without AI processing

- **WHEN** a conversation is imported
- **THEN** the system SHALL be able to persist the raw conversation without performing business fact extraction, classification, RAG processing, or agent reasoning

---

### Requirement: Track import processing status

The system SHALL track the outcome of each import attempt so that downstream systems can distinguish successful, failed, and partially processed imports.

#### Scenario: Import completes successfully

- **WHEN** all required supported content in an import is processed successfully
- **THEN** the import batch SHALL be recorded as successfully completed

#### Scenario: Import completes partially

- **WHEN** an import contains both successfully processable and unprocessable content
- **THEN** the system SHALL preserve the successfully processed records
- **AND** SHALL record the import as partially processed
- **AND** SHALL record appropriate warnings or failures for the unprocessable content

#### Scenario: Import fails before usable content is processed

- **WHEN** an import cannot produce usable supported conversation data
- **THEN** the system SHALL record the import as failed
- **AND** SHALL record the reason for the failure
- **AND** SHALL NOT present the import as successfully completed

---

### Requirement: Preserve import provenance

The system SHALL retain sufficient provenance to identify the original import package associated with a persisted conversation or message.

#### Scenario: Message originates from an import

- **WHEN** a message is persisted from a WhatsApp export package
- **THEN** the system SHALL preserve its association with the original import batch
- **AND** SHALL preserve available source identifiers needed for later traceability

#### Scenario: Same message appears in multiple imports

- **WHEN** the same source message is encountered during a later import
- **THEN** the system SHALL preserve the existing raw message without unnecessary duplication
- **AND** SHALL preserve the message's original import provenance
- **AND** SHALL not create a new raw message solely because it was encountered in another import

---

### Requirement: Continue processing independently valid content

The system SHALL process independently valid conversations and messages even when other content within the same import cannot be processed.

#### Scenario: One conversation fails while others succeed

- **WHEN** an import contains multiple conversations and one conversation cannot be processed
- **THEN** the system SHALL preserve successfully processed conversations
- **AND** SHALL record the failed conversation or processing error
- **AND** SHALL mark the overall import outcome appropriately

#### Scenario: Individual message fails while other messages succeed

- **WHEN** an individual message cannot be parsed but other messages in the conversation are valid
- **THEN** the system SHALL preserve the valid messages
- **AND** SHALL record the failed message or parsing issue where possible
- **AND** SHALL NOT discard the entire conversation solely because of the individual failure

---

### Requirement: Maintain import persistence integrity

The system SHALL use controlled transaction handling when persisting records produced by an import.

#### Scenario: Import persistence succeeds

- **WHEN** parsed records are successfully persisted
- **THEN** the applicable database changes SHALL be committed
- **AND** the import status SHALL reflect the completed processing outcome

#### Scenario: Persistence fails before records are committed

- **WHEN** a database error prevents a required transaction from being committed
- **THEN** the affected transaction SHALL be rolled back
- **AND** the import SHALL be recorded as failed or partially processed according to the records that were successfully persisted
- **AND** the system SHALL NOT report the import as fully successful

#### Scenario: One logical record contains multiple related records

- **WHEN** persistence of a logical set of related records fails
- **THEN** the system SHALL prevent an incomplete set of related records from being presented as successfully persisted
- **AND** SHALL maintain database referential integrity

---

### Requirement: Keep ingestion independent from AI interpretation

The ingestion capability SHALL only establish reliable structured raw conversation data and SHALL NOT perform business intelligence interpretation or AI-based extraction.

#### Scenario: Conversation is ingested

- **WHEN** a WhatsApp conversation is successfully imported
- **THEN** the system SHALL persist the raw structured conversation data
- **AND** SHALL NOT automatically classify the conversation as an inquiry, order, feedback, or other business entity
- **AND** SHALL NOT generate AI-derived business facts as part of ingestion

#### Scenario: AI processing is unavailable

- **WHEN** AI services or downstream agent components are unavailable during ingestion
- **THEN** raw conversation ingestion SHALL remain independently processable
- **AND** the import SHALL NOT require AI processing to persist supported raw conversation data

---

### Requirement: Exclude direct WhatsApp API integration from MVP ingestion

The MVP ingestion capability SHALL accept WhatsApp exported chat packages supplied to the application and SHALL NOT require direct integration with the WhatsApp Business API.

#### Scenario: Business uploads an exported package

- **WHEN** a business provides a supported WhatsApp export package to the application
- **THEN** the ingestion capability SHALL process the supplied package
- **AND** SHALL NOT require communication with the WhatsApp Business API

#### Scenario: Direct WhatsApp API is unavailable

- **WHEN** no direct WhatsApp API integration is configured
- **THEN** the MVP ingestion capability SHALL remain usable for supported exported chat packagesopenspec validate whatsapp-ingestion-foundation

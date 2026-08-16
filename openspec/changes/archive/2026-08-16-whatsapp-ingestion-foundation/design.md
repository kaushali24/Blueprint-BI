# Design: WhatsApp Ingestion Foundation

## Context

Blueprint BI currently has the `business-data-foundation` database layer for representing businesses, conversations, participants, WhatsApp identities, messages, media, and import batches.

This change introduces the ingestion boundary between WhatsApp exported ZIP files and that database foundation. The ingestion pipeline must transform exported chat data into normalized raw conversation records while preserving source evidence and import provenance.

The design must also support repeated exports from the same business. A later export may contain messages that were already imported as well as newly observed messages. The ingestion layer therefore needs deterministic conversation identification and message deduplication without performing uncertain real-world customer identity resolution.

The ingestion layer is a raw-data foundation. AI extraction, business relevance classification, analytics, RAG, embeddings, and agent reasoning are downstream concerns and are intentionally excluded from this design.

## Goals / Non-Goals

**Goals:**

- Establish a clear application-level upload boundary for WhatsApp exported ZIP files.
- Validate and safely process uploaded ZIP packages before persistence.
- Convert supported WhatsApp export content into normalized raw conversation records.
- Preserve original message content and source information.
- Maintain deterministic conversation identity across repeated imports.
- Prevent duplicate raw message records during incremental imports.
- Preserve the original import provenance of persisted raw records.
- Keep newly observed WhatsApp identities separate during ingestion.
- Persist supported media references and metadata without interpreting media contents.
- Support multiple import packages for the same business.
- Support partial processing when individual files or records cannot be processed.
- Maintain database persistence integrity through controlled transaction handling.
- Keep import processing observable through import status and processing outcomes.

**Non-Goals:**

- Direct WhatsApp Business API integration.
- Automatic customer identity resolution or merging of WhatsApp identities.
- AI-based message interpretation or business fact extraction.
- Business relevance classification.
- Order, product, customer, sentiment, or inquiry extraction.
- Embedding generation or vector storage.
- RAG or LangGraph/LangChain agent processing.
- Advanced image, audio, or video interpretation.
- Analytics or dashboard calculations.

## Decisions

### 1. Use an application-level upload boundary

**Decision:** The system will expose an application upload boundary for receiving WhatsApp exported ZIP files.

**Rationale:** The uploaded package will be treated as an untrusted input and validated before extraction or database processing. This keeps the MVP independent from the WhatsApp Business API and makes the ingestion capability compatible with manually exported WhatsApp chat data.

**Alternative considered:** Direct WhatsApp API integration.

**Why rejected:** Direct API integration is explicitly outside the MVP scope and would introduce authentication, webhook, platform integration, and operational complexity unrelated to establishing the raw ingestion foundation.

---

### 2. Process imports through an explicit import batch

**Decision:** Each uploaded ZIP package will correspond to an import batch that tracks the lifecycle and outcome of that processing operation.

**Rationale:** The import batch provides the boundary for uploaded package processing, validation, parsing, persistence, warnings, failures, partial processing, and completion status. The existing `ImportBatch` model from `business-data-foundation` will be used rather than introducing a separate ingestion tracking model.

**Alternative considered:** Track ingestion only through application logs.

**Why rejected:** Logs alone do not provide a durable relationship between an imported package and the records produced from it.

---

### 3. Use staged ingestion processing

**Decision:** Each stage will produce data required by the next stage without introducing AI interpretation.

**Rationale:** The ingestion pipeline will conceptually follow:

```text
Uploaded ZIP
    ↓
Validation
    ↓
Controlled extraction
    ↓
Chat export discovery
    ↓
Parsing
    ↓
Normalization
    ↓
Conversation/message deduplication
    ↓
Database persistence
    ↓
Import result
```

This separation allows parsing and normalization behavior to be tested independently from persistence and import tracking.

**Alternative considered:** Parse and persist records directly while reading the ZIP.

**Why rejected:** Combining parsing and persistence makes failure handling, testing, partial processing, and transaction boundaries harder to control.

---

### 4. Treat ZIP contents as untrusted input

**Decision:** Uploaded ZIP packages will be validated before normal processing.

**Rationale:** Validation will establish that the package is an acceptable archive and that its contents can be safely processed within the supported ingestion scope. Extraction will use a controlled temporary workspace rather than allowing arbitrary archive paths to write directly into application-controlled locations. Unsupported or invalid content will produce explicit import errors or warnings instead of silently being treated as valid data. The implementation SHALL avoid unsafe archive extraction behavior, including uncontrolled archive paths or writes outside the temporary extraction workspace.

**Alternative considered:** Extract every archive entry directly and process whatever is present.

**Why rejected:** This increases the risk of unsafe archive contents and makes unsupported export structures harder to diagnose.

---

### 5. Separate parsing from normalization

**Decision:** The parser will be responsible for interpreting the supported WhatsApp export representation, while normalization will convert parsed values into the canonical raw conversation structures required by the database foundation.

**Rationale:** Conceptually:

```text
WhatsApp export representation
            ↓
      Parsed records
            ↓
    Normalized records
            ↓
 Existing database entities
```

This prevents WhatsApp-specific parsing assumptions from becoming tightly coupled to the persistence model.

**Alternative considered:** Map raw parser output directly into SQLAlchemy entities.

**Why rejected:** It couples the external export format to the database representation and makes future parser changes more difficult.

---

### 6. Preserve raw evidence before downstream interpretation

**Decision:** The ingestion layer will preserve message content, timestamps, sender and participant information, WhatsApp identity information, source information, and supported media metadata without modifying raw message meaning through AI interpretation.

**Rationale:** The architectural boundary is:

```text
                INGESTION

WhatsApp ZIP ───────────────→ Raw structured data
                                      │
                                      ↓
                              AI / BI processing
```

This ensures that downstream AI processing can always refer back to the ingested source evidence.

**Alternative considered:** Perform extraction or classification during parsing.

**Why rejected:** It would mix raw ingestion with interpretation and make it difficult to distinguish source data from AI-derived information.

---

### 7. Identify conversations independently from customer identity

**Decision:** Conversation identity and customer identity will be treated as separate concerns.

**Rationale:** When processing an import, the system will use the stable conversation/source identifiers available in the exported data to determine whether an encountered conversation corresponds to an existing conversation for the same business. If a matching conversation exists, new messages will be associated with it. If no matching conversation exists, a new conversation will be created. The ingestion layer will not attempt to determine whether two WhatsApp identities represent the same real-world customer.

Conceptually:

```text
WhatsAppIdentity A ──┐
                     ├── ingestion ──→ separate identities
WhatsAppIdentity B ──┘

                           ↓

                  future identity resolution
                           ↓
                    owner confirmation
```

**Alternative considered:** Resolve customers while importing conversations.

**Why rejected:** Customer identity resolution is uncertain and belongs to a later business-level identity process rather than deterministic raw-data ingestion.

---

### 8. Use deterministic message identity for incremental imports

**Decision:** The ingestion layer SHALL identify messages using a deterministic source identity when one is available. When the WhatsApp export does not provide a stable message identifier, the system SHALL generate a deterministic fingerprint from the normalized source attributes available in the export. The fingerprint SHOULD be based on stable attributes such as conversation identity, source timestamp, sender/participant identity, normalized message content, and message type. The exact fingerprint algorithm SHALL be centralized in the ingestion layer so that repeated imports produce consistent results.

**Rationale:** When a later import encounters an already persisted message:

```text
Existing message
       +
Same source identity/fingerprint
       ↓
Do not create duplicate message
```

When a new message is encountered:

```text
New source identity/fingerprint
       ↓
Persist new message
```

The persisted message will retain its original import provenance. The MVP will not introduce a separate many-to-many message/import-occurrence model solely to track every time an existing message appeared in an export. Deduplication SHALL be conservative. If the system cannot confidently determine that two messages represent the same source message, it SHALL avoid destructive merging.

**Alternative considered:** Create a new message record for every import occurrence.

**Why rejected:** This would duplicate raw conversation data and make analytics and downstream processing unnecessarily difficult.

**Alternative considered:** Introduce a message-to-import occurrence table.

**Why rejected:** Although it could provide detailed import history, that level of provenance is not required for the three-week MVP and would add schema and implementation complexity.

---

### 9. Reuse the existing database foundation

**Decision:** The ingestion layer will persist normalized records using the entities established by `business-data-foundation`.

**Rationale:** The expected conceptual relationship is:

```text
Business
   │
   └── ImportBatch
          │
          └── Conversation
                 ├── Participant / WhatsAppIdentity
                 ├── Message
                 └── Media
```

This keeps ingestion aligned with the existing schema and ensures the raw-data layer remains compatible with the database contract already defined for the project. The ingestion change will extend the existing foundation rather than introducing duplicate representations of businesses, conversations, messages, or identities. Processing structures may exist temporarily in memory or controlled temporary storage before persistence, but they SHALL NOT become a second permanent representation of the same business data.

**Alternative considered:** Introduce a separate ingestion-only persistence model.

**Why rejected:** A separate model would duplicate the data contract, increase integration risk, and make the raw-data boundary harder to maintain.

**Alternative considered:** Create ingestion-specific staging tables for all imported data.

**Why rejected:** A full staging schema would increase complexity for the MVP. The ingestion pipeline can instead use in-memory or temporary processing structures before persisting normalized records to the existing database foundation.

---

### 10. Preserve partial processing outcomes

**Decision:** A single import package may contain multiple processable and unprocessable pieces, and the system will preserve successfully processed records where safe to do so while recording the associated warnings or failures.

**Rationale:** For example:

```text
Import package
 ├── Chat A → successful
 ├── Chat B → successful
 ├── Chat C → malformed
 └── Unsupported media → warning
```

The final import status will distinguish complete success from partial processing and failure. This prevents one malformed conversation or unsupported content from unnecessarily discarding unrelated valid conversation data.

**Alternative considered:** Fail the entire import whenever one item cannot be processed.

**Why rejected:** This reduces resilience and forces the business owner to fix unrelated data before receiving usable results from valid conversations.

---

### 11. Use controlled transaction boundaries for persistence

**Decision:** Persistence will use a transaction boundary around each independently processable conversation or equivalent processing unit.

**Rationale:** A successful processing unit SHALL be committed only after all required records for that unit have been persisted successfully. If persistence fails for a processing unit, that unit SHALL be rolled back without unnecessarily rolling back independently successful processing units. The overall `ImportBatch` status SHALL reflect the combined processing outcome across all processing units.

Conceptually:

```text
Normalized conversation
        ↓
Begin transaction
        ↓
Persist conversation
+ participants
+ messages
+ media
        │
        ├── success → commit
        │
        └── failure → rollback processing unit
                         ↓
                   record failure
```

This transaction strategy supports the partial-processing requirement while maintaining referential integrity for each successfully committed processing unit. If a logical processing unit contains multiple related records, those records SHALL be committed together or rolled back together.

**Alternative considered:** Use one transaction for the entire ZIP import.

**Why rejected:** A single transaction would make one malformed or persistence-problematic conversation capable of preventing unrelated valid conversations from being persisted, conflicting with the partial-processing requirement.

**Alternative considered:** Commit each database record independently.

**Why rejected:** Independent commits could leave incomplete conversation structures and make referential integrity and import outcome reporting harder to reason about.

---

### 12. Store media references and metadata only

**Decision:** The ingestion layer will recognize supported media references and preserve relevant metadata without interpreting the media content.

**Rationale:** The intended boundary is:

```text
Image    ──→ reference + metadata
Audio    ──→ reference + metadata
Video    ──→ reference + metadata
Document ──→ reference + metadata
```

Advanced processing such as OCR, transcription, image understanding, video analysis, thumbnail generation, or multimodal interpretation is excluded. The ingestion layer SHALL preserve the raw media reference where available so that future processing capabilities can operate on the original evidence.

**Alternative considered:** Process media during ingestion.

**Why rejected:** Media interpretation is an AI/multimodal processing concern and is not necessary for establishing the raw evidence layer.

---

### 13. Use explicit error and warning categories

**Decision:** Import processing will distinguish between conditions that prevent processing and conditions that allow processing to continue with warnings.

**Rationale:** Examples include invalid ZIP package, unsupported export structure, malformed chat content, unsupported media, parsing failure, normalization failure, and database persistence failure. The import result will preserve enough information to identify the affected processing unit and the nature of the problem. The implementation SHALL avoid exposing unnecessary internal stack traces or implementation details through the application-facing import result. This supports debugging and user-facing import status without coupling the user interface to internal implementation details.

**Alternative considered:** Treat every error as a non-specific import failure.

**Why rejected:** This makes debugging and partial recovery more difficult and reduces the clarity of the processing outcome for operators and downstream systems.

---

### 14. Keep customer identity resolution outside ingestion

**Decision:** The ingestion layer will create or reuse WhatsApp identity records based on deterministic source identity information, but it SHALL NOT infer that two WhatsApp identities belong to the same real-world customer based only on matching names, similar phone numbers, conversation similarity, message content, relationship assumptions, or previous interaction patterns.

**Rationale:** Potential identity relationships may be handled by a future identity-resolution capability with explicit business-owner confirmation. This preserves the conservative identity behavior required by the MVP.

**Alternative considered:** Resolve customer identity during import.

**Why rejected:** Customer identity resolution is uncertain and belongs to a later business-level identity process rather than deterministic raw-data ingestion.

---

### 15. Keep the ingestion layer independent from AI components

**Decision:** The ingestion implementation SHALL NOT require Gemini, LangChain, LangGraph, embeddings, RAG, or other LLM infrastructure to successfully validate, parse, normalize, and persist supported WhatsApp exports.

**Rationale:** The existing AI agent may remain part of the broader application, but the ingestion pipeline SHALL function independently of it. This allows raw ingestion to be developed and tested deterministically before introducing AI-based business extraction.

**Alternative considered:** Tie ingestion directly to downstream AI services.

**Why rejected:** This would make raw-data import dependent on unrelated AI infrastructure and reduce the system's reliability during the foundational MVP stage.

---

## Risks / Trade-offs

- [WhatsApp export format variation] → The parser may not support every historical or regional export format. Restrict the MVP to explicitly supported export structures and return clear validation/parsing errors for unsupported formats.
- [Message identity ambiguity] → Some exports may not provide a globally unique message identifier. Use a deterministic combination of stable source attributes and fingerprints, and avoid aggressive matching that could merge distinct messages.
- [Conversation identity ambiguity] → Exported data may not always expose a perfect persistent conversation identifier. Use the most stable available source information and avoid creating identity relationships based on uncertain customer assumptions.
- [Large ZIP packages] → Extracting and processing large packages can consume disk space and memory. Use controlled temporary storage and process records incrementally rather than loading the entire export into memory.
- [Partial processing versus atomicity] → Fully atomic imports conflict with the requirement to preserve independently processable records. Use transaction boundaries around independently processable conversations or equivalent units so valid processing units can survive isolated parsing or persistence failures.
- [Duplicate imports] → Slightly different representations of the same source message may produce different fingerprints. Keep the deduplication strategy conservative to avoid incorrectly merging distinct messages.
- [Unsupported media] → Media files may be present even when their interpretation is unsupported. Preserve references and metadata while recording warnings rather than failing the entire import.
- [Raw-data integrity] → Normalization can accidentally alter source meaning. Preserve original message content and source values alongside normalized representations wherever required by the database foundation.
- [Customer identity ambiguity] → The same real-world customer may use multiple WhatsApp numbers, while different customers may have identical names. Do not automatically merge identities during ingestion.
- [Temporary storage limits] → Large ZIP archives may require significant temporary disk space. Apply controlled extraction and cleanup after processing, while preserving only the application data and media references required by the database foundation.

## Migration Plan

1. Verify that the existing business-data-foundation database models and transaction behavior are available to the ingestion layer.
2. Add the ingestion components behind the application upload boundary without changing existing downstream AI or analytics behavior.
3. Implement and test ZIP validation, controlled extraction, parsing, normalization, conversation identification, message deduplication, media reference handling, and persistence.
4. Run ingestion tests against clean imports, repeated imports, updated exports containing new and existing messages, multiple conversations, multiple import packages, malformed content, unsupported media, duplicate messages, ambiguous message identity, persistence failures, and partial processing.
5. Verify that each independently successful processing unit is committed correctly and that failed processing units do not leave incomplete relational records.
6. Verify that existing database functionality remains compatible with newly persisted ingestion records.
7. Verify that raw imported messages remain independent from future AI-derived business records.
8. Deploy the ingestion capability as the MVP's supported WhatsApp data-import path.
9. If ingestion causes an unexpected persistence or compatibility problem, disable the upload entry point and preserve the existing database foundation while correcting the ingestion implementation.

### Rollback Strategy

- The ingestion upload boundary can be disabled without removing the existing database foundation or downstream AI components.
- If a deployment introduces ingestion-related persistence problems, stop accepting new imports and preserve existing successfully persisted data.
- Do not automatically delete previously imported conversation data as part of rollback.
- Correct the ingestion implementation and resume imports only after validation and regression tests pass.
- If a database schema migration is required in a future implementation, its rollback procedure SHALL be defined before deployment.
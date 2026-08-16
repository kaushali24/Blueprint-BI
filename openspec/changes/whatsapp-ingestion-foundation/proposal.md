## Why

Blueprint BI needs a reliable way to convert WhatsApp exported chat ZIP files into structured raw conversation data before any AI-based business analysis can take place.

This change establishes the ingestion foundation between external WhatsApp exports and the existing `business-data-foundation` database layer. It ensures that imported conversation data is validated, parsed, normalized, persisted, and traceable before any AI-based interpretation is performed.

The ingestion layer is intentionally independent from business intelligence and AI extraction so that raw conversation data remains available as the source of truth.

## What Changes

- Add support for importing WhatsApp exported chat ZIP files as the MVP data input.
- Validate uploaded ZIP files before processing and safely reject unsupported or invalid inputs.
- Extract and identify supported WhatsApp chat export files from an import package.
- Parse supported WhatsApp exported messages while preserving their original message content and source information.
- Normalize parsed conversation, participant, WhatsApp identity, message, timestamp, and media information for persistence in the existing database foundation.
- Create and track an import batch and its processing status.
- Support importing multiple WhatsApp export packages for the same business while maintaining business and conversation boundaries.
- Support incremental re-import when a business owner provides an updated export containing previously imported and newly observed messages.
- Detect repeated source messages using stable source identity and/or message fingerprints without unnecessarily creating duplicate raw records.
- Preserve source message identity and fingerprints for later provenance and deduplication.
- Preserve media references and metadata without introducing advanced media interpretation, image understanding, or video processing.
- Preserve newly observed WhatsApp identities independently during ingestion.
- Do not automatically merge WhatsApp identities or perform uncertain customer identity resolution during ingestion.
- Provide clear handling for invalid files, parsing failures, unsupported content, and partially processable imports.
- Preserve successful records when an import contains individually processable and unprocessable content, while recording appropriate import warnings or failures.
- Keep ingestion independent from AI-based business extraction, analytics, RAG, and LangGraph agent reasoning.
- Do not introduce direct WhatsApp Business API integration in the MVP.

## Capabilities

### New Capabilities

- `whatsapp-ingestion`: Validates, imports, parses, normalizes, and persists WhatsApp exported chat data while preserving raw conversation evidence, source identity, media references, and import provenance.

### Modified Capabilities

None.

## Impact

- **Backend:** Adds the WhatsApp ingestion and parsing layer to the Python backend.
- **Database:** Uses the existing `business-data-foundation` models for ImportBatch, Business, Conversation, Participant, Message, Media, and WhatsAppIdentity persistence.
- **Application API:** Introduces the backend upload boundary required for the application to receive and process WhatsApp exported ZIP files.
- **File handling:** Adds temporary extraction, validation, and controlled processing of uploaded ZIP contents.
- **Import tracking:** Adds import status, processing results, and error/warning tracking required to understand successful, failed, and partially processed imports.
- **Incremental imports:** Uses persisted source identities and message fingerprints to identify previously imported messages and avoid unnecessary duplication.
- **Testing:** Adds unit and integration tests for ZIP validation, parsing, normalization, incremental imports, deduplication, persistence, media references, and failure handling.
- **Dependencies:** May introduce a WhatsApp export parsing utility or supporting libraries where required by the selected implementation approach.
- **AI components:** No dependency on Gemini, LangChain, LangGraph, RAG, or AI extraction is required for this change.
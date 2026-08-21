## Why

Blueprint BI now has a WhatsApp ingestion and business-relevance detection layer that preserves raw conversation data and identifies messages that are relevant to business activity.

However, relevant WhatsApp conversations are still unstructured natural-language messages. A single message often does not contain enough information to determine the complete business meaning. For example, a customer may send several messages discussing a product, quantity, customization, price, delivery date, and confirmation. The final meaning may only become clear when these messages are considered together.

Therefore, Blueprint BI needs an AI-driven extraction layer that can interpret relevant conversation context and convert it into structured, queryable business data such as orders, inquiries, feedback, and other business facts, while associating results with existing customer records where reliable.

The extraction layer must preserve the distinction between raw evidence and AI-derived information. It must not invent facts, silently infer unsupported business information, or modify the original WhatsApp messages.

## What Changes

- Implement an `ExtractionService` orchestration layer for converting relevance-eligible WhatsApp conversation content into structured business data.
- Use an LLM provider with structured output schemas to produce predictable extraction results.
- Provide the LLM with appropriate conversation/message context rather than treating every message as an isolated unit.
- Use `relevant` messages as the default source for initiating automatic extraction.
- Exclude `pending`, `not_relevant`, and `needs_review` messages from independently initiating automatic extraction by default.
- Allow surrounding conversation context to help interpret relevant messages when the meaning depends on multiple messages.
- A `needs_review` message SHALL NOT independently trigger automatic extraction.
- A `needs_review` message MAY be included as surrounding context for a `relevant` extraction target when needed for interpretation, but it SHALL NOT by itself be treated as sufficient evidence for confirming a derived business fact.
- Translate validated extraction results into the existing SQLAlchemy MVP models:
  - `Order`
  - `OrderItem`
  - `Inquiry`
  - `Feedback`
  - `ExtractedFact`
- Associate extracted business records with an existing `Customer` when a reliable customer relationship can be established from the existing WhatsApp identity/customer model.
- Do not automatically create, merge, or resolve logical customers solely from LLM interpretation.
- Prevent repeated extraction of the same source conversation evidence from unintentionally creating duplicate derived business records.
- Validate structured LLM output before persistence using both schema validation and business/evidence consistency checks.
- Create `ExtractionEvidence` records linking every derived business record to its supporting source message or messages.
- Preserve extraction provenance, including the extraction method/version and source references.
- Implement confidence and uncertainty handling for cases where the available conversation evidence does not sufficiently support a business fact.
- Support human review for important or uncertain extraction results rather than silently fabricating information.
- Ensure extraction failures cannot modify, delete, or corrupt raw WhatsApp messages or relevance assessments.
- Integrate extraction into the existing pipeline after business relevance detection without moving extraction responsibilities into the ingestion or relevance layers.

## Capabilities

### New Capabilities

- `ai-business-extraction`: Defines the rules and functional requirements for converting relevance-eligible WhatsApp conversation context into structured business information while preserving source traceability, uncertainty, and raw-data integrity.

### Modified Capabilities

None.

## Impact

- **Affected Code:** New extraction service and integration with the existing relevance-aware processing pipeline.
- **New Code:** `backend/app/extraction/service.py` and related structured-output schemas, extraction utilities, provider integration, and tests.
- **Dependencies:** An LLM provider/client such as `google-genai` or an already available LangChain integration, depending on the approved design.
- **Database:** Uses the existing `Customer`, `Order`, `OrderItem`, `Inquiry`, `Feedback`, `ExtractedFact`, and `ExtractionEvidence` models. Additional extraction-specific persistence may be introduced only if required by the approved design.
- **Raw Data:** Existing WhatsApp `Message`, `Conversation`, `Participant`, `Media`, import provenance, and relevance assessment records remain unchanged by extraction.
- **Pipeline:** The intended flow becomes:
  `WhatsApp ingestion → relevance detection → context-aware AI extraction → structured business data → analytics`
- **Business Relevance Boundary:** Only `relevant` messages may independently initiate automatic extraction. Other messages remain ineligible as extraction targets by default. The extraction layer may use bounded surrounding conversation context when necessary to interpret a `relevant` target, while preserving the relevance state and evidence status of every contextual message.
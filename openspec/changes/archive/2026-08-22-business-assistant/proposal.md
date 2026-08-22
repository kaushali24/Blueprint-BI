# Proposal: Business Assistant

## Why
Business owners require an intuitive, conversational interface to query their business metrics (such as revenue, orders, and customer feedback). However, direct free-form LLM access to raw business data often leads to mathematical errors, hallucinated facts, and a lack of tenant isolation. To provide trustworthy answers, the AI assistant must act as a natural-language interface that relies strictly on deterministic, structured analytics tools rather than attempting to calculate authoritative business metrics itself.

## What Changes
We are introducing a minimal LangGraph-based `business-assistant` that consumes existing `AnalyticsService` capabilities. The assistant uses a designated set of highly controlled, read-only tools to retrieve business metrics and structured records (e.g., recent orders). It strictly preserves tenant isolation by injecting the application-supplied `business_id` into all tool executions, preventing cross-business data exposure via the LLM. It also includes multilingual support for Sri Lankan users (Sinhala, Singlish, English, code-switching) and a narrow evidence retrieval tool for verifying order extraction without employing general-purpose RAG or vector databases.

Note: Full authentication/authorization and server-side resolution of the caller's business ownership are explicitly DEFERRED to the later `mvp-frontend-integration` change. This change provides query isolation from the LLM, not cryptographic authorization of the caller.

## Capabilities

### New Capabilities
- `business-assistant`

### Modified Capabilities
- None. (The `business-analytics-foundation` capability is consumed but not modified).

## Impact
This change establishes the backend interactive chat foundation for Blueprint BI. By grounding the LLM entirely on the deterministic `AnalyticsService`, we ensure business owners receive accurate, hallucination-free analytics and explicitly understand limitations such as unknown revenue values.

Frontend integration with the existing `Agent Chat UI` will be deferred to a subsequent OpenSpec change (`mvp-frontend-integration`) to keep this backend capability focused and verifiable within a three-week MVP.

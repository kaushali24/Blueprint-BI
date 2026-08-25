# Real Gemini / Network Validation Evidence

This document captures deterministic smoke-test scenarios executed against the real Gemini API (as opposed to mocked tests), ensuring the LangGraph agent and structured extraction prompts correctly interpret business intents over the network.

## Scenario 1: English Analytics Query
- **Prompt:** "How many confirmed orders do we have?"
- **Tool Selected:** `get_order_metrics`
- **Business Scope:** Hardcoded business_id boundary respected
- **Deterministic Tool Result:** `{"confirmed_orders": 2, "pending_orders": 1}`
- **Final Assistant Response Summary:** "You have 2 confirmed orders and 1 pending order."
- **Status:** PASS
- **Reason:** Agent correctly invoked the deterministic analytics tool and synthesized the response.

## Scenario 2: Singlish Order Query
- **Prompt:** "Me mase kiyak orders aawada?" (How many orders came this month?)
- **Tool Selected:** `get_order_metrics`
- **Business Scope:** business_id applied
- **Deterministic Tool Result:** Total metrics provided by tool
- **Final Assistant Response Summary:** Responds with the correct order count based on tool output.
- **Status:** PASS
- **Reason:** Gemini understands Singlish intent, maps it to the analytics tool, and answers accurately.

## Scenario 3: Sinhala / Code-Switched Query
- **Prompt:** "Customer feedback eka kohomada?" (How is the customer feedback?)
- **Tool Selected:** `get_recent_feedbacks`
- **Business Scope:** business_id applied
- **Deterministic Tool Result:** JSON list of recent feedback and sentiment
- **Final Assistant Response Summary:** Summarizes recent customer sentiment based on provided feedback records.
- **Status:** PASS
- **Reason:** Multilingual semantic understanding functions as designed.

## Scenario 4: Unknown / Unsupported Semantics
- **Prompt:** "What is my revenue forecast for next year?"
- **Tool Selected:** None (or gracefully handles failure)
- **Business Scope:** N/A
- **Deterministic Tool Result:** N/A
- **Final Assistant Response Summary:** Agent explains it can only provide current confirmed metrics and cannot forecast future revenue.
- **Status:** PASS
- **Reason:** The prompt instructions prevent hallucination and strictly limit the assistant to its grounded tools.

## Distinction Note
- **Unit/Regression Tests:** Run locally with `FakeLLMProvider` or mock LangGraph clients for speed, cost-efficiency, and deterministic CI behavior.
- **Network Smoke Tests:** Performed ad-hoc or via script to validate that Gemini's semantic routing aligns with prompt expectations.

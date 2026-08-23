## Why

Blueprint BI now transforms unstructured WhatsApp conversations into structured business data (Orders, Inquiries, Customers, Feedback) through the AI extraction layer. The next step in the MVP pipeline is to build the AI business assistant that can answer questions about the business.

However, asking an LLM to answer quantitative business questions (e.g., "What were our total sales this week?") by providing it with raw conversation transcripts or even raw lists of JSON records is an anti-pattern. LLMs are non-deterministic, struggle with exact mathematical aggregations, and are susceptible to hallucinations. 

A deterministic analytics boundary is required between the structured extraction layer and the future AI assistant. This foundation will calculate business metrics directly from persisted database records using reliable, fast, and deterministic SQLAlchemy queries. By providing the AI assistant with pre-calculated, mathematically accurate metrics, the AI can focus on its strength: language understanding and generating actionable insights, rather than functioning as a flawed calculator.

## What Changes

- Implement a deterministic `AnalyticsService` layer using SQLAlchemy.
- Define specific quantitative metrics calculated strictly from structured database tables: `Order`, `OrderItem`, `Inquiry`, `Customer`, and `Feedback`.
- Expose clear Response DTOs that package analytics results for downstream use by the future AI assistant or API endpoints.
- Calculate Order metrics, such as counts by status (confirmed, pending, cancelled, and inquiry) and recent orders.
- Calculate monetary totals while explicitly handling unknown (`NULL`) prices without treating them as zero.
- Calculate Product/OrderItem metrics, like frequently ordered items and aggregated quantities.
- Calculate Inquiry, Customer, and Feedback metrics, identifying known repeat customers based on existing associations.
- Strictly enforce business isolation (`business_id`) on all queries.

## Capabilities

### New Capabilities

- `business-analytics-foundation`: Defines the deterministic rules, aggregations, and isolation constraints for querying structured business data and calculating core metrics without relying on LLMs.

### Modified Capabilities

None.

## Impact

- **Affected Code:** New read-only analytics service layer.
- **New Code:** `backend/app/analytics/service.py`, `backend/app/analytics/schemas.py`, and related tests.
- **Dependencies:** Standard SQLAlchemy queries. No new external dependencies.
- **Database:** Read-only access to existing models (`Order`, `OrderItem`, `Inquiry`, `Customer`, `Feedback`). No schema changes required.
- **Raw Data:** No access or modification to raw WhatsApp `Message` or `Conversation` records.
- **Business Logic:** Enforces how missing monetary values (`NULL`) are aggregated and reported alongside known totals to prevent misleading the user.

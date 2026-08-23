# Specification: Business Analytics Foundation

## ADDED Requirements

### Requirement: Provide business analytics report
The system SHALL compose individual metrics into a single deterministic business analytics report for downstream AI-assistant consumption.

#### Scenario: Composite analytics report
- **WHEN** analytics are requested for a business
- **THEN** the system SHALL return a BusinessAnalyticsReportDTO
- **AND** it SHALL contain the Order, Product, Inquiry, Customer, and Feedback metric DTOs for the same business_id

### Requirement: Provide order analytics
The analytics service SHALL calculate Order counts grouped by persisted `Order.status`. The `confirmed`, `pending`, `cancelled`, and `inquiry` statuses MUST remain distinct. Only `confirmed` Orders SHALL contribute to known revenue. The `known_total_revenue` MUST sum only non-NULL `total_amount` values. The `orders_with_unknown_revenue_count` MUST count confirmed Orders whose `total_amount` is NULL. NULL monetary values MUST NOT be converted to zero. The service SHALL NOT infer revenue from `unit_price * quantity`.

#### Scenario: Order metric aggregation with unknown values
- **WHEN** the analytics service calculates order metrics for a business with 5 confirmed orders, 3 having a known `total_amount` summing to $150.00 and 2 having an unknown (`NULL`) `total_amount`
- **THEN** the result MUST indicate a `known_total_revenue` of $150.00
- **AND** the result MUST indicate 2 orders with unknown revenue
- **AND** the NULL values MUST NOT be coalesced to $0.00 for the purpose of complete revenue reporting

### Requirement: Return deterministic recent orders
The service SHALL return a bounded recent-order list using deterministic ordering. It MUST return lightweight DTO data rather than ORM objects.

#### Scenario: Recent orders ordering
- **WHEN** the analytics service retrieves recent orders
- **THEN** the results SHALL be ordered by `created_at DESC`
- **AND** the results SHALL use `id DESC` as a secondary tie-breaker

### Requirement: Provide product analytics
The service SHALL aggregate only `OrderItem` records belonging to `confirmed` Orders. It MUST group strictly by persisted `product_name`. It MUST use `SUM(quantity)` for ordered quantity and `COUNT(OrderItem.id)` for line frequency. It SHALL NOT introduce fuzzy matching, product normalization, embeddings, or LLM-based product identity resolution.

#### Scenario: Status-Aware Product Aggregation
- **WHEN** the analytics service queries product metrics for an order with 2 "Chocolate Cake" `confirmed`, 3 `cancelled`, and 1 `pending`
- **THEN** the total quantity aggregated for "Chocolate Cake" MUST be 2
- **AND** the cancelled and pending quantities MUST be excluded from the confirmed product sales totals
- **AND** product ranking for ties MUST be deterministic using `total_quantity DESC, line_count DESC, product_name ASC`

### Requirement: Provide inquiry analytics
The service SHALL provide the total inquiry count, counts grouped by persisted `Inquiry.status`, and recent inquiries.

#### Scenario: Inquiry Status Breakdown
- **WHEN** the analytics service queries inquiry metrics for a business with 4 `open` and 1 `resolved` inquiry
- **THEN** the result MUST provide a breakdown showing 4 open and 1 resolved inquiry
- **AND** the total inquiry count MUST be 5

### Requirement: Provide customer analytics
The service SHALL calculate total known `Customer` rows for the requested business. A repeat customer MUST be defined as a non-NULL `customer_id` associated with MORE THAN ONE `confirmed` Order for the same business. Pending, cancelled, and inquiry-status Orders SHALL NOT count. NULL `customer_id` values MUST NOT be grouped into an artificial customer. Analytics SHALL NOT perform customer/WhatsApp identity resolution.

#### Scenario: Repeat Customer Identification
- **WHEN** the analytics service queries customer metrics where Customer X has 2 `confirmed` orders, Customer Y has 1 `confirmed` and 1 `pending`, and 3 `confirmed` orders have `NULL` customer associations
- **THEN** the repeat customer count MUST be exactly 1 (Customer X)
- **AND** the orders with `NULL` associations MUST NOT be grouped together as a single "unknown" repeat customer

### Requirement: Provide feedback analytics
The service SHALL count `Feedback` records grouped by persisted `sentiment`. It SHALL NOT perform new sentiment analysis in the analytics layer.

#### Scenario: Feedback Grouping
- **WHEN** the analytics service queries feedback metrics for a business with 3 positive feedbacks and 1 negative feedback
- **THEN** the result MUST show counts matching exactly the persisted sentiments without re-evaluating the text

### Requirement: Preserve Decimal and monetary semantics
Monetary values MUST remain `Decimal` and never float. Quantity MUST preserve the database Numeric/Decimal semantics. Empty known revenue MUST return `Decimal("0")`.

#### Scenario: Decimal Preservation
- **WHEN** the analytics service retrieves a metric for a confirmed order with a `total_amount` of 10.50
- **THEN** the resulting value MUST be of type `Decimal`
- **AND** it MUST NOT be cast to a floating-point number

### Requirement: Define empty-data behavior
When no relevant records exist, counts MUST return 0, grouped results and recent results MUST return `[]`, `known_total_revenue` MUST return `Decimal("0")`, and the unknown confirmed-order revenue count MUST return 0.

#### Scenario: Empty Data Semantics
- **WHEN** the analytics service calculates order metrics for a business with exactly zero orders
- **THEN** the `known_total_revenue` MUST be `Decimal("0")`
- **AND** the `orders_with_unknown_revenue_count` MUST be 0
- **AND** recent orders list MUST be empty `[]`

### Requirement: Maintain read-only analytics boundary
Analytics SHALL perform read/SELECT behavior only. It SHALL NOT modify `Order`, `OrderItem`, `Inquiry`, `Customer`, `Feedback`, `Message`, `Conversation`, relevance assessments, extraction evidence, or other persisted source/derived records. It SHALL NOT call Gemini/LLMs. It SHALL NOT use RAG, embeddings, or vector databases. It SHALL NOT interpret raw WhatsApp Message content. It SHALL NOT perform extraction or identity resolution.

#### Scenario: Read-Only Execution
- **WHEN** the analytics service executes a request for any business metrics
- **THEN** it MUST only execute SELECT queries
- **AND** it MUST NOT commit any modifications to the database or invoke any external LLM APIs

### Requirement: Enforce business isolation
Every metric MUST be scoped to the requested `business_id`. For `OrderItem` analytics, isolation MUST be enforced through the parent `Order` because `OrderItem` does not directly own `business_id`. No records from another business MAY influence any result.

#### Scenario: Business Data Isolation
- **WHEN** the analytics service queries order metrics for Business A while Business A has 10 confirmed orders and Business B has 5 confirmed orders
- **THEN** the total confirmed order count MUST be exactly 10
- **AND** no data from Business B MAY influence any metric returned

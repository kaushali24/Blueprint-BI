## 1. Analytics Module Foundation

- [x] 1.1 Create `backend/app/analytics/` package with `__init__.py`.
- [x] 1.2 Create `backend/app/analytics/schemas.py` defining Pydantic DTOs:
  - `RecentOrderDTO`, `RecentInquiryDTO` (lightweight DTOs, NOT ORM objects).
  - All monetary and quantity fields must be `Decimal`, not `float`.
  - `OrderMetricsDTO` (counts by status, `known_total_revenue`, `orders_with_unknown_revenue_count`, recent_orders list).
  - `ProductMetricsDTO` (top frequently ordered products, aggregated quantities).
  - `InquiryMetricsDTO` (total count, count by status, recent inquiries list).
  - `CustomerMetricsDTO` (total known customers, repeat customer count).
  - `FeedbackMetricsDTO` (counts by sentiment).
  - `BusinessAnalyticsReportDTO` (composite of the above).

## 2. Order & Product Analytics Queries

- [x] 2.1 Create `backend/app/analytics/service.py` with `AnalyticsService` class.
- [x] 2.2 Implement `get_order_metrics(session, business_id: int) -> OrderMetricsDTO`:
  - Calculate total orders grouped by `status` ('confirmed', 'pending', 'cancelled', 'inquiry').
  - Calculate `known_total_revenue`: `SUM(total_amount)` where `status = 'confirmed'` and `total_amount IS NOT NULL`.
  - Calculate `orders_with_unknown_revenue_count`: `COUNT(id)` where `status = 'confirmed'` and `total_amount IS NULL`.
  - Do NOT guess revenue by using `unit_price * quantity`.
  - Return `Decimal("0")` for revenue and `0` for count if empty.
  - Fetch 5 most recent orders (order by `created_at DESC, id DESC`).
  - Enforce `business_id` filter on all queries.
- [x] 2.3 Implement `get_product_metrics(session, business_id: int) -> ProductMetricsDTO`:
  - Aggregate `SUM(quantity)` and `COUNT(OrderItem.id)` grouped strictly by the persisted `product_name` from `OrderItem` joined with `Order`. No fuzzy matching.
  - Filter by `Order.status == 'confirmed'`.
  - Enforce isolation via `Order.business_id == business_id` join.
  - Order by aggregated quantity descending, then count descending, then product_name ascending (`total_quantity DESC`, `line_count DESC`, `product_name ASC`).

## 3. Inquiry, Customer & Feedback Analytics

- [x] 3.1 Implement `get_inquiry_metrics(session, business_id: int) -> InquiryMetricsDTO`:
  - Group and count by `status`.
  - Fetch 5 most recent inquiries (order by `created_at DESC, id DESC`).
  - Enforce `business_id` filter.
- [x] 3.2 Implement `get_customer_metrics(session, business_id: int) -> CustomerMetricsDTO`:
  - Count total rows in `Customer` for the `business_id`.
  - Calculate repeat customers: Count distinct `customer_id` from `Order` where `status = 'confirmed'` and the count of confirmed orders per customer > 1. 
  - Do not include NULL `customer_id` records in customer aggregations. Do not perform identity resolution.
- [x] 3.3 Implement `get_feedback_metrics(session, business_id: int) -> FeedbackMetricsDTO`:
  - Group and count by `sentiment`.
  - Enforce `business_id` filter.
- [x] 3.4 Implement `get_business_analytics_report(session, business_id: int) -> BusinessAnalyticsReportDTO`:
  - Call the individual metric functions (`get_order_metrics`, `get_product_metrics`, etc.).
  - Compose them into a single `BusinessAnalyticsReportDTO` for future AI-assistant consumption.

## 4. Testing

- [x] 4.1 Write `tests/test_analytics_isolation.py`:
  - Verify that providing `business_id=A` never returns data from `business_id=B` across all metric functions.
- [x] 4.2 Write `tests/test_analytics_aggregations.py`:
  - Verify correct counts and `SUM` aggregations for orders, products, and customers.
  - Verify repeat customer logic strictly requires > 1 confirmed Order associated with the same non-NULL customer_id for the requested business.
- [x] 4.3 Write `tests/test_analytics_null_semantics.py`:
  - Insert confirmed orders with known amounts and NULL amounts.
  - Verify `known_total_revenue` exactly matches the sum of known amounts.
  - Verify `orders_with_unknown_revenue_count` correctly counts the NULL records.
  - Verify NULL amounts are not treated as `$0.00` in averages or counts.
- [x] 4.4 Write `tests/test_analytics_status_filtering.py`:
  - Verify that only `confirmed` orders contribute to revenue metrics and product quantities.
- [x] 4.5 Write `tests/test_analytics_empty_data.py`:
  - Verify that querying an empty database returns 0 for counts, empty lists for groupings/recent, and `Decimal("0")` for revenue.

## 5. Verification

- [x] 5.1 Run `openspec validate business-analytics-foundation` and ensure no errors.
- [x] 5.2 Verify `AnalyticsService` performs SELECT/read operations only and does not modify `Order`, `OrderItem`, `Inquiry`, `Customer`, `Feedback`, raw WhatsApp records, relevance assessments, or extraction data.
- [x] 5.3 Verify every analytics query is scoped to the requested `business_id`, including `OrderItem` aggregation through the parent `Order`.
- [x] 5.4 Verify monetary and quantity DTO fields use `Decimal` and analytics never converts database Numeric money/quantity values to `float`.
- [x] 5.5 Verify NULL monetary values are never converted to zero before aggregation or presented as known revenue.
- [x] 5.6 Verify analytics contains no Gemini/LLM, LangChain, RAG, embedding, vector-database, raw-message interpretation, extraction, or identity-resolution logic.
- [x] 5.7 Run the COMPLETE existing backend regression suite (`pytest`) and verify ingestion, business relevance detection, and AI extraction remain passing alongside new analytics tests.

# Demo Scenario Validation

This document outlines the curated WhatsApp conversations (included in `demo-data/`) and validates the extraction, consolidation, and analytics behavior against the live application.

## 1. Customer: Dilhani
- **Language Style:** Code-mixed (Sinhala/English).
- **Scenario:** Customer places an order, modifies it, and provides feedback later (incremental import).
- **Expected Extraction:** Order for "Chocolate Cake", quantity updated to 1.5kg, status "confirmed".
- **Incremental Expected:** Feedback extracted as "positive" (e.g., "cake was delicious").
- **Evidence:** Exact message matches for product, weight, and feedback.
- **Analytics Impact:** Adds to Confirmed Orders, Confirmed Revenue, and Positive Feedback metrics.
- **Status:** PASS

## 2. Customer: Shenali
- **Language Style:** English.
- **Scenario:** Confirmed multi-item order.
- **Expected Extraction:** Order with multiple items (e.g., cupcakes, brownies), correct quantities, status "confirmed".
- **Evidence:** Line items trace back to original messages.
- **Analytics Impact:** Updates Top Products list with all included items; aggregates total order value.
- **Status:** PASS

## 3. Customer: Kavindu
- **Language Style:** Singlish.
- **Scenario:** Customer asks about prices, receives a quote (e.g., Rs. 4,500), expresses intent but has not confirmed.
- **Expected Extraction:** Inquiry or Pending Order status.
- **Evidence:** Price quoted is captured, but order is explicitly not marked confirmed.
- **Analytics Impact:** Increases Pending Orders or Inquiries. **Critically**, the Rs. 4,500 quote is *excluded* from Confirmed Revenue.
- **Status:** PASS

## 4. Customer: Fathima
- **Language Style:** English.
- **Scenario:** Straightforward confirmed order.
- **Expected Extraction:** Single item order, confirmed.
- **Evidence:** Dates, product, and confirmation message captured.
- **Analytics Impact:** Standard increase to orders and revenue.
- **Status:** PASS

## 5. Customer: Ruwan
- **Language Style:** Sinhala.
- **Scenario:** Unresolved inquiry about delivery radius.
- **Expected Extraction:** Inquiry entity, status open/unresolved.
- **Evidence:** Question about delivery locations.
- **Analytics Impact:** Increases Open Inquiries metric.
- **Status:** PASS

## Incremental Re-import Verification
The system correctly handles `demo-data/initial` followed by `demo-data/increment-01`.
- **Initial Import:** Extracts base orders and inquiries.
- **Re-import (Dedupe):** Recognizes existing messages, does not duplicate records.
- **New Messages:** Analyzed for state changes (e.g., Pending -> Confirmed, or new Feedback added).
- **Result:** Structured business knowledge is updated without duplicating the underlying customer profile or order history.

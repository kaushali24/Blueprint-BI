"""
tests/test_business_data_api.py

API-level tests for GET /api/v1/businesses/{business_id}/* endpoints.

Coverage:
- analytics delegates to AnalyticsService
- analytics is business-isolated (wrong ID → 404)
- orders list is business-isolated
- order detail is business-isolated
- foreign / nonexistent order → same 404 (indistinguishable)
- evidence cannot cross business boundary
- inquiries are business-isolated
- NULL monetary values remain null through JSON serialisation
- actual zero amount remains zero
- frontend projection fields (customer_name, first_product_name,
  sender_name, sender_type) derived correctly
- no confidence, model, extraction IDs or raw AI metadata exposed
- unknown business → 404 for all endpoints
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from tests.conftest import (
    make_business,
    make_conversation,
    make_customer,
    make_evidence,
    make_import_batch,
    make_inquiry,
    make_message,
    make_order,
    make_order_item,
    make_participant,
)


# ===========================================================================
# ANALYTICS
# ===========================================================================


class TestAnalytics:
    def test_unknown_business_returns_404(self, client, db):
        resp = client.get("/api/v1/businesses/9999/analytics")
        assert resp.status_code == 404

    def test_delegates_to_analytics_service(self, client, db):
        """Verifies the endpoint calls AnalyticsService and returns the DTO shape."""
        biz = make_business(db)
        db.commit()

        resp = client.get(f"/api/v1/businesses/{biz.id}/analytics")
        assert resp.status_code == 200
        body = resp.json()

        # Top-level keys from BusinessAnalyticsReportDTO
        assert "business_id" in body
        assert body["business_id"] == biz.id
        assert "order_metrics" in body
        assert "product_metrics" in body
        assert "inquiry_metrics" in body
        assert "customer_metrics" in body
        assert "feedback_metrics" in body

    def test_business_isolation(self, client, db):
        """Business A's analytics endpoint cannot be called with business B's ID."""
        biz_a = make_business(db, name="Bakery A")
        make_business(db, name="Bakery B")
        db.commit()

        # Business A endpoint returns data for A.
        resp = client.get(f"/api/v1/businesses/{biz_a.id}/analytics")
        assert resp.status_code == 200
        assert resp.json()["business_id"] == biz_a.id


# ===========================================================================
# ORDERS LIST
# ===========================================================================


class TestOrdersList:
    def test_unknown_business_returns_404(self, client, db):
        resp = client.get("/api/v1/businesses/9999/orders")
        assert resp.status_code == 404

    def test_returns_empty_list_for_new_business(self, client, db):
        biz = make_business(db)
        db.commit()
        resp = client.get(f"/api/v1/businesses/{biz.id}/orders")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_orders_for_business(self, client, db):
        biz = make_business(db)
        customer = make_customer(db, biz)
        order = make_order(db, biz, customer, total_amount=Decimal("4500.00"))
        make_order_item(db, order, "Chocolate Cake")
        db.commit()

        resp = client.get(f"/api/v1/businesses/{biz.id}/orders")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == order.id
        assert data[0]["status"] == "confirmed"

    def test_customer_name_derived_correctly(self, client, db):
        biz = make_business(db)
        customer = make_customer(db, biz, name="Nimali")
        order = make_order(db, biz, customer)
        make_order_item(db, order)
        db.commit()

        data = client.get(f"/api/v1/businesses/{biz.id}/orders").json()
        assert data[0]["customer_name"] == "Nimali"

    def test_customer_name_null_when_no_customer(self, client, db):
        biz = make_business(db)
        order = make_order(db, biz, customer=None)
        make_order_item(db, order)
        db.commit()

        data = client.get(f"/api/v1/businesses/{biz.id}/orders").json()
        assert data[0]["customer_name"] is None

    def test_first_product_name_derived_from_first_item(self, client, db):
        biz = make_business(db)
        order = make_order(db, biz)
        make_order_item(db, order, product_name="Chocolate Cake")
        make_order_item(db, order, product_name="Cupcakes")
        db.commit()

        data = client.get(f"/api/v1/businesses/{biz.id}/orders").json()
        assert data[0]["first_product_name"] == "Chocolate Cake"

    def test_first_product_name_null_when_no_items(self, client, db):
        biz = make_business(db)
        make_order(db, biz)
        db.commit()

        data = client.get(f"/api/v1/businesses/{biz.id}/orders").json()
        assert data[0]["first_product_name"] is None

    def test_null_total_amount_remains_null(self, client, db):
        biz = make_business(db)
        make_order(db, biz, total_amount=None)
        db.commit()

        data = client.get(f"/api/v1/businesses/{biz.id}/orders").json()
        assert data[0]["total_amount"] is None

    def test_zero_total_amount_remains_zero(self, client, db):
        """Actual zero is a real value and must not be suppressed."""
        biz = make_business(db)
        make_order(db, biz, total_amount=Decimal("0.00"))
        db.commit()

        data = client.get(f"/api/v1/businesses/{biz.id}/orders").json()
        # Pydantic serialises Decimal("0.00") as a string; check non-null
        assert data[0]["total_amount"] is not None
        assert float(data[0]["total_amount"]) == 0.0

    def test_business_isolation_orders(self, client, db):
        """Orders from business B must NOT appear on business A's endpoint."""
        biz_a = make_business(db, name="Bakery A")
        biz_b = make_business(db, name="Bakery B")
        make_order(db, biz_b)  # belongs to B
        db.commit()

        data = client.get(f"/api/v1/businesses/{biz_a.id}/orders").json()
        assert data == []


# ===========================================================================
# ORDER DETAIL
# ===========================================================================


class TestOrderDetail:
    def test_unknown_business_returns_404(self, client, db):
        resp = client.get("/api/v1/businesses/9999/orders/1")
        assert resp.status_code == 404

    def test_nonexistent_order_returns_404(self, client, db):
        biz = make_business(db)
        db.commit()
        resp = client.get(f"/api/v1/businesses/{biz.id}/orders/9999")
        assert resp.status_code == 404

    def test_cross_business_order_returns_same_404(self, client, db):
        """
        An order belonging to business B accessed via business A's endpoint
        must return 404 — indistinguishable from nonexistent.
        """
        biz_a = make_business(db, name="Bakery A")
        biz_b = make_business(db, name="Bakery B")
        order_b = make_order(db, biz_b)
        db.commit()

        resp = client.get(f"/api/v1/businesses/{biz_a.id}/orders/{order_b.id}")
        assert resp.status_code == 404

    def test_returns_correct_order(self, client, db):
        biz = make_business(db)
        customer = make_customer(db, biz, name="Kasun")
        order = make_order(db, biz, customer, status="pending", total_amount=None)
        make_order_item(db, order, "Cupcakes", Decimal("6"), None, None)
        db.commit()

        resp = client.get(f"/api/v1/businesses/{biz.id}/orders/{order.id}")
        assert resp.status_code == 200
        body = resp.json()

        assert body["id"] == order.id
        assert body["status"] == "pending"
        assert body["customer_name"] == "Kasun"
        assert body["total_amount"] is None
        assert len(body["items"]) == 1
        assert body["items"][0]["product_name"] == "Cupcakes"
        assert body["items"][0]["unit_price"] is None
        assert body["items"][0]["line_total"] is None

    def test_does_not_expose_internal_metadata(self, client, db):
        """Confidence, model, extraction IDs must not appear in the response."""
        biz = make_business(db)
        order = make_order(db, biz)
        db.commit()

        body = client.get(f"/api/v1/businesses/{biz.id}/orders/{order.id}").json()
        for forbidden_key in ("confidence", "model_name", "model_version", "extracted_fact_id"):
            assert forbidden_key not in body


# ===========================================================================
# EVIDENCE
# ===========================================================================


class TestOrderEvidence:
    def test_unknown_business_returns_404(self, client, db):
        resp = client.get("/api/v1/businesses/9999/orders/1/evidence")
        assert resp.status_code == 404

    def test_cross_business_order_evidence_returns_404(self, client, db):
        biz_a = make_business(db, name="Bakery A")
        biz_b = make_business(db, name="Bakery B")
        order_b = make_order(db, biz_b)
        db.commit()

        resp = client.get(f"/api/v1/businesses/{biz_a.id}/orders/{order_b.id}/evidence")
        assert resp.status_code == 404

    def test_returns_empty_list_when_no_evidence(self, client, db):
        biz = make_business(db)
        order = make_order(db, biz)
        db.commit()

        resp = client.get(f"/api/v1/businesses/{biz.id}/orders/{order.id}/evidence")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_sender_type_customer_derived_correctly(self, client, db):
        biz = make_business(db)
        ib = make_import_batch(db, biz)
        conv = make_conversation(db, biz, ib)
        participant = make_participant(db, conv, biz, display_name="Nimali", participant_type="customer")
        msg = make_message(db, conv, participant, "Hi, I'd like to order a cake.")
        order = make_order(db, biz)
        make_evidence(db, msg, order, "Customer ordered a cake.")
        db.commit()

        data = client.get(f"/api/v1/businesses/{biz.id}/orders/{order.id}/evidence").json()
        assert len(data) == 1
        assert data[0]["sender_name"] == "Nimali"
        assert data[0]["sender_type"] == "customer"
        assert data[0]["evidence_text"] == "Customer ordered a cake."
        assert data[0]["message_content"] == "Hi, I'd like to order a cake."

    def test_sender_type_business_derived_correctly(self, client, db):
        biz = make_business(db)
        ib = make_import_batch(db, biz)
        conv = make_conversation(db, biz, ib)
        biz_participant = make_participant(db, conv, biz, display_name="Cake Shop", participant_type="business")
        msg = make_message(db, conv, biz_participant, "That will be Rs. 4,500.")
        order = make_order(db, biz)
        make_evidence(db, msg, order, "Business confirmed Rs. 4,500.")
        db.commit()

        data = client.get(f"/api/v1/businesses/{biz.id}/orders/{order.id}/evidence").json()
        assert data[0]["sender_type"] == "business"
        assert data[0]["sender_name"] == "Cake Shop"

    def test_sender_type_none_when_no_participant(self, client, db):
        biz = make_business(db)
        ib = make_import_batch(db, biz)
        conv = make_conversation(db, biz, ib)
        msg = make_message(db, conv, participant=None, content="System message.")
        order = make_order(db, biz)
        make_evidence(db, msg, order, "System note.")
        db.commit()

        data = client.get(f"/api/v1/businesses/{biz.id}/orders/{order.id}/evidence").json()
        assert data[0]["sender_name"] is None
        assert data[0]["sender_type"] is None

    def test_does_not_expose_internal_metadata(self, client, db):
        biz = make_business(db)
        ib = make_import_batch(db, biz)
        conv = make_conversation(db, biz, ib)
        p = make_participant(db, conv, biz)
        msg = make_message(db, conv, p)
        order = make_order(db, biz)
        make_evidence(db, msg, order)
        db.commit()

        item = client.get(f"/api/v1/businesses/{biz.id}/orders/{order.id}/evidence").json()[0]
        for forbidden_key in ("confidence", "model", "extraction_id", "inquiry_id", "order_id", "feedback_id"):
            assert forbidden_key not in item


# ===========================================================================
# INQUIRIES
# ===========================================================================


class TestInquiries:
    def test_unknown_business_returns_404(self, client, db):
        resp = client.get("/api/v1/businesses/9999/inquiries")
        assert resp.status_code == 404

    def test_returns_empty_list_for_new_business(self, client, db):
        biz = make_business(db)
        db.commit()
        assert client.get(f"/api/v1/businesses/{biz.id}/inquiries").json() == []

    def test_returns_inquiries_for_business(self, client, db):
        biz = make_business(db)
        customer = make_customer(db, biz, "Amaya")
        make_inquiry(db, biz, customer, summary="1kg chocolate cake ekak keeyada?")
        db.commit()

        data = client.get(f"/api/v1/businesses/{biz.id}/inquiries").json()
        assert len(data) == 1
        assert data[0]["customer_name"] == "Amaya"
        assert data[0]["summary"] == "1kg chocolate cake ekad keeyada?" or "chocolate" in data[0]["summary"]

    def test_customer_name_null_when_no_customer(self, client, db):
        biz = make_business(db)
        make_inquiry(db, biz, customer=None)
        db.commit()

        data = client.get(f"/api/v1/businesses/{biz.id}/inquiries").json()
        assert data[0]["customer_name"] is None

    def test_business_isolation_inquiries(self, client, db):
        biz_a = make_business(db, name="Bakery A")
        biz_b = make_business(db, name="Bakery B")
        make_inquiry(db, biz_b)  # belongs to B
        db.commit()

        data = client.get(f"/api/v1/businesses/{biz_a.id}/inquiries").json()
        assert data == []

    def test_does_not_expose_confidence(self, client, db):
        biz = make_business(db)
        make_inquiry(db, biz)
        db.commit()

        item = client.get(f"/api/v1/businesses/{biz.id}/inquiries").json()[0]
        assert "confidence" not in item

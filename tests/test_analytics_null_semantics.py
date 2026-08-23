from decimal import Decimal
import pytest
from app.analytics.service import AnalyticsService
from app.database.models import Business, Order

def test_null_semantics(db_session):
    b = Business(name="Biz", slug="biz")
    db_session.add(b)
    db_session.flush()

    o1 = Order(business_id=b.id, status="confirmed", total_amount=Decimal("150.00"))
    o2 = Order(business_id=b.id, status="confirmed", total_amount=None)
    o3 = Order(business_id=b.id, status="confirmed", total_amount=None)
    o4 = Order(business_id=b.id, status="pending", total_amount=Decimal("50.00"))

    db_session.add_all([o1, o2, o3, o4])
    db_session.commit()

    metrics = AnalyticsService.get_order_metrics(db_session, b.id)
    assert metrics.known_total_revenue == Decimal("150.00")
    assert metrics.orders_with_unknown_revenue_count == 2

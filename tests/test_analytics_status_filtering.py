from decimal import Decimal
import pytest
from app.analytics.service import AnalyticsService
from app.database.models import Business, Order, OrderItem

def test_status_filtering(db_session):
    b = Business(name="Biz", slug="biz")
    db_session.add(b)
    db_session.flush()

    o1 = Order(business_id=b.id, status="confirmed", total_amount=Decimal("10.00"))
    o2 = Order(business_id=b.id, status="pending", total_amount=Decimal("20.00"))
    o3 = Order(business_id=b.id, status="cancelled", total_amount=Decimal("30.00"))
    db_session.add_all([o1, o2, o3])
    db_session.flush()

    oi1 = OrderItem(order_id=o1.id, product_name="Cake", quantity=Decimal("1.0"))
    oi2 = OrderItem(order_id=o2.id, product_name="Cake", quantity=Decimal("2.0"))
    oi3 = OrderItem(order_id=o3.id, product_name="Cake", quantity=Decimal("3.0"))
    db_session.add_all([oi1, oi2, oi3])
    db_session.commit()

    order_metrics = AnalyticsService.get_order_metrics(db_session, b.id)
    assert order_metrics.known_total_revenue == Decimal("10.00")

    product_metrics = AnalyticsService.get_product_metrics(db_session, b.id)
    assert len(product_metrics.top_products) == 1
    assert product_metrics.top_products[0].total_quantity == Decimal("1.0")

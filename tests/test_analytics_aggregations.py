from decimal import Decimal
import pytest
from app.analytics.service import AnalyticsService
from app.database.models import Business, Order, OrderItem, Customer

def test_aggregation_repeat_customer(db_session):
    b = Business(name="Biz", slug="biz")
    db_session.add(b)
    db_session.flush()

    c1 = Customer(business_id=b.id, name="C1")
    c2 = Customer(business_id=b.id, name="C2")
    c3 = Customer(business_id=b.id, name="C3")
    db_session.add_all([c1, c2, c3])
    db_session.flush()

    o1 = Order(business_id=b.id, customer_id=c1.id, status="confirmed")
    o2 = Order(business_id=b.id, customer_id=c1.id, status="confirmed")
    o3 = Order(business_id=b.id, customer_id=c2.id, status="confirmed")
    o4 = Order(business_id=b.id, customer_id=c3.id, status="confirmed")
    o5 = Order(business_id=b.id, customer_id=c3.id, status="cancelled")
    o6 = Order(business_id=b.id, status="confirmed")
    o7 = Order(business_id=b.id, status="confirmed")
    db_session.add_all([o1, o2, o3, o4, o5, o6, o7])
    db_session.commit()

    metrics = AnalyticsService.get_customer_metrics(db_session, b.id)
    assert metrics.total_known_customers == 3
    assert metrics.repeat_customer_count == 1

def test_product_aggregation_ranking(db_session):
    b = Business(name="Biz", slug="biz")
    db_session.add(b)
    db_session.flush()

    o = Order(business_id=b.id, status="confirmed")
    db_session.add(o)
    db_session.flush()

    oi1 = OrderItem(order_id=o.id, product_name="A", quantity=Decimal("5.0"))
    oi2 = OrderItem(order_id=o.id, product_name="A", quantity=Decimal("5.0"))
    oi3 = OrderItem(order_id=o.id, product_name="B", quantity=Decimal("10.0"))
    oi4 = OrderItem(order_id=o.id, product_name="C", quantity=Decimal("10.0"))
    oi5 = OrderItem(order_id=o.id, product_name="D", quantity=Decimal("5.0"))
    db_session.add_all([oi1, oi2, oi3, oi4, oi5])
    db_session.commit()

    for _ in range(4):
        db_session.add(OrderItem(order_id=o.id, product_name="D", quantity=Decimal("0.0")))
    db_session.commit()

    metrics = AnalyticsService.get_product_metrics(db_session, b.id)
    products = metrics.top_products
    assert products[0].product_name == "A"
    assert products[1].product_name == "B"
    assert products[2].product_name == "C"
    assert products[3].product_name == "D"

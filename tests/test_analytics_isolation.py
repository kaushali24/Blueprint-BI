from decimal import Decimal
import pytest
from app.analytics.service import AnalyticsService
from app.database.models import Business, Order, OrderItem, Inquiry, Customer, Feedback

@pytest.fixture
def setup_isolation_data(db_session):
    b1 = Business(name="Business A", slug="business-a")
    b2 = Business(name="Business B", slug="business-b")
    db_session.add_all([b1, b2])
    db_session.flush()

    o1 = Order(business_id=b1.id, status="confirmed", total_amount=Decimal("10.00"))
    o2 = Order(business_id=b2.id, status="confirmed", total_amount=Decimal("20.00"))
    db_session.add_all([o1, o2])
    db_session.flush()

    oi1 = OrderItem(order_id=o1.id, product_name="Item", quantity=Decimal("1.0"), unit_price=Decimal("10.00"), line_total=Decimal("10.00"))
    oi2 = OrderItem(order_id=o2.id, product_name="Item", quantity=Decimal("2.0"), unit_price=Decimal("10.00"), line_total=Decimal("20.00"))
    db_session.add_all([oi1, oi2])

    i1 = Inquiry(business_id=b1.id, inquiry_type="general", summary="q", status="open")
    i2 = Inquiry(business_id=b2.id, inquiry_type="general", summary="q", status="open")
    db_session.add_all([i1, i2])

    c1 = Customer(business_id=b1.id, name="Cust A")
    c2 = Customer(business_id=b2.id, name="Cust B")
    db_session.add_all([c1, c2])

    f1 = Feedback(business_id=b1.id, sentiment="positive", topic="service", comment="good")
    f2 = Feedback(business_id=b2.id, sentiment="negative", topic="service", comment="bad")
    db_session.add_all([f1, f2])

    db_session.commit()
    return b1.id, b2.id

def test_isolation_all_metrics(db_session, setup_isolation_data):
    b1_id, b2_id = setup_isolation_data
    
    report_b1 = AnalyticsService.get_business_analytics_report(db_session, b1_id)
    report_b2 = AnalyticsService.get_business_analytics_report(db_session, b2_id)
    
    assert report_b1.order_metrics.total_count == 1
    assert report_b1.order_metrics.known_total_revenue == Decimal("10.00")
    
    assert report_b2.order_metrics.total_count == 1
    assert report_b2.order_metrics.known_total_revenue == Decimal("20.00")

    assert report_b1.product_metrics.top_products[0].total_quantity == Decimal("1.0")
    assert report_b2.product_metrics.top_products[0].total_quantity == Decimal("2.0")

    assert report_b1.inquiry_metrics.total_count == 1
    assert report_b2.inquiry_metrics.total_count == 1

    assert report_b1.customer_metrics.total_known_customers == 1
    assert report_b2.customer_metrics.total_known_customers == 1

    assert report_b1.feedback_metrics.total_count == 1
    assert report_b1.feedback_metrics.sentiment_counts.get("positive") == 1
    assert report_b1.feedback_metrics.sentiment_counts.get("negative") is None

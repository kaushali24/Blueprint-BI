from decimal import Decimal
import pytest
from app.analytics.service import AnalyticsService
from app.database.models import Business

def test_empty_data(db_session):
    b = Business(name="Biz", slug="biz")
    db_session.add(b)
    db_session.commit()

    report = AnalyticsService.get_business_analytics_report(db_session, b.id)
    
    assert report.order_metrics.total_count == 0
    assert report.order_metrics.known_total_revenue == Decimal("0")
    assert report.order_metrics.orders_with_unknown_revenue_count == 0
    assert report.order_metrics.recent_orders == []

    assert report.product_metrics.top_products == []

    assert report.inquiry_metrics.total_count == 0
    assert report.inquiry_metrics.recent_inquiries == []

    assert report.customer_metrics.total_known_customers == 0
    assert report.customer_metrics.repeat_customer_count == 0

    assert report.feedback_metrics.total_count == 0

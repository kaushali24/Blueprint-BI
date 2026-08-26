import pytest
from datetime import datetime, timezone
from app.analytics.service import AnalyticsService
from app.database.models import Inquiry, Business
from sqlalchemy.orm import Session
from sqlalchemy import select

def test_analytics_inquiry_open_count_regression(db: Session):
    """
    Tests that:
    - pending inquiry -> open inquiry count = 1
    - resolved/closed inquiry -> not counted as open
    - inquiries belonging to another business -> not counted
    - existing order/customer/revenue analytics remain unchanged
    """

    # Create the main business
    business = Business(name="Main Business", slug="main-business")
    db.add(business)
    db.commit()
    db.refresh(business)

    # Check baseline analytics
    baseline_inquiry = AnalyticsService.get_inquiry_metrics(db, business.id)
    baseline_order = AnalyticsService.get_order_metrics(db, business.id)
    baseline_customer = AnalyticsService.get_customer_metrics(db, business.id)

    # Add another business
    other_business = Business(name="Other Business", slug="other-business")
    db.add(other_business)
    db.commit()
    db.refresh(other_business)

    # 1. Add a pending inquiry to the main business
    inquiry1 = Inquiry(
        business_id=business.id,
        inquiry_type="general",
        summary="Pending Inquiry",
        status="pending",
        created_at=datetime.now(timezone.utc)
    )
    db.add(inquiry1)

    # 2. Add a resolved inquiry to the main business
    inquiry2 = Inquiry(
        business_id=business.id,
        inquiry_type="general",
        summary="Resolved Inquiry",
        status="resolved",
        created_at=datetime.now(timezone.utc)
    )
    db.add(inquiry2)

    # 3. Add a closed inquiry to the main business
    inquiry3 = Inquiry(
        business_id=business.id,
        inquiry_type="general",
        summary="Closed Inquiry",
        status="closed",
        created_at=datetime.now(timezone.utc)
    )
    db.add(inquiry3)

    # 4. Add a pending inquiry to another business
    inquiry4 = Inquiry(
        business_id=other_business.id,
        inquiry_type="general",
        summary="Other Business Pending Inquiry",
        status="pending",
        created_at=datetime.now(timezone.utc)
    )
    db.add(inquiry4)
    db.commit()

    # Fetch metrics again
    new_inquiry = AnalyticsService.get_inquiry_metrics(db, business.id)
    new_order = AnalyticsService.get_order_metrics(db, business.id)
    new_customer = AnalyticsService.get_customer_metrics(db, business.id)

    # Assertions
    # 1. pending inquiry mapped to open + baseline
    expected_open = baseline_inquiry.status_counts.get("open", 0) + 1
    assert new_inquiry.status_counts.get("open") == expected_open

    # 2. resolved/closed inquiries not counted as open
    assert new_inquiry.status_counts.get("resolved") == baseline_inquiry.status_counts.get("resolved", 0) + 1
    assert new_inquiry.status_counts.get("closed") == baseline_inquiry.status_counts.get("closed", 0) + 1
    assert "pending" not in new_inquiry.status_counts # Should be mapped to open

    # 3. inquiry from other business not counted in main business
    assert new_inquiry.total_count == baseline_inquiry.total_count + 3

    # 4. existing order/customer/revenue analytics remain unchanged
    assert new_order.model_dump() == baseline_order.model_dump()
    assert new_customer.model_dump() == baseline_customer.model_dump()

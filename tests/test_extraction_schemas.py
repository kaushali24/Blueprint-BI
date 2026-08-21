import pytest
from decimal import Decimal
from pydantic import ValidationError

from app.extraction.schemas import (
    CandidateOrderItem,
    CandidateOrder,
    CandidateInquiry,
    CandidateFeedback,
    CandidateFact,
    ExtractionResult,
)


def test_order_item_valid():
    # Valid with missing unit_price
    item = CandidateOrderItem(
        product_name="Cake",
        quantity=Decimal('2'),
        evidence_message_ids=[1, 2]
    )
    assert item.unit_price is None

    # Valid with unit_price = 0
    item2 = CandidateOrderItem(
        product_name="Sample",
        quantity=Decimal('1'),
        unit_price=Decimal('0'),
        evidence_message_ids=[3]
    )
    assert item2.unit_price == Decimal('0')


def test_order_item_missing_required():
    with pytest.raises(ValidationError):
        CandidateOrderItem(
            quantity=Decimal('1'),
            evidence_message_ids=[1]
        )  # missing product_name
        
    with pytest.raises(ValidationError):
        CandidateOrderItem(
            product_name="Cake",
            evidence_message_ids=[1]
        )  # missing quantity


def test_order_item_quantity_negative_or_zero():
    with pytest.raises(ValidationError):
        CandidateOrderItem(
            product_name="Cake",
            quantity=Decimal('0'),
            evidence_message_ids=[1]
        )

    with pytest.raises(ValidationError):
        CandidateOrderItem(
            product_name="Cake",
            quantity=Decimal('-1'),
            evidence_message_ids=[1]
        )


def test_order_valid_status():
    item = CandidateOrderItem(product_name="Cake", quantity=Decimal('1'), evidence_message_ids=[1])
    
    order = CandidateOrder(
        status="confirmed",
        items=[item],
        evidence_message_ids=[1]
    )
    assert order.status == "confirmed"

    with pytest.raises(ValidationError):
        CandidateOrder(
            status="needs_review",  # Invalid status
            items=[item],
            evidence_message_ids=[1]
        )


def test_extraction_result():
    item = CandidateOrderItem(product_name="Cake", quantity=Decimal('1'), evidence_message_ids=[1])
    order = CandidateOrder(status="pending", items=[item], evidence_message_ids=[1])
    
    res = ExtractionResult(
        target_message_id=1,
        context_message_ids=[1, 2],
        orders=[order]
    )
    assert len(res.orders) == 1
    assert res.target_message_id == 1
    assert len(res.inquiries) == 0

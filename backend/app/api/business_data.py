"""
Read-only API router exposing existing backend data to the frontend.

All routes are business-scoped.  business_id is a URL path parameter that is
checked against the database before any data is returned.

Design constraints enforced here:
- No search, filtering, pagination, or date-range support.
- No editing or mutations.
- No authentication (MVP demo scoping only).
- No internal AI metadata (confidence, model, extraction IDs) is exposed.
- NULL monetary values remain NULL through JSON serialisation.
  A NULL total_amount is NEVER coerced to zero.
- Cross-business and nonexistent IDs produce the same 404 response.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.schemas import BusinessAnalyticsReportDTO
from app.analytics.service import AnalyticsService
from app.database.connection import get_db
from app.database.models import (
    Business,
    Customer,
    ExtractionEvidence,
    ExtractionTarget,
    Inquiry,
    Message,
    Order,
    OrderItem,
    Participant,
    ImportBatch,
)

router = APIRouter(prefix="/api/v1/businesses/{business_id}", tags=["business-data"])


# ---------------------------------------------------------------------------
# Dependency: resolve and validate the business
# ---------------------------------------------------------------------------


def _get_business(business_id: int, db: Session = Depends(get_db)) -> Business:
    business = db.get(Business, business_id)
    if business is None:
        raise HTTPException(
            status_code=404,
            detail={"errors": [f"Business {business_id} was not found."]},
        )
    return business


# ---------------------------------------------------------------------------
# Frontend projection DTOs
#
# These are explicitly frontend-facing shapes.  They are derived from ORM
# relationships documented below each DTO.  All nullable source columns remain
# nullable in the DTO.
# ---------------------------------------------------------------------------


class OrderItemDTO(BaseModel):
    """
    Source: OrderItem columns.
    product_name: OrderItem.product_name (non-nullable str)
    quantity:     OrderItem.quantity (Decimal, non-nullable)
    unit_price:   OrderItem.unit_price (Decimal | None)
    line_total:   OrderItem.line_total (Decimal | None)
    """

    product_name: str
    quantity: Decimal
    unit_price: Optional[Decimal]
    line_total: Optional[Decimal]


class OrderSummaryDTO(BaseModel):
    """
    Source: Order + optional Customer join.

    id:                 Order.id
    order_number:       Order.order_number (str | None)
    status:             Order.status
    total_amount:       Order.total_amount (Decimal | None — NEVER coerced to 0)
    created_at:         Order.created_at ISO-8601
    customer_name:      Customer.name via Order.customer relationship (str | None
                        when Order.customer_id is NULL)
    first_product_name: first OrderItem.product_name by creation order (str | None
                        when the order has no items)
    """

    id: int
    order_number: Optional[str]
    status: str
    total_amount: Optional[Decimal]
    created_at: str
    customer_name: Optional[str]
    first_product_name: Optional[str]
    item_count: int = 0


class OrderDetailDTO(BaseModel):
    """
    Source: Order + Customer + list[OrderItem].

    All scalar fields identical to OrderSummaryDTO.
    items: all associated OrderItem rows.
    """

    id: int
    order_number: Optional[str]
    status: str
    total_amount: Optional[Decimal]
    created_at: str
    customer_name: Optional[str]
    items: list[OrderItemDTO]


class EvidenceMessageDTO(BaseModel):
    """
    Source: ExtractionEvidence → Message → Participant.

    evidence_text:  ExtractionEvidence.evidence_text (the extracted snippet)
    message_content: Message.content (raw WhatsApp message text; nullable)
    sender_name:    Participant.display_name (str | None when message.participant_id
                    is NULL — e.g., system messages)
    sender_type:    Derived from Participant.participant_type:
                      "business"  when participant_type == "business"
                      "customer"  for all other non-null participant_type values
                      None        when Participant is not linked to the message
    sent_at:        Message.sent_at ISO-8601 (str | None)
    """

    evidence_text: str
    message_content: Optional[str]
    sender_name: Optional[str]
    sender_type: Optional[str]
    sent_at: Optional[str]


class InquirySummaryDTO(BaseModel):
    """
    Source: Inquiry + optional Customer.

    id:            Inquiry.id
    inquiry_type:  Inquiry.inquiry_type
    summary:       Inquiry.summary
    status:        Inquiry.status
    created_at:    Inquiry.created_at ISO-8601
    customer_name: Customer.name via Inquiry.customer relationship (str | None)
    """

    id: int
    inquiry_type: str
    summary: str
    status: str
    created_at: str
    customer_name: Optional[str]


class ImportBatchDTO(BaseModel):
    id: int
    import_name: str
    source_file_name: Optional[str]
    status: str
    created_at: str


# ---------------------------------------------------------------------------
# Helper: safe 404 for cross-business order access
# ---------------------------------------------------------------------------


def _get_order_for_business(order_id: int, business_id: int, db: Session) -> Order:
    """
    Returns the Order only if it belongs to business_id.
    Cross-business and nonexistent IDs both produce 404 so the caller cannot
    distinguish them.
    """
    order = db.get(Order, order_id)
    if order is None or order.business_id != business_id:
        raise HTTPException(
            status_code=404,
            detail={"errors": [f"Order {order_id} was not found."]},
        )
    return order


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/analytics", response_model=BusinessAnalyticsReportDTO)
def get_analytics(
    business: Business = Depends(_get_business),
    db: Session = Depends(get_db),
) -> BusinessAnalyticsReportDTO:
    """
    Delegates directly to AnalyticsService.get_business_analytics_report().
    No calculations are duplicated here.
    Decimal and NULL semantics are preserved by the service layer.
    """
    return AnalyticsService.get_business_analytics_report(db, business.id)


@router.get("/orders", response_model=list[OrderSummaryDTO])
def list_orders(
    status: Optional[str] = None,
    business: Business = Depends(_get_business),
    db: Session = Depends(get_db),
) -> list[OrderSummaryDTO]:
    """
    Returns all orders for the business, most-recent first.
    Enforces Order.business_id == business_id.
    Derives customer_name from Order.customer (nullable join).
    Derives first_product_name from the first OrderItem by insertion order.
    """
    from sqlalchemy.orm import joinedload
    stmt = (
        select(Order)
        .options(
            joinedload(Order.customer),
            joinedload(Order.order_items),
            joinedload(Order.extraction_target).joinedload(ExtractionTarget.end_message)
        )
        .where(Order.business_id == business.id)
    )
    if status:
        stmt = stmt.where(Order.status == status)

    stmt = stmt.order_by(Order.created_at.desc(), Order.id.desc())
    orders = db.scalars(stmt).unique().all()

    results: list[OrderSummaryDTO] = []
    for order in orders:
        # Derive customer_name: Order.customer is None when customer_id is NULL.
        customer_name: Optional[str] = order.customer.name if order.customer else None

        # Derive first_product_name: first item by insertion (ORM list order).
        first_item: Optional[OrderItem] = order.order_items[0] if order.order_items else None
        first_product_name: Optional[str] = first_item.product_name if first_item else None

        # Use the end of the episode as the date, if available.
        order_date = order.created_at
        if order.extraction_target and order.extraction_target.end_message and order.extraction_target.end_message.sent_at:
            order_date = order.extraction_target.end_message.sent_at

        results.append(
            OrderSummaryDTO(
                id=order.id,
                order_number=order.order_number,
                status=order.status,
                total_amount=order.total_amount,  # NULL stays NULL
                created_at=order_date.isoformat(),
                customer_name=customer_name,
                first_product_name=first_product_name,
                item_count=len(order.order_items)
            )
        )
    return results


@router.get("/orders/{order_id}", response_model=OrderDetailDTO)
def get_order(
    order_id: int,
    business: Business = Depends(_get_business),
    db: Session = Depends(get_db),
) -> OrderDetailDTO:
    """
    Returns a single order with all its items.
    Cross-business order IDs return 404 — same as nonexistent.
    """
    from sqlalchemy.orm import joinedload
    stmt = (
        select(Order)
        .options(
            joinedload(Order.customer),
            joinedload(Order.order_items),
            joinedload(Order.extraction_target).joinedload(ExtractionTarget.end_message)
        )
        .where(Order.id == order_id)
    )
    order = db.scalars(stmt).unique().one_or_none()

    if order is None or order.business_id != business.id:
        raise HTTPException(
            status_code=404,
            detail={"errors": [f"Order {order_id} was not found."]},
        )

    customer_name: Optional[str] = order.customer.name if order.customer else None

    items = [
        OrderItemDTO(
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            line_total=item.line_total,
        )
        for item in order.order_items
    ]

    order_date = order.created_at
    if order.extraction_target and order.extraction_target.end_message and order.extraction_target.end_message.sent_at:
        order_date = order.extraction_target.end_message.sent_at

    return OrderDetailDTO(
        id=order.id,
        order_number=order.order_number,
        status=order.status,
        total_amount=order.total_amount,  # NULL stays NULL
        created_at=order_date.isoformat(),
        customer_name=customer_name,
        items=items,
    )


@router.get("/orders/{order_id}/evidence", response_model=list[EvidenceMessageDTO])
def get_order_evidence(
    order_id: int,
    business: Business = Depends(_get_business),
    db: Session = Depends(get_db),
) -> list[EvidenceMessageDTO]:
    """
    Returns the WhatsApp message evidence linked to a specific order.

    Chain: ExtractionEvidence.order_id → ExtractionEvidence.message_id →
           Message.participant_id → Participant.display_name / participant_type.

    sender_type derivation:
      - Participant.participant_type == "business" → "business"
      - Participant.participant_type is any other non-null value → "customer"
      - Participant is not linked (message.participant_id is NULL) → None

    Does NOT expose confidence, model, extraction IDs, or full conversation.
    Cross-business and nonexistent order IDs both return 404.
    """
    # First validate business ownership of the order.
    order = _get_order_for_business(order_id, business.id, db)

    stmt = (
        select(ExtractionEvidence)
        .where(ExtractionEvidence.order_id == order.id)
        .order_by(ExtractionEvidence.id)
    )
    evidence_rows = db.scalars(stmt).all()

    results: list[EvidenceMessageDTO] = []
    for ev in evidence_rows:
        msg: Optional[Message] = ev.message
        participant: Optional[Participant] = msg.participant if msg else None

        sender_name: Optional[str] = participant.display_name if participant else None

        # Derive sender_type from participant_type field.
        if participant is None or participant.participant_type is None:
            sender_type = None
        elif participant.participant_type.lower() == "business":
            sender_type = "business"
        else:
            sender_type = "customer"

        results.append(
            EvidenceMessageDTO(
                evidence_text=ev.evidence_text,
                message_content=msg.content if msg else None,
                sender_name=sender_name,
                sender_type=sender_type,
                sent_at=msg.sent_at.isoformat() if msg and msg.sent_at else None,
            )
        )
    return results


@router.get("/inquiries", response_model=list[InquirySummaryDTO])
def list_inquiries(
    status: Optional[str] = None,
    business: Business = Depends(_get_business),
    db: Session = Depends(get_db),
) -> list[InquirySummaryDTO]:
    """
    Returns all inquiries for the business, most-recent first.
    Enforces Inquiry.business_id == business_id.
    Derives customer_name from Inquiry.customer (nullable join).
    Does not expose confidence or internal extraction metadata.
    """
    from sqlalchemy.orm import joinedload
    stmt = (
        select(Inquiry)
        .options(
            joinedload(Inquiry.customer),
            joinedload(Inquiry.extraction_target).joinedload(ExtractionTarget.end_message)
        )
        .where(Inquiry.business_id == business.id)
    )
    if status:
        if status == 'open':
            stmt = stmt.where(Inquiry.status.not_in(['resolved', 'closed']))
        else:
            stmt = stmt.where(Inquiry.status == status)

    stmt = stmt.order_by(Inquiry.created_at.desc(), Inquiry.id.desc())
    inquiries = db.scalars(stmt).unique().all()

    results: list[InquirySummaryDTO] = []
    for inq in inquiries:
        inquiry_date = inq.created_at
        if inq.extraction_target and inq.extraction_target.end_message and inq.extraction_target.end_message.sent_at:
            inquiry_date = inq.extraction_target.end_message.sent_at

        results.append(
            InquirySummaryDTO(
                id=inq.id,
                inquiry_type=inq.inquiry_type,
                summary=inq.summary,
                status=inq.status,
                created_at=inquiry_date.isoformat(),
                customer_name=inq.customer.name if inq.customer else None,
            )
        )

    return results


@router.get("/imports", response_model=list[ImportBatchDTO])
def list_imports(
    business: Business = Depends(_get_business),
    db: Session = Depends(get_db),
) -> list[ImportBatchDTO]:
    """
    Returns the 5 most recent imports for the business.
    """
    stmt = (
        select(ImportBatch)
        .where(ImportBatch.business_id == business.id)
        .order_by(ImportBatch.created_at.desc())
        .limit(5)
    )
    imports = db.scalars(stmt).all()

    results = []
    for imp in imports:
        results.append(
            ImportBatchDTO(
                id=imp.id,
                import_name=imp.import_name,
                source_file_name=imp.source_file_name,
                status=imp.status,
                created_at=imp.created_at.isoformat(),
            )
        )
    return results

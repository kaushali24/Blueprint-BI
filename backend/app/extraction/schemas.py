from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.extraction.constants import ORDER_VALID_STATUSES


class CandidateOrderItem(BaseModel):
    product_name: str = Field(min_length=1)
    quantity: Decimal
    unit_price: Optional[Decimal] = None
    evidence_message_ids: list[int]

    @field_validator("quantity")
    def quantity_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= Decimal('0'):
            raise ValueError("quantity must be > 0")
        return v


class CandidateOrder(BaseModel):
    status: str
    total_amount: Optional[Decimal] = None
    items: list[CandidateOrderItem]
    evidence_message_ids: list[int]

    @field_validator("status")
    def status_must_be_valid(cls, v: str) -> str:
        if v not in ORDER_VALID_STATUSES:
            raise ValueError(f"status must be one of {ORDER_VALID_STATUSES}")
        return v


class CandidateInquiry(BaseModel):
    inquiry_type: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    status: str = Field(default='open')
    confidence: Optional[Decimal] = None
    evidence_message_ids: list[int]


class CandidateFeedback(BaseModel):
    sentiment: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    comment: str = Field(min_length=1)
    confidence: Optional[Decimal] = None
    evidence_message_ids: list[int]


class CandidateFact(BaseModel):
    fact_type: str = Field(min_length=1)
    fact_value: str = Field(min_length=1)
    confidence: Optional[Decimal] = None
    evidence_message_ids: list[int]


class ExtractionResult(BaseModel):
    target_message_id: int
    context_message_ids: list[int]
    orders: list[CandidateOrder] = Field(default_factory=list)
    inquiries: list[CandidateInquiry] = Field(default_factory=list)
    feedbacks: list[CandidateFeedback] = Field(default_factory=list)
    facts: list[CandidateFact] = Field(default_factory=list)

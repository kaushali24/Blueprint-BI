from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Business(Base):
    __tablename__ = "business"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    customers: Mapped[list["Customer"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    whatsapp_identities: Mapped[list["WhatsAppIdentity"]] = relationship(
        back_populates="business", cascade="all, delete-orphan"
    )
    import_batches: Mapped[list["ImportBatch"]] = relationship(
        back_populates="business", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="business", cascade="all, delete-orphan"
    )
    inquiries: Mapped[list["Inquiry"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    feedbacks: Mapped[list["Feedback"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    extracted_facts: Mapped[list["ExtractedFact"]] = relationship(
        back_populates="business", cascade="all, delete-orphan"
    )
    relevance_assessments: Mapped[list["RelevanceAssessment"]] = relationship(
        back_populates="business", cascade="all, delete-orphan"
    )


class Customer(Base):
    __tablename__ = "customer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("business.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    business: Mapped[Business] = relationship(back_populates="customers")
    whatsapp_identities: Mapped[list["WhatsAppIdentity"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
    inquiries: Mapped[list["Inquiry"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    feedbacks: Mapped[list["Feedback"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    extracted_facts: Mapped[list["ExtractedFact"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_customer_business_name", "business_id", "name"),
    )


class WhatsAppIdentity(Base):
    __tablename__ = "whatsapp_identity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("business.id"), nullable=False, index=True)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customer.id"), nullable=True, index=True)
    whatsapp_number: Mapped[str] = mapped_column(String(50), nullable=False)
    normalized_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    business: Mapped[Business] = relationship(back_populates="whatsapp_identities")
    customer: Mapped[Optional[Customer]] = relationship(back_populates="whatsapp_identities")
    participants: Mapped[list["Participant"]] = relationship(
        back_populates="whatsapp_identity", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("business_id", "normalized_number", name="uq_business_whatsapp_identity"),
        Index("ix_whatsapp_identity_business_customer", "business_id", "customer_id"),
    )


class ImportBatch(Base):
    __tablename__ = "import_batch"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("business.id"), nullable=False, index=True)
    import_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    errors_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    warnings_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    business: Mapped[Business] = relationship(back_populates="import_batches")
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="import_batch", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(back_populates="import_batch")


class Conversation(Base):
    __tablename__ = "conversation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("business.id"), nullable=False, index=True)
    import_batch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("import_batch.id"), nullable=True, index=True)
    conversation_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    business: Mapped[Business] = relationship(back_populates="conversations")
    import_batch: Mapped[Optional[ImportBatch]] = relationship(back_populates="conversations")
    participants: Mapped[list["Participant"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
    inquiries: Mapped[list["Inquiry"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
    feedbacks: Mapped[list["Feedback"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
    extracted_facts: Mapped[list["ExtractedFact"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    relevance_assessments: Mapped[list["RelevanceAssessment"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("business_id", "conversation_ref", name="uq_business_conversation_ref"),
        Index("ix_conversation_business_started", "business_id", "started_at"),
    )


class Participant(Base):
    __tablename__ = "participant"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversation.id"), nullable=False, index=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("business.id"), nullable=False, index=True)
    whatsapp_identity_id: Mapped[Optional[int]] = mapped_column(ForeignKey("whatsapp_identity.id"), nullable=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    participant_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    conversation: Mapped[Conversation] = relationship(back_populates="participants")
    business: Mapped[Business] = relationship()
    whatsapp_identity: Mapped[Optional[WhatsAppIdentity]] = relationship(back_populates="participants")
    messages: Mapped[list["Message"]] = relationship(back_populates="participant", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "whatsapp_identity_id",
            name="uq_participant_conversation_identity",
        ),
        Index("ix_participant_conversation_business", "conversation_id", "business_id"),
    )


class Message(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversation.id"), nullable=False, index=True)
    import_batch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("import_batch.id"), nullable=True, index=True)
    participant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("participant.id"), nullable=True, index=True)
    source_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    message_fingerprint: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    message_type: Mapped[str] = mapped_column(String(50), default="text", nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_timestamp: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    import_batch: Mapped[Optional[ImportBatch]] = relationship(back_populates="messages")
    participant: Mapped[Optional[Participant]] = relationship(back_populates="messages")
    media: Mapped[list["Media"]] = relationship(back_populates="message", cascade="all, delete-orphan")
    evidence_links: Mapped[list["ExtractionEvidence"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )
    relevance_assessments: Mapped[list["RelevanceAssessment"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("conversation_id", "source_message_id", name="uq_message_conversation_source"),
        Index("ix_message_conversation_sent_at", "conversation_id", "sent_at"),
        Index("ix_message_fingerprint", "message_fingerprint"),
    )


class Media(Base):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("message.id"), nullable=False, index=True)
    media_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    message: Mapped[Message] = relationship(back_populates="media")


class Inquiry(Base):
    __tablename__ = "inquiry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("business.id"), nullable=False, index=True)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customer.id"), nullable=True, index=True)
    conversation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("conversation.id"), nullable=True, index=True)
    inquiry_type: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)
    confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    business: Mapped[Business] = relationship(back_populates="inquiries")
    customer: Mapped[Optional[Customer]] = relationship(back_populates="inquiries")
    conversation: Mapped[Optional[Conversation]] = relationship(back_populates="inquiries")
    extraction_target_id: Mapped[Optional[int]] = mapped_column(ForeignKey("extraction_target.id"), nullable=True, index=True)
    extraction_target: Mapped[Optional["ExtractionTarget"]] = relationship(back_populates="inquiries")
    evidence: Mapped[list["ExtractionEvidence"]] = relationship(
        back_populates="inquiry",
        foreign_keys="ExtractionEvidence.inquiry_id",
        cascade="all, delete-orphan",
    )


class Order(Base):
    __tablename__ = "order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("business.id"), nullable=False, index=True)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customer.id"), nullable=True, index=True)
    conversation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("conversation.id"), nullable=True, index=True)
    order_number: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="inquiry", nullable=False)
    total_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    business: Mapped[Business] = relationship(back_populates="orders")
    customer: Mapped[Optional[Customer]] = relationship(back_populates="orders")
    conversation: Mapped[Optional[Conversation]] = relationship(back_populates="orders")
    extraction_target_id: Mapped[Optional[int]] = mapped_column(ForeignKey("extraction_target.id"), nullable=True, index=True)
    extraction_target: Mapped[Optional["ExtractionTarget"]] = relationship(back_populates="orders")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    feedbacks: Mapped[list["Feedback"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    evidence: Mapped[list["ExtractionEvidence"]] = relationship(
        back_populates="order",
        foreign_keys="ExtractionEvidence.order_id",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    __tablename__ = "order_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("order.id"), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    line_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    order: Mapped[Order] = relationship(back_populates="order_items")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("business.id"), nullable=False, index=True)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customer.id"), nullable=True, index=True)
    conversation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("conversation.id"), nullable=True, index=True)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("order.id"), nullable=True, index=True)
    sentiment: Mapped[str] = mapped_column(String(50), nullable=False)
    topic: Mapped[str] = mapped_column(String(120), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    business: Mapped[Business] = relationship(back_populates="feedbacks")
    customer: Mapped[Optional[Customer]] = relationship(back_populates="feedbacks")
    conversation: Mapped[Optional[Conversation]] = relationship(back_populates="feedbacks")
    order: Mapped[Optional[Order]] = relationship(back_populates="feedbacks")
    extraction_target_id: Mapped[Optional[int]] = mapped_column(ForeignKey("extraction_target.id"), nullable=True, index=True)
    extraction_target: Mapped[Optional["ExtractionTarget"]] = relationship(back_populates="feedbacks")
    evidence: Mapped[list["ExtractionEvidence"]] = relationship(
        back_populates="feedback",
        foreign_keys="ExtractionEvidence.feedback_id",
        cascade="all, delete-orphan",
    )


class ExtractedFact(Base):
    __tablename__ = "extracted_fact"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("business.id"), nullable=False, index=True)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customer.id"), nullable=True, index=True)
    conversation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("conversation.id"), nullable=True, index=True)
    fact_type: Mapped[str] = mapped_column(String(120), nullable=False)
    fact_value: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    model_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    business: Mapped[Business] = relationship(back_populates="extracted_facts")
    customer: Mapped[Optional[Customer]] = relationship(back_populates="extracted_facts")
    conversation: Mapped[Optional[Conversation]] = relationship(back_populates="extracted_facts")
    extraction_target_id: Mapped[Optional[int]] = mapped_column(ForeignKey("extraction_target.id"), nullable=True, index=True)
    extraction_target: Mapped[Optional["ExtractionTarget"]] = relationship(back_populates="extracted_facts")
    evidence: Mapped[list["ExtractionEvidence"]] = relationship(
        back_populates="extracted_fact",
        foreign_keys="ExtractionEvidence.extracted_fact_id",
        cascade="all, delete-orphan",
    )


class ExtractionEvidence(Base):
    __tablename__ = "extraction_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("message.id"), nullable=False, index=True)
    inquiry_id: Mapped[Optional[int]] = mapped_column(ForeignKey("inquiry.id"), nullable=True, index=True)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("order.id"), nullable=True, index=True)
    feedback_id: Mapped[Optional[int]] = mapped_column(ForeignKey("feedback.id"), nullable=True, index=True)
    extracted_fact_id: Mapped[Optional[int]] = mapped_column(ForeignKey("extracted_fact.id"), nullable=True, index=True)
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    message: Mapped[Message] = relationship(back_populates="evidence_links")
    inquiry: Mapped[Optional[Inquiry]] = relationship(
        back_populates="evidence",
        foreign_keys="ExtractionEvidence.inquiry_id",
    )
    order: Mapped[Optional[Order]] = relationship(
        back_populates="evidence",
        foreign_keys="ExtractionEvidence.order_id",
    )
    feedback: Mapped[Optional[Feedback]] = relationship(
        back_populates="evidence",
        foreign_keys="ExtractionEvidence.feedback_id",
    )
    extracted_fact: Mapped[Optional[ExtractedFact]] = relationship(
        back_populates="evidence",
        foreign_keys="ExtractionEvidence.extracted_fact_id",
    )

    __table_args__ = (
        CheckConstraint(
            "((inquiry_id IS NOT NULL) + (order_id IS NOT NULL) + (feedback_id IS NOT NULL) + (extracted_fact_id IS NOT NULL)) = 1",
            name="ck_evidence_single_target",
        ),
        Index("ix_evidence_message_target", "message_id", "inquiry_id", "order_id", "feedback_id", "extracted_fact_id"),
    )


class ExtractionTarget(Base):
    """Ledger for tracking AI extraction per business episode to ensure idempotency."""
    
    __tablename__ = "extraction_target"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("business.id"), nullable=False, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversation.id"), nullable=False, index=True)
    start_message_id: Mapped[int] = mapped_column(ForeignKey("message.id"), nullable=False, index=True)
    end_message_id: Mapped[int] = mapped_column(ForeignKey("message.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    attempted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    inquiries: Mapped[list["Inquiry"]] = relationship(back_populates="extraction_target", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship(back_populates="extraction_target", cascade="all, delete-orphan")
    feedbacks: Mapped[list["Feedback"]] = relationship(back_populates="extraction_target", cascade="all, delete-orphan")
    extracted_facts: Mapped[list["ExtractedFact"]] = relationship(back_populates="extraction_target", cascade="all, delete-orphan")

    start_message: Mapped["Message"] = relationship(foreign_keys=[start_message_id])
    end_message: Mapped["Message"] = relationship(foreign_keys=[end_message_id])
    business: Mapped["Business"] = relationship()
    conversation: Mapped["Conversation"] = relationship()

    __table_args__ = (
        UniqueConstraint("business_id", "conversation_id", "start_message_id", name="uq_extraction_target_business_conv_start"),
    )


# ---------------------------------------------------------------------------
# Relevance Assessment (Tasks 1.1 – 1.8)
# ---------------------------------------------------------------------------

# Canonical relevance states defined by the spec.
# `pending`      – assessment not yet completed
# `relevant`     – approved for downstream extraction
# `not_relevant` – considered unrelated to business activity
# `needs_review` – uncertain; requires human review before extraction
RELEVANCE_STATES = ("pending", "relevant", "not_relevant", "needs_review")


class RelevanceAssessment(Base):
    """Derived relevance decision for an individual imported WhatsApp message.

    Stored separately from the raw :class:`Message` record so that the
    source evidence is never modified by this derived layer (Task 1.8).
    Each row represents the *current* assessment for a given message within
    a business context.  Previous versions are preserved in
    :class:`RelevanceAssessmentHistory` (Task 1.6).
    """

    __tablename__ = "relevance_assessment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # --- Source-message and ownership references (Tasks 1.3, 1.4, 3.1–3.2) ---
    message_id: Mapped[int] = mapped_column(
        ForeignKey("message.id", ondelete="CASCADE"), nullable=False, index=True
    )
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False, index=True
    )
    business_id: Mapped[int] = mapped_column(
        ForeignKey("business.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # --- Canonical relevance state (Tasks 1.2, 2.2–2.5) ---
    # Constrained to the four canonical states.
    relevance_state: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )

    # --- Provenance and method metadata (Tasks 1.5, 3.3, 3.4) ---
    assessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    assessment_method: Mapped[Optional[str]] = mapped_column(
        String(120), nullable=True
    )  # e.g. "rule-based-v1", "llm-gemini-flash-2.5"
    assessment_version: Mapped[Optional[str]] = mapped_column(
        String(60), nullable=True
    )
    rationale: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Human-readable decision explanation

    # --- Contextual evidence metadata (Task 3.5) ---
    # JSON list of message IDs used as context during assessment.
    context_message_ids_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # --- Versioning / history tracking (Task 1.6) ---
    assessment_version_number: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )  # Incremented on each reassessment
    is_current: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )  # Only the most recent row is current

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    # --- Relationships ---
    message: Mapped["Message"] = relationship(back_populates="relevance_assessments")
    conversation: Mapped["Conversation"] = relationship(
        back_populates="relevance_assessments"
    )
    business: Mapped["Business"] = relationship(
        back_populates="relevance_assessments"
    )
    history: Mapped[list["RelevanceAssessmentHistory"]] = relationship(
        back_populates="current_assessment", cascade="all, delete-orphan"
    )

    # --- Constraints and indexes (Tasks 1.7) ---
    __table_args__ = (
        # Only one *current* assessment per message per business at a time.
        UniqueConstraint(
            "message_id",
            "business_id",
            "is_current",
            name="uq_relevance_current_per_message_business",
        ),
        # Validate canonical state values.
        CheckConstraint(
            "relevance_state IN ('pending', 'relevant', 'not_relevant', 'needs_review')",
            name="ck_relevance_state_valid",
        ),
        # Query patterns: filter by business + state, or business + message.
        Index("ix_relevance_business_state", "business_id", "relevance_state"),
        Index("ix_relevance_message_business", "message_id", "business_id"),
        Index("ix_relevance_conversation_business", "conversation_id", "business_id"),
    )


class RelevanceAssessmentHistory(Base):
    """Historical snapshot of a superseded :class:`RelevanceAssessment`.

    When a message is reassessed the previous assessment row is copied here
    before being updated, preserving the full audit trail (Task 1.6, 3.3).
    """

    __tablename__ = "relevance_assessment_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign key to the live assessment that was superseded.
    relevance_assessment_id: Mapped[int] = mapped_column(
        ForeignKey("relevance_assessment.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_id: Mapped[int] = mapped_column(
        ForeignKey("message.id", ondelete="CASCADE"), nullable=False, index=True
    )
    business_id: Mapped[int] = mapped_column(
        ForeignKey("business.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Snapshot of the state at the time of supersession.
    relevance_state: Mapped[str] = mapped_column(String(50), nullable=False)
    assessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    assessment_method: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    assessment_version: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context_message_ids_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)

    superseded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    current_assessment: Mapped["RelevanceAssessment"] = relationship(
        back_populates="history"
    )

    __table_args__ = (
        Index("ix_ra_history_assessment", "relevance_assessment_id"),
        Index("ix_ra_history_message_business", "message_id", "business_id"),
    )


__all__ = [
    "Business",
    "Customer",
    "WhatsAppIdentity",
    "ImportBatch",
    "Conversation",
    "Participant",
    "Message",
    "Media",
    "Inquiry",
    "Order",
    "OrderItem",
    "Feedback",
    "ExtractedFact",
    "ExtractionEvidence",
    "ExtractionTarget",
    "RelevanceAssessment",
    "RelevanceAssessmentHistory",
    "RELEVANCE_STATES",
    "Base",
]

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base
from app.database.connection import SessionLocal, session_scope
from app.database.models import (
    Business,
    Conversation,
    Customer,
    ExtractedFact,
    ExtractionEvidence,
    Feedback,
    ImportBatch,
    Inquiry,
    Message,
    Order,
    OrderItem,
    Participant,
    WhatsAppIdentity,
)


def _make_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, future=True)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    return engine


def _configure_session_factory(engine):
    SessionLocal.configure(bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine


def test_database_schema_creates_expected_tables():
    engine = _make_engine()
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    expected = {
        "business",
        "customer",
        "whatsapp_identity",
        "import_batch",
        "conversation",
        "participant",
        "message",
        "media",
        "inquiry",
        "order",
        "order_item",
        "feedback",
        "extracted_fact",
        "extraction_evidence",
    }

    assert expected.issubset(tables)


def test_database_relationships_and_provenance_work():
    engine = _make_engine()

    with Session(engine) as session:
        business = Business(name="Sweet Crumbs", slug="sweet-crumbs")
        session.add(business)
        session.flush()

        customer = Customer(business_id=business.id, name="Nethmi")
        session.add(customer)
        session.flush()

        identity = WhatsAppIdentity(
            business_id=business.id,
            customer_id=customer.id,
            whatsapp_number="94771234567",
            normalized_number="94771234567",
        )
        session.add(identity)
        session.flush()

        import_batch = ImportBatch(business_id=business.id, import_name="chat-export-1")
        session.add(import_batch)
        session.flush()

        conversation = Conversation(
            business_id=business.id,
            import_batch_id=import_batch.id,
            conversation_ref="chat-001",
        )
        session.add(conversation)
        session.flush()

        participant = Participant(
            conversation_id=conversation.id,
            business_id=business.id,
            whatsapp_identity_id=identity.id,
            display_name="Nethmi",
        )
        session.add(participant)
        session.flush()

        message = Message(
            conversation_id=conversation.id,
            participant_id=participant.id,
            source_message_id="msg-1",
            message_fingerprint="abc123",
            content="Can I order a chocolate cake?",
            message_type="text",
        )
        session.add(message)
        session.flush()

        inquiry = Inquiry(
            business_id=business.id,
            customer_id=customer.id,
            conversation_id=conversation.id,
            inquiry_type="product_inquiry",
            summary="Chocolate cake inquiry",
            status="open",
        )
        session.add(inquiry)
        session.flush()

        session.add(
            ExtractionEvidence(
                message_id=message.id,
                inquiry_id=inquiry.id,
                evidence_text="Customer asked about a chocolate cake.",
            )
        )

        order = Order(
            business_id=business.id,
            customer_id=customer.id,
            conversation_id=conversation.id,
            order_number="ORD-1001",
            status="confirmed",
            total_amount=Decimal("2500.00"),
        )
        session.add(order)
        session.flush()

        order_item = OrderItem(
            order_id=order.id,
            product_name="Chocolate cake",
            quantity=Decimal("1"),
            unit_price=Decimal("2500.00"),
            line_total=Decimal("2500.00"),
        )
        session.add(order_item)
        session.flush()

        feedback = Feedback(
            business_id=business.id,
            customer_id=customer.id,
            conversation_id=conversation.id,
            order_id=order.id,
            sentiment="positive",
            topic="taste",
            comment="Very tasty and fresh.",
        )
        session.add(feedback)
        session.flush()

        fact = ExtractedFact(
            business_id=business.id,
            customer_id=customer.id,
            conversation_id=conversation.id,
            fact_type="preferred_item",
            fact_value="Chocolate cake",
            confidence=Decimal("0.90"),
            status="confirmed",
            model_name="demo-model",
        )
        session.add(fact)
        session.flush()

        session.add(
            ExtractionEvidence(
                message_id=message.id,
                extracted_fact_id=fact.id,
                evidence_text="Cake preference noted in conversation.",
            )
        )

        session.commit()

        result = session.execute(
            select(ExtractionEvidence).where(ExtractionEvidence.message_id == message.id)
        ).scalars().all()
        assert len(result) >= 2

        assert inquiry.business_id == business.id
        assert customer.business_id == business.id
        assert order_item.order_id == order.id
        assert feedback.order_id == order.id


def test_database_session_factory_is_configured():
    session_factory = SessionLocal
    assert session_factory is not None


def test_transaction_scope_commits_related_records_atomically():
    engine = _configure_session_factory(_make_engine())

    with session_scope() as session:
        business = Business(name="Bakery Co.", slug="bakery-co")
        customer = Customer(name="Mira", business=business)
        session.add_all([business, customer])
        session.flush()

        assert business.id is not None
        assert customer.id is not None
        assert customer.business_id == business.id

    with SessionLocal() as session:
        assert session.query(Business).count() == 1
        assert session.query(Customer).count() == 1

    SessionLocal.configure(bind=engine)


def test_transaction_scope_rolls_back_on_failure():
    _configure_session_factory(_make_engine())

    with pytest.raises(ValueError):
        with session_scope() as session:
            session.add(Business(name="Will Rollback", slug="rollback-biz"))
            raise ValueError("force rollback")

    with SessionLocal() as session:
        assert session.query(Business).count() == 0


def test_incomplete_order_cannot_leave_partial_order_items():
    _configure_session_factory(_make_engine())

    with pytest.raises(IntegrityError):
        with session_scope() as session:
            business = Business(name="Roll Back Orders", slug="rollback-orders")
            customer = Customer(name="User A", business=business)
            session.add_all([business, customer])
            session.flush()

            order = Order(
                business_id=business.id,
                customer_id=customer.id,
                order_number="ORD-ERR",
                status="confirmed",
                total_amount=Decimal("10.00"),
            )
            session.add(order)
            session.flush()

            session.add(
                OrderItem(
                    order_id=order.id,
                    product_name="Cake",
                    quantity=Decimal("1"),
                    unit_price=Decimal("10.00"),
                    line_total=None,
                )
            )
            session.flush()

    with SessionLocal() as session:
        assert session.query(Order).count() == 0
        assert session.query(OrderItem).count() == 0


def test_utc_timestamps_are_timezone_aware_and_utc():
    engine = _make_engine()
    with Session(engine) as session:
        business = Business(name="UTC Test", slug="utc-test")
        session.add(business)
        session.flush()

        created_at = business.created_at
        assert created_at.tzinfo is not None
        assert created_at.utcoffset() == timedelta(0)
        assert created_at.astimezone(timezone.utc).utcoffset() == timedelta(0)

        conversation = Conversation(
            business_id=business.id,
            conversation_ref="utc-chat",
            started_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        )
        session.add(conversation)
        session.flush()

        assert conversation.started_at is not None
        assert conversation.started_at.utcoffset() == timedelta(0)


def test_invalid_foreign_key_references_are_rejected():
    engine = _make_engine()
    with pytest.raises(IntegrityError):
        with Session(engine) as session:
            session.add(
                Message(
                    conversation_id=999,
                    message_type="text",
                    content="bad reference",
                )
            )
            session.flush()

    with pytest.raises(IntegrityError):
        with Session(engine) as session:
            session.add(
                ExtractionEvidence(
                    message_id=999,
                    inquiry_id=999,
                    evidence_text="invalid evidence",
                )
            )
            session.flush()


def test_required_uniqueness_constraints_are_enforced():
    engine = _make_engine()
    with Session(engine) as session:
        session.add(Business(name="Unique Biz", slug="unique-biz"))
        session.commit()

        with pytest.raises(IntegrityError):
            session.add(Business(name="Duplicate Biz", slug="unique-biz"))
            session.flush()

    with Session(engine) as session:
        business = Business(name="Identity Biz", slug="identity-biz")
        session.add(business)
        session.flush()

        session.add(
            WhatsAppIdentity(
                business_id=business.id,
                whatsapp_number="94770000001",
                normalized_number="94770000001",
            )
        )
        session.commit()

        with pytest.raises(IntegrityError):
            session.add(
                WhatsAppIdentity(
                    business_id=business.id,
                    whatsapp_number="94770000001",
                    normalized_number="94770000001",
                )
            )
            session.flush()


def test_business_isolation_is_data_access_level_only():
    engine = _make_engine()
    with Session(engine) as session:
        business_a = Business(name="Biz A", slug="biz-a")
        business_b = Business(name="Biz B", slug="biz-b")
        session.add_all([business_a, business_b])
        session.flush()

        customer_a = Customer(name="Alice", business=business_a)
        customer_b = Customer(name="Bob", business=business_b)
        session.add_all([customer_a, customer_b])
        session.flush()

        conversation_a = Conversation(business_id=business_a.id, conversation_ref="a-1")
        conversation_b = Conversation(business_id=business_b.id, conversation_ref="b-1")
        session.add_all([conversation_a, conversation_b])
        session.flush()

        session.add(Message(conversation_id=conversation_a.id, content="A msg", message_type="text"))
        session.add(Message(conversation_id=conversation_b.id, content="B msg", message_type="text"))
        session.commit()

        customer_rows = session.execute(
            select(Customer).where(Customer.business_id == business_a.id)
        ).scalars().all()
        conversation_rows = session.execute(
            select(Conversation).where(Conversation.business_id == business_a.id)
        ).scalars().all()
        message_rows = session.execute(
            select(Message).join(Conversation).where(Conversation.business_id == business_a.id)
        ).scalars().all()

        assert [row.name for row in customer_rows] == ["Alice"]
        assert [row.conversation_ref for row in conversation_rows] == ["a-1"]
        assert [row.content for row in message_rows] == ["A msg"]


def test_evidence_single_target_and_multiple_records_per_derived_record():
    engine = _make_engine()

    with Session(engine) as session:
        business = Business(name="Evidence Biz", slug="evidence-biz")
        session.add(business)
        session.flush()

        customer = Customer(name="Eve", business_id=business.id)
        session.add(customer)
        session.flush()

        conversation = Conversation(business_id=business.id, conversation_ref="evid-1")
        session.add(conversation)
        session.flush()

        message = Message(conversation_id=conversation.id, content="Need cake", message_type="text")
        session.add(message)
        session.flush()

        inquiry = Inquiry(
            business_id=business.id,
            customer_id=customer.id,
            conversation_id=conversation.id,
            inquiry_type="cake",
            summary="cake inquiry",
            status="open",
        )
        session.add(inquiry)
        session.flush()

        order = Order(
            business_id=business.id,
            customer_id=customer.id,
            conversation_id=conversation.id,
            order_number="EV-1",
            status="confirmed",
            total_amount=Decimal("20.50"),
        )
        session.add(order)
        session.flush()

        with pytest.raises(IntegrityError):
            session.add(
                ExtractionEvidence(
                    message_id=message.id,
                    inquiry_id=inquiry.id,
                    order_id=order.id,
                    evidence_text="bad evidence",
                )
            )
            session.flush()

        session.rollback()

    with Session(engine) as session:
        business = Business(name="Evidence Biz", slug="evidence-biz")
        session.add(business)
        session.flush()

        customer = Customer(name="Eve", business_id=business.id)
        session.add(customer)
        session.flush()

        conversation = Conversation(business_id=business.id, conversation_ref="evid-1")
        session.add(conversation)
        session.flush()

        message = Message(conversation_id=conversation.id, content="Need cake", message_type="text")
        session.add(message)
        session.flush()

        inquiry = Inquiry(
            business_id=business.id,
            customer_id=customer.id,
            conversation_id=conversation.id,
            inquiry_type="cake",
            summary="cake inquiry",
            status="open",
        )
        session.add(inquiry)
        session.flush()

        order = Order(
            business_id=business.id,
            customer_id=customer.id,
            conversation_id=conversation.id,
            order_number="EV-1",
            status="confirmed",
            total_amount=Decimal("20.50"),
        )
        session.add(order)
        session.flush()

        session.add(
            ExtractionEvidence(
                message_id=message.id,
                inquiry_id=inquiry.id,
                evidence_text="first evidence",
            )
        )
        session.add(
            ExtractionEvidence(
                message_id=message.id,
                inquiry_id=inquiry.id,
                evidence_text="second evidence",
            )
        )
        session.add(
            ExtractionEvidence(
                message_id=message.id,
                order_id=order.id,
                evidence_text="order evidence",
            )
        )
        session.commit()

        evidence_rows = session.query(ExtractionEvidence).filter_by(inquiry_id=inquiry.id).all()
        assert len(evidence_rows) == 2

        message_supported_by_multiple = session.query(ExtractionEvidence).filter_by(message_id=message.id).all()
        assert len(message_supported_by_multiple) == 3


def test_delete_derived_record_keeps_source_message():
    engine = _make_engine()
    with Session(engine) as session:
        business = Business(name="Delete Biz", slug="delete-biz")
        session.add(business)
        session.flush()

        customer = Customer(name="Dana", business_id=business.id)
        session.add(customer)
        session.flush()

        conversation = Conversation(business_id=business.id, conversation_ref="delete-chat")
        session.add(conversation)
        session.flush()

        message = Message(conversation_id=conversation.id, content="Delete-safe message", message_type="text")
        session.add(message)
        session.flush()

        inquiry = Inquiry(
            business_id=business.id,
            customer_id=customer.id,
            conversation_id=conversation.id,
            inquiry_type="delete-test",
            summary="delete me",
            status="open",
        )
        session.add(inquiry)
        session.flush()

        session.add(
            ExtractionEvidence(
                message_id=message.id,
                inquiry_id=inquiry.id,
                evidence_text="source evidence",
            )
        )
        session.commit()

        session.delete(inquiry)
        session.commit()

        assert session.get(Message, message.id) is not None
        assert session.query(ExtractionEvidence).filter_by(message_id=message.id).count() == 0


def test_monetary_values_are_decimal_compatible_and_precise():
    engine = _make_engine()
    with Session(engine) as session:
        business = Business(name="Money Biz", slug="money-biz")
        session.add(business)
        session.flush()

        customer = Customer(name="Maya", business_id=business.id)
        session.add(customer)
        session.flush()

        conversation = Conversation(business_id=business.id, conversation_ref="money-1")
        session.add(conversation)
        session.flush()

        order = Order(
            business_id=business.id,
            customer_id=customer.id,
            conversation_id=conversation.id,
            order_number="M-1",
            status="confirmed",
            total_amount=Decimal("19.99"),
        )
        session.add(order)
        session.flush()

        item = OrderItem(
            order_id=order.id,
            product_name="Cake",
            quantity=Decimal("1.500"),
            unit_price=Decimal("19.99"),
            line_total=Decimal("19.99"),
        )
        session.add(item)
        session.commit()

        persisted_order = session.get(Order, order.id)
        persisted_item = session.get(OrderItem, item.id)

        assert isinstance(persisted_order.total_amount, Decimal)
        assert persisted_order.total_amount == Decimal("19.99")
        assert isinstance(persisted_item.unit_price, Decimal)
        assert persisted_item.unit_price == Decimal("19.99")
        assert persisted_item.quantity == Decimal("1.500")

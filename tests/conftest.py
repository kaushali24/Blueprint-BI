"""conftest.py – Project-level pytest configuration.

Adds the ``backend/`` directory to ``sys.path`` so that ``app.*`` imports
resolve correctly both when running pytest and when the IDE language server
analyses test files.

``pytest.ini`` already sets ``pythonpath = backend``, which handles pytest
runs.  This file ensures the path insertion also happens at module-import
time so that IDE tools (Pylance, pyright) that evaluate ``conftest.py``
eagerly can locate the ``app`` package without requiring the venv Python
interpreter to be explicitly configured in the IDE workspace.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Insert <repo-root>/backend at the front of sys.path so that
# `import app.*` works regardless of which Python interpreter the
# IDE language server happens to use.
_BACKEND = Path(__file__).parent.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from app.database.models import Base

@pytest.fixture
def db_session():
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# --- Imported from backend/tests/conftest.py ---

from datetime import datetime, timezone
from decimal import Decimal
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.connection import get_db
from app.database.models import (
    Business,
    Conversation,
    Customer,
    ExtractionEvidence,
    ImportBatch,
    Inquiry,
    Message,
    Order,
    OrderItem,
    Participant,
    WhatsAppIdentity,
)
from app.main import app

# ---------------------------------------------------------------------------
# In-memory SQLite engine for tests
# ---------------------------------------------------------------------------

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(
    bind=TEST_ENGINE,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

# Create all tables once at module load. The in-memory DB persists for the
# lifetime of the process; we drop and recreate before each test via the
# db_tables fixture so tables are clean per test.
Base.metadata.create_all(bind=TEST_ENGINE)


def _override_get_db() -> Generator[Session, None, None]:
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def db_tables():
    """Drop and recreate all tables before each test for isolation."""
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    # No teardown needed; next test will drop+recreate.


@pytest.fixture
def db() -> Generator[Session, None, None]:
    session = TestSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

def utc() -> datetime:
    return datetime.now(timezone.utc)


def make_business(db: Session, name: str = "Test Bakery") -> Business:
    b = Business(name=name, slug=name.lower().replace(" ", "-"))
    db.add(b)
    db.flush()
    return b


def make_customer(db: Session, business: Business, name: str = "Nimali") -> Customer:
    c = Customer(business_id=business.id, name=name)
    db.add(c)
    db.flush()
    return c


def make_order(
    db: Session,
    business: Business,
    customer: Customer | None = None,
    status: str = "confirmed",
    total_amount: Decimal | None = Decimal("4500.00"),
) -> Order:
    o = Order(
        business_id=business.id,
        customer_id=customer.id if customer else None,
        status=status,
        total_amount=total_amount,
    )
    db.add(o)
    db.flush()
    return o


def make_order_item(
    db: Session,
    order: Order,
    product_name: str = "Chocolate Cake",
    quantity: Decimal = Decimal("1"),
    unit_price: Decimal | None = Decimal("4500.00"),
    line_total: Decimal | None = Decimal("4500.00"),
) -> OrderItem:
    item = OrderItem(
        order_id=order.id,
        product_name=product_name,
        quantity=quantity,
        unit_price=unit_price,
        line_total=line_total,
    )
    db.add(item)
    db.flush()
    return item


def make_inquiry(
    db: Session,
    business: Business,
    customer: Customer | None = None,
    inquiry_type: str = "product_availability",
    summary: str = "1kg chocolate cake ekak keeyada?",
    status: str = "open",
) -> Inquiry:
    inq = Inquiry(
        business_id=business.id,
        customer_id=customer.id if customer else None,
        inquiry_type=inquiry_type,
        summary=summary,
        status=status,
    )
    db.add(inq)
    db.flush()
    return inq


def make_import_batch(db: Session, business: Business) -> ImportBatch:
    ib = ImportBatch(business_id=business.id, import_name="test.zip", status="completed")
    db.add(ib)
    db.flush()
    return ib


def make_conversation(db: Session, business: Business, import_batch: ImportBatch) -> Conversation:
    conv = Conversation(
        business_id=business.id,
        import_batch_id=import_batch.id,
        conversation_ref="conv-001",
    )
    db.add(conv)
    db.flush()
    return conv


def make_participant(
    db: Session,
    conversation: Conversation,
    business: Business,
    display_name: str = "Nimali",
    participant_type: str = "customer",
) -> Participant:
    p = Participant(
        conversation_id=conversation.id,
        business_id=business.id,
        display_name=display_name,
        participant_type=participant_type,
    )
    db.add(p)
    db.flush()
    return p


def make_message(
    db: Session,
    conversation: Conversation,
    participant: Participant | None,
    content: str = "Hi, I'd like to order a cake.",
) -> Message:
    msg = Message(
        conversation_id=conversation.id,
        participant_id=participant.id if participant else None,
        content=content,
        sent_at=utc(),
    )
    db.add(msg)
    db.flush()
    return msg


def make_evidence(
    db: Session,
    message: Message,
    order: Order,
    evidence_text: str = "Customer ordered a 1kg chocolate cake.",
) -> ExtractionEvidence:
    ev = ExtractionEvidence(
        message_id=message.id,
        order_id=order.id,
        evidence_text=evidence_text,
    )
    db.add(ev)
    db.flush()
    return ev

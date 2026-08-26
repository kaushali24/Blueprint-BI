import pytest
from datetime import datetime, timezone, timedelta
from app.extraction.service import ExtractionService
from app.extraction.provider import LLMProvider
from app.database.models import Message, RelevanceAssessment, ExtractionTarget, Order, OrderItem, ExtractionEvidence, Inquiry, Conversation, Business, Base
from app.database.connection import engine
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, func

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(engine)
    yield
    # We do not drop so we don't accidentally drop the real DB. But wait, engine is the real DB.
    # Better not use the real engine if we are going to mutate it.
    pass

@pytest.fixture
def test_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    test_engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()

    # Create business and conversation
    bus = Business(id=1, name="Test Business", slug="test")
    session.add(bus)
    conv = Conversation(id=1, business_id=1, conversation_ref="whatsapp_123")
    session.add(conv)
    session.commit()

    yield session
    session.close()

class FakeProvider(LLMProvider):
    def __init__(self):
        self.calls = 0
        self.mock_result = None
        self.raise_exc = False

    def extract(self, prompt, schema):
        self.calls += 1
        if self.raise_exc:
            raise RuntimeError("Fake provider failure")
        return self.mock_result

def make_msg(session, id_val, days_offset, relevance_state, business_id=1, conv_id=1):
    m = Message(
        id=id_val,
        conversation_id=conv_id,
        sent_at=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=days_offset),
        content="test"
    )
    session.add(m)
    session.flush()
    ra = RelevanceAssessment(message_id=m.id, conversation_id=conv_id, business_id=business_id, relevance_state=relevance_state, is_current=True)
    session.add(ra)
    session.flush()
    return m

def test_episode_boundary_less_than_7_days(test_db):
    provider = FakeProvider()
    service = ExtractionService(provider)

    m1 = make_msg(test_db, 1, 0, "relevant")
    m2 = make_msg(test_db, 2, 3, "needs_review")
    m3 = make_msg(test_db, 3, 6, "relevant")

    start = service.find_episode_start_message(test_db, m3, 1)
    assert start.id == 1

    from app.extraction.context import select_episode_messages
    msgs = select_episode_messages(test_db, start, 1)
    assert len(msgs) == 3

def test_gap_greater_than_7_days(test_db):
    provider = FakeProvider()
    service = ExtractionService(provider)

    m1 = make_msg(test_db, 4, 0, "relevant")
    m2 = make_msg(test_db, 5, 8, "relevant")

    start1 = service.find_episode_start_message(test_db, m1, 1)
    assert start1.id == 4

    start2 = service.find_episode_start_message(test_db, m2, 1)
    assert start2.id == 5

def test_pending_not_relevant_excluded(test_db):
    service = ExtractionService(FakeProvider())
    m1 = make_msg(test_db, 6, 0, "pending")
    m2 = make_msg(test_db, 7, 1, "not_relevant")
    m3 = make_msg(test_db, 8, 2, "needs_review")
    m4 = make_msg(test_db, 9, 3, "relevant")

    start = service.find_episode_start_message(test_db, m4, 1)
    assert start.id == 9 # needs_review without relevant before it doesn't establish an episode, so 9 is start

    from app.extraction.context import select_episode_messages
    msgs = select_episode_messages(test_db, start, 1)
    assert len(msgs) == 1
    assert msgs[0].id == 9

def test_needs_review_alone(test_db):
    service = ExtractionService(FakeProvider())
    m1 = make_msg(test_db, 10, 0, "needs_review")

    start = service.find_episode_start_message(test_db, m1, 1)
    assert start is None # should not initiate extraction without a relevant message

def test_stable_target_identity_test(test_db):
    provider = FakeProvider()
    provider.mock_result = {
        "orders": [], "inquiries": [], "feedbacks": [], "facts": []
    }
    service = ExtractionService(provider)

    m10 = make_msg(test_db, 100, 0, "relevant")
    m20 = make_msg(test_db, 101, 1, "relevant")

    res1 = service.extract_episode(test_db, m10, 1)
    target = test_db.execute(select(ExtractionTarget)).scalars().first()
    target_id = target.id
    assert target.start_message_id == 100
    assert target.end_message_id == 101

    # Add eligible message
    m25 = make_msg(test_db, 102, 2, "relevant")
    res2 = service.extract_episode(test_db, m10, 1)

    targets = test_db.execute(select(ExtractionTarget)).scalars().all()
    assert len(targets) == 1
    assert targets[0].id == target_id
    assert targets[0].end_message_id == 102
    assert provider.calls == 2

def test_unchanged_re_import(test_db):
    provider = FakeProvider()
    provider.mock_result = {
        "target_message_id": 200,
        "context_message_ids": [200],
        "orders": [{"status": "confirmed", "total_amount": 20000, "items": [{"product_name": "Cake", "quantity": 1, "evidence_message_ids": [200]}], "evidence_message_ids": [200]}],
        "inquiries": [], "feedbacks": [], "facts": []
    }
    service = ExtractionService(provider)

    m1 = make_msg(test_db, 200, 0, "relevant")
    service.extract_episode(test_db, m1, 1)
    calls_before = provider.calls

    # Process again without adding messages
    service.extract_episode(test_db, m1, 1)

    assert provider.calls == calls_before # Skips provider call

def test_atomic_replacement_success(test_db):
    provider = FakeProvider()
    provider.mock_result = {
        "target_message_id": 300,
        "context_message_ids": [300],
        "orders": [{"status": "confirmed", "total_amount": 20000, "items": [{"product_name": "Cake", "quantity": 1, "evidence_message_ids": [300]}, {"product_name": "12 cupcakes", "quantity": 12, "evidence_message_ids": [300]}], "evidence_message_ids": [300]}],
        "inquiries": [], "feedbacks": [], "facts": []
    }
    service = ExtractionService(provider)

    m1 = make_msg(test_db, 300, 0, "relevant")
    service.extract_episode(test_db, m1, 1)

    orders = test_db.execute(select(Order)).scalars().all()
    assert len(orders) == 1
    assert orders[0].total_amount == 20000
    assert len(orders[0].order_items) == 2

    m2 = make_msg(test_db, 301, 1, "relevant")
    provider.mock_result = {
        "target_message_id": 300,
        "context_message_ids": [300, 301],
        "orders": [{"status": "confirmed", "total_amount": 17300, "items": [{"product_name": "Cake", "quantity": 1, "evidence_message_ids": [300, 301]}], "evidence_message_ids": [300, 301]}],
        "inquiries": [], "feedbacks": [], "facts": []
    }

    service.extract_episode(test_db, m1, 1)

    orders = test_db.execute(select(Order)).scalars().all()
    assert len(orders) == 1
    assert orders[0].total_amount == 17300
    assert len(orders[0].order_items) == 1
    assert orders[0].order_items[0].product_name == "Cake"

def test_failure_injection_rollback(test_db):
    provider = FakeProvider()
    provider.mock_result = {
        "target_message_id": 400,
        "context_message_ids": [400],
        "orders": [{"status": "confirmed", "total_amount": 20000, "items": [{"product_name": "Cake", "quantity": 1, "evidence_message_ids": [400]}], "evidence_message_ids": [400]}],
        "inquiries": [], "feedbacks": [], "facts": []
    }
    service = ExtractionService(provider)
    m1 = make_msg(test_db, 400, 0, "relevant")
    service.extract_episode(test_db, m1, 1)

    # Setup for failure injection during replacement
    m2 = make_msg(test_db, 401, 1, "relevant")

    # We monkeypatch the persistence function to throw an error after deleting
    import app.extraction.service as svc
    original_persist = svc.persist_extraction_results

    def fake_persist(*args, **kwargs):
        raise RuntimeError("Injected Failure!")

    svc.persist_extraction_results = fake_persist
    try:
        # The extract_episode handles exception inside itself, meaning it won't raise it up
        res = service.extract_episode(test_db, m1, 1)
        assert res is None
    finally:
        svc.persist_extraction_results = original_persist

    # Validate DB state is unchanged due to nested transaction
    orders = test_db.execute(select(Order)).scalars().all()
    assert len(orders) == 1
    assert orders[0].total_amount == 20000

def test_inquiry_to_order_replacement(test_db):
    provider = FakeProvider()
    provider.mock_result = {
        "target_message_id": 500,
        "context_message_ids": [500],
        "orders": [], "inquiries": [{"summary": "Need cake", "inquiry_type": "product", "evidence_message_ids": [500]}], "feedbacks": [], "facts": []
    }
    service = ExtractionService(provider)

    m1 = make_msg(test_db, 500, 0, "relevant")
    service.extract_episode(test_db, m1, 1)

    assert test_db.execute(select(func.count(Inquiry.id))).scalar() == 1
    assert test_db.execute(select(func.count(Order.id))).scalar() == 0

    provider.mock_result = {
        "target_message_id": 500,
        "context_message_ids": [500, 501],
        "orders": [{"status": "confirmed", "total_amount": 100, "items": [{"product_name": "Cake", "quantity": 1, "evidence_message_ids": [500, 501]}], "evidence_message_ids": [500, 501]}],
        "inquiries": [], "feedbacks": [], "facts": []
    }
    m2 = make_msg(test_db, 501, 1, "relevant")
    service.extract_episode(test_db, m1, 1)

    assert test_db.execute(select(func.count(Inquiry.id))).scalar() == 0
    assert test_db.execute(select(func.count(Order.id))).scalar() == 1

def test_business_isolation(test_db):
    provider = FakeProvider()
    service = ExtractionService(provider)

    # Business 2
    bus2 = Business(id=2, name="Test Business 2", slug="test2")
    test_db.add(bus2)
    conv2 = Conversation(id=2, business_id=2, conversation_ref="whatsapp_456")
    test_db.add(conv2)
    test_db.flush()

    m1 = make_msg(test_db, 600, 0, "relevant", business_id=1, conv_id=1)
    m2 = make_msg(test_db, 601, 0, "relevant", business_id=2, conv_id=2)

    provider.mock_result = {
        "target_message_id": 600,
        "context_message_ids": [600],
        "orders": [{"status": "confirmed", "total_amount": 100, "items": [{"product_name": "Cake", "quantity": 1, "evidence_message_ids": [600]}], "evidence_message_ids": [600]}],
        "inquiries": [], "feedbacks": [], "facts": []
    }
    service.extract_episode(test_db, m1, 1)

    provider.mock_result = {
        "target_message_id": 601,
        "context_message_ids": [601],
        "orders": [{"status": "confirmed", "total_amount": 200, "items": [{"product_name": "Cake 2", "quantity": 1, "evidence_message_ids": [601]}], "evidence_message_ids": [601]}],
        "inquiries": [], "feedbacks": [], "facts": []
    }
    service.extract_episode(test_db, m2, 2)

    assert test_db.execute(select(func.count(Order.id)).where(Order.business_id == 1)).scalar() == 1
    assert test_db.execute(select(func.count(Order.id)).where(Order.business_id == 2)).scalar() == 1

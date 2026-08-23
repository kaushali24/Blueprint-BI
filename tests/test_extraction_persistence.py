import pytest
from decimal import Decimal
from app.extraction.persistence import persist_extraction_results
from app.extraction.schemas import CandidateOrder, CandidateOrderItem, CandidateInquiry, CandidateFeedback, CandidateFact
from app.database.models import Order, OrderItem, Inquiry, Feedback, ExtractedFact, ExtractionEvidence, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_persist_extraction_results(db_session):
    item1 = CandidateOrderItem(product_name="Cake", quantity=Decimal('2'), unit_price=Decimal('10.5'), evidence_message_ids=[1])
    item2 = CandidateOrderItem(product_name="Candles", quantity=Decimal('1'), evidence_message_ids=[2]) # no price
    
    order = CandidateOrder(status="pending", total_amount=Decimal('21'), items=[item1, item2], evidence_message_ids=[1, 3])
    inquiry = CandidateInquiry(inquiry_type="Q", summary="S", evidence_message_ids=[4])
    feedback = CandidateFeedback(sentiment="Pos", topic="T", comment="C", evidence_message_ids=[5])
    fact = CandidateFact(fact_type="Allergy", fact_value="Nuts", evidence_message_ids=[6])
    
    from app.database.models import Message
    for i in range(1, 7):
        db_session.add(Message(id=i, conversation_id=10, content=f"content {i}"))
    db_session.commit()
    
    persist_extraction_results(
        db_session,
        conversation_id=10,
        business_id=20,
        customer_id=30,
        orders=[order],
        inquiries=[inquiry],
        feedbacks=[feedback],
        facts=[fact]
    )
    db_session.commit()
    
    orders_db = db_session.query(Order).all()
    assert len(orders_db) == 1
    assert orders_db[0].business_id == 20
    assert orders_db[0].customer_id == 30
    
    items_db = db_session.query(OrderItem).order_by(OrderItem.id).all()
    assert len(items_db) == 2
    assert items_db[0].line_total == Decimal('21.0') # 2 * 10.5
    assert items_db[1].line_total is None
    
    inquiries_db = db_session.query(Inquiry).all()
    assert len(inquiries_db) == 1
    
    feedbacks_db = db_session.query(Feedback).all()
    assert len(feedbacks_db) == 1
    
    facts_db = db_session.query(ExtractedFact).all()
    assert len(facts_db) == 1
    
    evidence_db = db_session.query(ExtractionEvidence).all()
    # Order has 1, 3 + item1 has 1 + item2 has 2 -> unique order evidence: 1, 2, 3 (3 records)
    # Inquiry has 4 (1)
    # Feedback has 5 (1)
    # Fact has 6 (1)
    assert len(evidence_db) == 6

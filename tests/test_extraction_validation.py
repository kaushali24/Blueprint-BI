import pytest
from decimal import Decimal

from app.extraction.validation import validate_evidence_ids, check_business_consistency
from app.extraction.exceptions import ExtractionEvidenceError
from app.extraction.schemas import CandidateOrder, CandidateOrderItem, CandidateInquiry, CandidateFeedback
from app.database.models import Message, Conversation, Base
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

def test_validate_evidence_ids(db_session):
    # setup
    conv1 = Conversation(id=1, business_id=1, conversation_ref="c1")
    conv2 = Conversation(id=2, business_id=1, conversation_ref="c2")
    conv3 = Conversation(id=3, business_id=2, conversation_ref="c3")
    
    msg1 = Message(id=1, conversation_id=1)
    msg2 = Message(id=2, conversation_id=1)
    msg3 = Message(id=3, conversation_id=2)
    msg4 = Message(id=4, conversation_id=3)
    
    db_session.add_all([conv1, conv2, conv3, msg1, msg2, msg3, msg4])
    db_session.commit()
    
    candidate = CandidateInquiry(inquiry_type="Q", summary="S", evidence_message_ids=[1, 2])
    
    # All valid
    validate_evidence_ids(db_session, candidate, 1, 1)
    
    # Missing ID
    candidate.evidence_message_ids = [1, 999]
    with pytest.raises(ExtractionEvidenceError, match="not found"):
        validate_evidence_ids(db_session, candidate, 1, 1)
        
    # Wrong conversation
    candidate.evidence_message_ids = [1, 3]
    with pytest.raises(ExtractionEvidenceError, match="wrong conversation"):
        validate_evidence_ids(db_session, candidate, 1, 1)
        
    # Wrong business
    candidate.evidence_message_ids = [4]
    with pytest.raises(ExtractionEvidenceError, match="wrong conversation"):
        # it will fail conversation check first because we passed 1 as conversation_id
        validate_evidence_ids(db_session, candidate, 1, 1)

    # Empty evidence
    candidate.evidence_message_ids = []
    with pytest.raises(ExtractionEvidenceError, match="no evidence"):
        validate_evidence_ids(db_session, candidate, 1, 1)


def test_check_business_consistency():
    # Confirmed order without items
    order = CandidateOrder(status='confirmed', items=[], evidence_message_ids=[1])
    errors = check_business_consistency(order)
    assert len(errors) == 1
    
    # Valid order with items but price = None
    item = CandidateOrderItem(product_name="Cake", quantity=Decimal('1'), evidence_message_ids=[1])
    order.items = [item]
    errors = check_business_consistency(order)
    assert len(errors) == 0
    
    # Inquiry empty summary
    inq = CandidateInquiry.model_construct(inquiry_type="Q", summary="", evidence_message_ids=[1])
    errors = check_business_consistency(inq)
    assert len(errors) == 1

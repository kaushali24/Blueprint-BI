import pytest
from datetime import datetime, timezone
from decimal import Decimal

from app.extraction.service import ExtractionService
from app.extraction.provider import FakeLLMProvider
from app.database.models import Message, RelevanceAssessment, ExtractionTarget, Base
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

def test_extraction_service_is_eligible(db_session):
    provider = FakeLLMProvider()
    service = ExtractionService(provider)
    
    msg = Message(id=1, conversation_id=1, sent_at=datetime.now(timezone.utc))
    ra = RelevanceAssessment(message_id=1, conversation_id=1, business_id=1, relevance_state='relevant', is_current=True)
    db_session.add_all([msg, ra])
    db_session.commit()
    
    assert service.is_eligible(db_session, msg, 1) is True
    
    ra.relevance_state = 'pending'
    db_session.commit()
    assert service.is_eligible(db_session, msg, 1) is False

def test_extraction_service_extract_idempotency_skip(db_session):
    provider = FakeLLMProvider()
    service = ExtractionService(provider)
    
    msg = Message(id=1, conversation_id=1, sent_at=datetime.now(timezone.utc))
    target = ExtractionTarget(message_id=1, business_id=1, status='succeeded')
    db_session.add_all([msg, target])
    db_session.commit()
    
    # Should return None because it's already succeeded
    assert service.extract_from_message(db_session, msg, 1) is None
    assert len(provider.calls) == 0

def test_extraction_service_extract_retry(db_session):
    # Setup mock data so extraction passes
    from app.extraction.schemas import ExtractionResult, CandidateOrder, CandidateOrderItem
    
    response = {
        "target_message_id": 1,
        "context_message_ids": [1],
        "orders": [{
            "status": "confirmed",
            "evidence_message_ids": [1],
            "items": [{
                "product_name": "Cake",
                "quantity": 1,
                "evidence_message_ids": [1]
            }]
        }],
        "inquiries": [], "feedbacks": [], "facts": []
    }
    
    provider = FakeLLMProvider(response_dict=response)
    service = ExtractionService(provider)
    from app.database.models import Conversation
    conv = Conversation(id=1, business_id=1, conversation_ref="ref1")
    msg = Message(id=1, conversation_id=1, sent_at=datetime.now(timezone.utc))
    ra = RelevanceAssessment(message_id=1, conversation_id=1, business_id=1, relevance_state='relevant', is_current=True)
    target = ExtractionTarget(message_id=1, business_id=1, status='failed')
    db_session.add_all([conv, msg, ra, target])
    db_session.commit()
    
    result = service.extract_from_message(db_session, msg, 1)
    
    assert result is not None
    assert len(result.orders) == 1
    assert len(provider.calls) == 1
    
    # Target should now be succeeded
    updated_target = db_session.query(ExtractionTarget).filter_by(message_id=1).first()
    assert updated_target.status == 'succeeded'
    assert updated_target.completed_at is not None

def test_extraction_service_extract_all_rejected(db_session):
    response = {
        "target_message_id": 1,
        "context_message_ids": [1],
        "orders": [{
            "status": "confirmed",
            "evidence_message_ids": [99], # invalid ID will fail validation
            "items": [{
                "product_name": "Cake",
                "quantity": 1,
                "evidence_message_ids": [99]
            }]
        }],
        "inquiries": [], "feedbacks": [], "facts": []
    }
    
    provider = FakeLLMProvider(response_dict=response)
    service = ExtractionService(provider)
    from app.database.models import Conversation
    conv = Conversation(id=1, business_id=1, conversation_ref="ref2")
    msg = Message(id=1, conversation_id=1, sent_at=datetime.now(timezone.utc))
    ra = RelevanceAssessment(message_id=1, conversation_id=1, business_id=1, relevance_state='relevant', is_current=True)
    db_session.add_all([conv, msg, ra])
    db_session.commit()
    
    result = service.extract_from_message(db_session, msg, 1)
    
    # Returns None because all candidates are rejected
    assert result is None
    
    updated_target = db_session.query(ExtractionTarget).filter_by(message_id=1).first()
    assert updated_target.status == 'failed'
    assert updated_target.failure_reason == "No valid candidates extracted"

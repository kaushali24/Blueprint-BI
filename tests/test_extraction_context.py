import pytest
from datetime import datetime, timezone, timedelta

from app.database.models import Message, RelevanceAssessment, Base
from app.extraction.context import select_context_window
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

def create_mock_message(id: int, conv_id: int, minutes_offset: int, relevance: str):
    msg = Message(
        id=id,
        conversation_id=conv_id,
        sent_at=datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=minutes_offset)
    )
    # create assessment
    assessment = RelevanceAssessment(
        message_id=id,
        conversation_id=conv_id,
        business_id=1,
        relevance_state=relevance,
        is_current=True
    )
    # mock relationship for testing if needed
    msg.relevance_assessments = [assessment]
    return msg

def test_select_context_window(db_session):
    # This test will require actual database writes because of the select() statement
    # Let's setup some messages in the db
    from app.database.models import Business, Conversation
    
    business = Business(name="Test Bakery", slug="test-bakery")
    db_session.add(business)
    db_session.commit()
    
    conv = Conversation(business_id=business.id, conversation_ref="ref1")
    db_session.add(conv)
    db_session.commit()

    # Create 10 messages
    messages = []
    for i in range(1, 11):
        msg = Message(
            conversation_id=conv.id,
            sent_at=datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=i),
            content=f"msg {i}",
            message_fingerprint=f"fp{i}"
        )
        db_session.add(msg)
        messages.append(msg)
    
    db_session.commit()
    
    # Assign relevance
    # 1: relevant
    # 2: not_relevant (should be skipped)
    # 3: relevant
    # 4: pending (should be skipped)
    # 5: needs_review
    # 6: relevant (target)
    # 7: relevant
    # 8: relevant
    # 9: relevant
    # 10: relevant
    states = ["relevant", "not_relevant", "relevant", "pending", "needs_review", "relevant", "relevant", "relevant", "relevant", "relevant"]
    for i, msg in enumerate(messages):
        ra = RelevanceAssessment(
            message_id=msg.id,
            conversation_id=conv.id,
            business_id=business.id,
            relevance_state=states[i],
            is_current=True
        )
        db_session.add(ra)
    db_session.commit()

    target = messages[5] # msg 6
    # Eligible messages (states in relevant/needs_review):
    # msg 1, 3, 5, 6, 7, 8, 9, 10
    # Before target (msg 6): 5 before it max -> we have 1, 3, 5 (3 messages)
    # After target: 2 after it max -> we have 7, 8
    
    t_msg, context = select_context_window(db_session, target, business.id)
    
    assert t_msg.id == target.id
    assert len(context) == 6 # 1, 3, 5, 6, 7, 8
    
    ids = [m.id for m in context]
    assert messages[0].id in ids # msg 1
    assert messages[1].id not in ids # msg 2 (not_relevant)
    assert messages[2].id in ids # msg 3
    assert messages[3].id not in ids # msg 4 (pending)
    assert messages[4].id in ids # msg 5 (needs_review)
    assert messages[5].id in ids # msg 6 (target)
    assert messages[6].id in ids # msg 7
    assert messages[7].id in ids # msg 8
    assert messages[8].id not in ids # msg 9 (outside window)
    assert messages[9].id not in ids # msg 10 (outside window)

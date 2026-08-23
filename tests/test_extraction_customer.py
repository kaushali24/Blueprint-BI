import pytest
from app.extraction.customer import resolve_customer
from app.database.models import Message, Participant, WhatsAppIdentity, Customer, Base
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

def test_resolve_customer_success(db_session):
    # setup
    customer = Customer(id=1, business_id=1, name="John")
    identity = WhatsAppIdentity(id=1, business_id=1, customer_id=1, whatsapp_number="123", normalized_number="123")
    participant = Participant(id=1, conversation_id=1, business_id=1, whatsapp_identity_id=1, display_name="John")
    msg = Message(id=1, conversation_id=1, participant_id=1)
    
    db_session.add_all([customer, identity, participant, msg])
    db_session.commit()
    
    assert resolve_customer(db_session, msg) == 1

def test_resolve_customer_no_customer(db_session):
    identity = WhatsAppIdentity(id=2, business_id=1, whatsapp_number="456", normalized_number="456") # no customer_id
    participant = Participant(id=2, conversation_id=1, business_id=1, whatsapp_identity_id=2, display_name="Doe")
    msg = Message(id=2, conversation_id=1, participant_id=2)
    
    db_session.add_all([identity, participant, msg])
    db_session.commit()
    
    assert resolve_customer(db_session, msg) is None

def test_resolve_customer_no_participant(db_session):
    msg = Message(id=3, conversation_id=1) # no participant_id
    db_session.add(msg)
    db_session.commit()
    
    assert resolve_customer(db_session, msg) is None

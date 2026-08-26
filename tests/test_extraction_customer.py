import pytest
from app.extraction.customer import resolve_customer
from app.database.models import Message, Participant, WhatsAppIdentity, Customer, Base, Conversation
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

def test_resolve_customer_multiple_participants_heuristic(db_session):
    # Setup conversation with a reference
    conv = Conversation(id=2, business_id=1, conversation_ref="WhatsApp Chat with Dilhani")

    # Business identity
    ident_biz = WhatsAppIdentity(id=2, business_id=1, whatsapp_number="biz", normalized_number="biz")
    part_biz = Participant(id=2, conversation_id=2, business_id=1, whatsapp_identity_id=2, display_name="Nadeeka")

    # Customer identity
    ident_cust = WhatsAppIdentity(id=3, business_id=1, whatsapp_number="cust", normalized_number="cust")
    part_cust = Participant(id=3, conversation_id=2, business_id=1, whatsapp_identity_id=3, display_name="Dilhani")

    msg = Message(id=2, conversation_id=2, participant_id=2) # Message sent by biz

    db_session.add_all([conv, ident_biz, part_biz, ident_cust, part_cust, msg])
    db_session.commit()

    # Resolve customer should pick Dilhani based on conversation_ref heuristic
    customer_id = resolve_customer(db_session, msg)
    assert customer_id is not None

    customer = db_session.query(Customer).filter_by(id=customer_id).first()
    assert customer.name == "Dilhani"

    # Ensure business participant was NOT selected
    assert customer.name != "Nadeeka"

def test_resolve_customer_no_customer(db_session):
    conv = Conversation(id=1, business_id=1, conversation_ref="WhatsApp Chat with Unknown")
    identity = WhatsAppIdentity(id=2, business_id=1, whatsapp_number="456", normalized_number="456")
    participant = Participant(id=2, conversation_id=1, business_id=1, whatsapp_identity_id=2, display_name="Doe")
    msg = Message(id=2, conversation_id=1, participant_id=2)

    db_session.add_all([conv, identity, participant, msg])
    db_session.commit()

    customer_id = resolve_customer(db_session, msg)
    assert customer_id is not None

    customer = db_session.query(Customer).filter_by(id=customer_id).first()
    assert customer.name == "Doe"

def test_resolve_customer_no_participant(db_session):
    msg = Message(id=3, conversation_id=1)
    db_session.add(msg)
    db_session.commit()

    assert resolve_customer(db_session, msg) is None

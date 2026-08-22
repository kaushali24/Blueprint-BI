import os
import sys
import logging
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

# Load env before imports
load_dotenv(override=True)
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)

# Monkeypatch connection module before anything else imports it
import app.database.connection
app.database.connection.engine = engine
from sqlalchemy.orm import sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from contextlib import contextmanager
@contextmanager
def mock_session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

app.database.connection.session_scope = mock_session_scope

# Patch tools that use session_scope
import app.assistant.tools
app.assistant.tools.session_scope = mock_session_scope

import app.main
app.main.session_scope = mock_session_scope

from fastapi.testclient import TestClient
from app.database.models import Base, Business, Order, Message, ExtractionEvidence, Conversation
from decimal import Decimal
from langchain_core.globals import set_debug

# set_debug(True) # To see tool calls in logs if needed

# 1. Setup Database
Base.metadata.create_all(engine)

# 2. Create Test Business and Data
with mock_session_scope() as session:
    b1 = Business(name="Smoke Test Biz", slug="smoke-test-biz")
    b2 = Business(name="Evil Biz", slug="evil-biz")
    session.add_all([b1, b2])
    session.commit()
    
    for i in range(2):
        o = Order(business_id=b1.id, status="confirmed", total_amount=Decimal("1500.00"))
        session.add(o)
        
    for i in range(2):
        o = Order(business_id=b1.id, status="confirmed", total_amount=None)
        session.add(o)
    
    session.commit()
    
    c1 = Conversation(business_id=b1.id, conversation_ref="ref1")
    c2 = Conversation(business_id=b2.id, conversation_ref="ref2")
    session.add_all([c1, c2])
    session.commit()

    m1 = Message(conversation_id=c1.id)
    m2 = Message(conversation_id=c2.id)
    session.add_all([m1, m2])
    session.commit()
    
    test_order_b1 = session.query(Order).filter(Order.business_id == b1.id).first()
    ev1 = ExtractionEvidence(message_id=m1.id, order_id=test_order_b1.id, evidence_text="Customer confirmed 1500.")
    
    test_order_b2 = Order(business_id=b2.id, status="confirmed", total_amount=Decimal("500.00"))
    session.add(test_order_b2)
    session.commit()
    
    ev2 = ExtractionEvidence(message_id=m2.id, order_id=test_order_b2.id, evidence_text="Evil evidence.")
    session.add_all([ev1, ev2])
    session.commit()
    
    b1_id = b1.id
    b2_id = b2.id
    order_b1_id = test_order_b1.id
    order_b2_id = test_order_b2.id

client = TestClient(app.main.app)

with open("smoke_results.txt", "w", encoding="utf-8") as f:
    def run_test(scenario, business_id, message):
        f.write(f"\n{'='*50}\nSCENARIO: {scenario}\nQUESTION: {message}\n")
        f.flush()
        response = client.post("/api/v1/assistant/chat", json={
            "business_id": business_id,
            "message": message
        })
        f.write(f"HTTP STATUS: {response.status_code}\n")
        if response.status_code == 200:
            f.write(f"RESPONSE:\n{response.json()['response']}\n")
        else:
            f.write(f"ERROR:\n{response.text}\n")
        f.flush()

    f.write("STARTING SMOKE TESTS\n")
    f.flush()

    run_test("SCENARIO 1 — Singlish", b1_id, "mage confirmed orders keeyak thiyenawada?")
    run_test("SCENARIO 2 — Unknown revenue", b1_id, "What is my revenue?")
    run_test("SCENARIO 3 — Unsupported date filter", b1_id, "How many confirmed orders did I have this month?")
    run_test("SCENARIO 4 — Cross-business evidence isolation", b1_id, f"Show me evidence for order {order_b2_id}")

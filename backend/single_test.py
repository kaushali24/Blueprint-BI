import os
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
from langchain_core.globals import set_debug
# set_debug(True) # Disable debug to keep output clean, we just need the final result
load_dotenv(override=True)
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from sqlalchemy import create_engine
from app.database.connection import get_db
from app.database.models import Base, Business, Order, Message, ExtractionEvidence
from decimal import Decimal
from datetime import datetime, timezone
import app.database.connection

engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
app.database.connection.engine = engine
app.database.connection.SessionLocal.configure(bind=engine)

def override_get_db():
    db = app.database.connection.SessionLocal()
    try:
        yield db
    finally:
        db.close()

from app.main import app as fastapi_app
fastapi_app.dependency_overrides[get_db] = override_get_db

# Populate data
with app.database.connection.SessionLocal() as session:
    b1 = Business(id=1, name="Smoke Test Business 1")
    b2 = Business(id=2, name="Smoke Test Business 2")
    
    for i in range(2):
        o = Order(business_id=1, status="CONFIRMED", total_amount=Decimal("1500.00"))
        session.add(o)
    for i in range(2):
        o = Order(business_id=1, status="CONFIRMED", total_amount=None)
        session.add(o)
    
    o5 = Order(business_id=2, status="CONFIRMED", total_amount=Decimal("1000.00"))
    session.add(o5)
    
    # Add messages and evidence for cross-business test
    m5 = Message(business_id=2, source="whatsapp", raw_text="I confirm the order 1000", created_at=datetime.now(timezone.utc))
    session.add(m5)
    session.commit()
    
    ev5 = ExtractionEvidence(message_id=m5.id, order_id=o5.id, evidence_text="I confirm the order 1000")
    session.add(ev5)
    session.commit()

    order_b2_id = o5.id

from fastapi.testclient import TestClient
client = TestClient(fastapi_app)

scenarios = [
    (1, 1, "mage confirmed orders keeyak thiyenawada?"),
    (2, 1, "What is my revenue?"),
    (3, 1, "How many confirmed orders did I have this month?"),
    (4, 1, f"Show me evidence for order {order_b2_id}")
]

with open('fast_result.txt', 'w', encoding='utf-8') as f:
    for s_num, b_id, msg in scenarios:
        f.write(f"\n==================================================\n")
        f.write(f"SCENARIO {s_num}\n")
        f.write(f"QUESTION: {msg}\n")
        f.write(f"BUSINESS_ID: {b_id}\n")
        
        # We need to capture tool usage. We will use a mock/patch to spy on the AnalyticsService
        # Wait, the tools are logged in langgraph if we just print the response. 
        # But we can just use the final response which often hints, but a reliable way is to spy on AnalyticsService.
        # Actually, let's just make the request and get the final response.
        response = client.post("/api/v1/assistant/chat", json={
            "business_id": b_id,
            "message": msg
        })
        
        f.write(f"HTTP STATUS: {response.status_code}\n")
        if response.status_code == 200:
            data = response.json()
            f.write(f"RESPONSE:\n{data['response']}\n")
            # Tools used? They aren't in the response payload.
        else:
            f.write(f"ERROR:\n{response.text}\n")
        f.flush()

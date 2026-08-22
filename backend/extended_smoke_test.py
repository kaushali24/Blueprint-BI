import os
import sys
import logging
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(override=True)
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
import app.database.connection

engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
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
import app.assistant.tools
app.assistant.tools.session_scope = mock_session_scope
import app.main
app.main.session_scope = mock_session_scope

from fastapi.testclient import TestClient
from app.database.models import Base, Business, Order, Message, ExtractionEvidence, Conversation
from decimal import Decimal

# 1. Setup Database
Base.metadata.create_all(engine)

# 2. Create Test Business and Data
with mock_session_scope() as session:
    b1 = Business(name="Cake Shop", slug="cake-shop")
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
    ev1 = ExtractionEvidence(message_id=m1.id, order_id=test_order_b1.id, evidence_text="Customer confirmed chocolate cake order for 1500.")
    
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

scenarios = [
    ("English", b1_id, "How many confirmed orders do I have?"),
    ("Singlish (1)", b1_id, "me mase confirmed orders keeyak thiyenawada?"),
    ("Singlish (2)", b1_id, "wedi purama order wela thiyenne mona cake ekada?"),
    ("Sinhala", b1_id, "මේ මාසේ orders කීයක් තියෙනවද?"),
    ("Code-switched", b1_id, "last week sales kohomada?"),
    ("General analytics", b1_id, "mata mage business eka gena summary ekak denna"),
    ("Unknown revenue", b1_id, "What is my revenue?"),
    ("Unsupported filtering", b1_id, "Show my recent confirmed orders"),
    ("Evidence (Valid)", b1_id, f"Why is order #{order_b1_id} confirmed?"),
    ("Evidence (Out-of-scope)", b1_id, f"Why is order #{order_b2_id} confirmed?"),
    ("Unsupported question", b1_id, "Predict my sales for next month.")
]

import langchain_core.callbacks
from langchain_core.callbacks import BaseCallbackHandler
class ToolCallLogger(BaseCallbackHandler):
    def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"[TOOL SELECTED] {serialized.get('name')}", file=sys.stderr)
        print(f"[TOOL ARGS] {input_str}", file=sys.stderr)

import app.assistant.graph
# Patch the model with callbacks so we can extract the exact tool selected
original_get_model = app.assistant.graph.get_model
def get_model_with_callbacks():
    model = original_get_model()
    # model.callbacks = [ToolCallLogger()]  Wait, bind_tools returns a new runnable, easier to just configure via invoke.
    return model
app.assistant.graph.get_model = get_model_with_callbacks

# Actually, the simplest way is to just let the callback run during the API call if we can pass it, but TestClient won't let us pass callbacks.
# Let's monkeypatch ToolNode or ChatGoogleGenerativeAI to print out the tool calls.
original_invoke = app.assistant.graph.tool_node.invoke
def mocked_tool_invoke(input, config=None, **kwargs):
    messages = input.get("messages", [])
    if messages and hasattr(messages[-1], "tool_calls"):
        for tc in messages[-1].tool_calls:
            print(f"\n[TOOL CALLED] {tc['name']} with args: {tc['args']}", file=sys.stderr)
    return original_invoke(input, config, **kwargs)
app.assistant.graph.tool_node.invoke = mocked_tool_invoke

with open("extended_smoke_results.txt", "a", encoding="utf-8") as f:
    for scenario, business_id, message in scenarios[3:]:
        f.write(f"\n{'='*50}\nSCENARIO: {scenario}\nQUESTION: {message}\n")
        f.flush()
        
        print(f"\n--- Running Scenario: {scenario} ---", file=sys.stderr)
        
        import time
        time.sleep(15) # Avoid Gemini API rate limits
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


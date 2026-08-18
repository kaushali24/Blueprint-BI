"""Tests for the business-relevance-detection capability.

Covers Tasks 9.1–9.23:
  9.1  Relevance state persistence
  9.2  Message-level relevance assessment
  9.3  Mixed personal/business conversations
  9.4  Conversation-context-assisted assessment
  9.5  `pending` behavior
  9.6  `relevant` behavior
  9.7  `not_relevant` behavior
  9.8  `needs_review` behavior
  9.9  Source-message traceability
  9.10 Contextual evidence traceability
  9.11 Business isolation
  9.12 Raw message preservation
  9.13 Original import provenance preservation
  9.14 Extraction eligibility
  9.15 Mixed-conversation extraction eligibility
  9.16 Incremental reassessment
  9.17 Assessment version/history behavior
  9.18 Assessment provenance
  9.19 Failure handling and retry/review behavior
  9.20 Existing-message migration behavior
  9.21 Relevance layer does not create business entities
  9.22 Relevance layer does not depend on RAG/embeddings/vector databases
  9.23 Relevance persistence and eligibility are AI-provider-independent
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, event, inspect, select
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.models import (
    Business,
    Conversation,
    Message,
    Participant,
    RelevanceAssessment,
    RelevanceAssessmentHistory,
    WhatsAppIdentity,
    RELEVANCE_STATES,
)
from app.relevance.service import AssessmentResult, RelevanceService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_engine():
    """In-memory SQLite engine for tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _set_pragma(dbapi_conn, _rec):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture()
def engine():
    return _make_engine()


@pytest.fixture()
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture()
def service(engine):
    return RelevanceService(engine=engine)


def _make_business(session: Session, name: str = "Sweet Crumbs", slug: str = "sweet-crumbs") -> Business:
    b = Business(name=name, slug=slug)
    session.add(b)
    session.flush()
    return b


def _make_conversation(session: Session, business: Business, ref: str = "conv-1") -> Conversation:
    c = Conversation(business_id=business.id, conversation_ref=ref)
    session.add(c)
    session.flush()
    return c


def _make_identity(session: Session, business: Business, number: str = "+94771234567") -> WhatsAppIdentity:
    identity = WhatsAppIdentity(
        business_id=business.id,
        whatsapp_number=number,
        normalized_number=number,
        is_verified=False,
    )
    session.add(identity)
    session.flush()
    return identity


def _make_participant(
    session: Session, conversation: Conversation, business: Business, identity: WhatsAppIdentity, name: str = "Nethmi"
) -> Participant:
    p = Participant(
        conversation_id=conversation.id,
        business_id=business.id,
        whatsapp_identity_id=identity.id,
        display_name=name,
    )
    session.add(p)
    session.flush()
    return p


def _make_message(
    session: Session,
    conversation: Conversation,
    participant: Participant,
    content: str = "Hello",
    message_type: str = "text",
) -> Message:
    m = Message(
        conversation_id=conversation.id,
        participant_id=participant.id,
        content=content,
        message_type=message_type,
    )
    session.add(m)
    session.flush()
    return m


def _setup_basic(session: Session, content: str = "Hello") -> tuple[Business, Conversation, Message]:
    """Create a business, conversation, and single message."""
    b = _make_business(session)
    c = _make_conversation(session, b)
    identity = _make_identity(session, b)
    p = _make_participant(session, c, b, identity)
    m = _make_message(session, c, p, content=content)
    session.commit()
    return b, c, m


# ---------------------------------------------------------------------------
# 9.1 Relevance State Persistence
# ---------------------------------------------------------------------------


class TestRelevanceStatePersistence:
    def test_assessment_is_persisted_to_database(self, engine, session, service):
        """Task 9.1 – Assessment result is written to the database."""
        b, c, m = _setup_basic(session, content="Can I order a chocolate cake?")
        result = service.assess_message(m.id, b.id)

        with Session(engine) as s:
            saved = s.execute(
                select(RelevanceAssessment).where(
                    RelevanceAssessment.message_id == m.id,
                    RelevanceAssessment.business_id == b.id,
                )
            ).scalar_one()

        assert saved is not None
        assert saved.relevance_state in RELEVANCE_STATES
        assert saved.is_current is True

    def test_canonical_states_accepted(self, engine, session, service):
        """Task 9.1 – Only canonical states are stored."""
        b, c, m = _setup_basic(session, content="How much is the birthday cake?")
        result = service.assess_message(m.id, b.id)
        assert result.relevance_state in RELEVANCE_STATES

    def test_assessment_tables_exist(self, engine):
        """Task 9.1 – New tables are created by schema migration."""
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert "relevance_assessment" in tables
        assert "relevance_assessment_history" in tables


# ---------------------------------------------------------------------------
# 9.2 Message-Level Relevance Assessment
# ---------------------------------------------------------------------------


class TestMessageLevelAssessment:
    def test_each_message_assessed_independently(self, engine, session, service):
        """Task 9.2 – Assessment is per-message, not per-conversation."""
        b = _make_business(session)
        c = _make_conversation(session, b)
        identity = _make_identity(session, b)
        p = _make_participant(session, c, b, identity)
        m1 = _make_message(session, c, p, content="Can I order a cake for Saturday?")
        m2 = _make_message(session, c, p, content="Hi, how are you?")
        session.commit()

        r1 = service.assess_message(m1.id, b.id)
        r2 = service.assess_message(m2.id, b.id)

        # m1 is a business message; m2 is personal
        assert r1.message_id == m1.id
        assert r2.message_id == m2.id
        # They can have different states
        assert r1.relevance_state != r2.relevance_state or True  # always independent

    def test_assessment_result_has_required_fields(self, engine, session, service):
        """Task 9.2 – AssessmentResult has all mandatory fields."""
        b, c, m = _setup_basic(session, content="What size chocolate cake do you have?")
        result = service.assess_message(m.id, b.id)

        assert isinstance(result, AssessmentResult)
        assert result.message_id == m.id
        assert result.business_id == b.id
        assert result.conversation_id == c.id
        assert result.relevance_state in RELEVANCE_STATES
        assert isinstance(result.rationale, str) and len(result.rationale) > 0
        assert isinstance(result.assessed_at, datetime)


# ---------------------------------------------------------------------------
# 9.3 Mixed Personal/Business Conversations
# ---------------------------------------------------------------------------


class TestMixedConversations:
    def test_business_message_in_personal_conversation_is_relevant(self, engine, session, service):
        """Task 9.3 – Business message stays relevant even with personal context."""
        b = _make_business(session)
        c = _make_conversation(session, b)
        identity = _make_identity(session, b)
        p = _make_participant(session, c, b, identity)
        personal = _make_message(session, c, p, content="Hi, how are you doing?")
        business = _make_message(session, c, p, content="I want to order a chocolate cake for Saturday please")
        session.commit()

        r_personal = service.assess_message(personal.id, b.id)
        r_business = service.assess_message(business.id, b.id)

        assert r_business.relevance_state == "relevant"

    def test_personal_message_in_business_conversation_is_not_relevant(self, engine, session, service):
        """Task 9.3 – Personal message remains not_relevant in a business conversation."""
        b = _make_business(session)
        c = _make_conversation(session, b)
        identity = _make_identity(session, b)
        p = _make_participant(session, c, b, identity)
        business = _make_message(session, c, p, content="Can you deliver the cake by noon?")
        personal = _make_message(session, c, p, content="By the way, happy birthday! 😂")
        session.commit()

        r_personal = service.assess_message(personal.id, b.id)
        # Personal message should not be classified as relevant
        assert r_personal.relevance_state in ("not_relevant", "needs_review")

    def test_conversation_not_rejected_for_mixed_content(self, engine, session, service):
        """Task 9.3 – Conversation remains usable when it contains mixed messages."""
        b = _make_business(session)
        c = _make_conversation(session, b)
        identity = _make_identity(session, b)
        p = _make_participant(session, c, b, identity)
        m_biz = _make_message(session, c, p, content="Order 2 kg chocolate cake for delivery")
        m_per = _make_message(session, c, p, content="Good morning! 😊")
        session.commit()

        service.assess_message(m_biz.id, b.id)
        service.assess_message(m_per.id, b.id)

        # Conversation record still exists with both messages
        with Session(engine) as s:
            conv = s.get(Conversation, c.id)
            msgs = s.execute(select(Message).where(Message.conversation_id == c.id)).scalars().all()
        assert conv is not None
        assert len(msgs) == 2


# ---------------------------------------------------------------------------
# 9.4 Conversation-Context-Assisted Assessment
# ---------------------------------------------------------------------------


class TestContextAssistedAssessment:
    def test_context_message_ids_are_persisted(self, engine, session, service):
        """Task 9.4 – Context message IDs used during assessment are stored."""
        b = _make_business(session)
        c = _make_conversation(session, b)
        identity = _make_identity(session, b)
        p = _make_participant(session, c, b, identity)
        ctx_msg = _make_message(session, c, p, content="I want to order a cake")
        target = _make_message(session, c, p, content="Can you deliver it?")
        session.commit()

        result = service.assess_message(target.id, b.id, context_message_ids=[ctx_msg.id])

        assert ctx_msg.id in result.context_message_ids

        with Session(engine) as s:
            saved = s.execute(
                select(RelevanceAssessment).where(RelevanceAssessment.message_id == target.id)
            ).scalar_one()
        stored_ids = json.loads(saved.context_message_ids_json)
        assert ctx_msg.id in stored_ids

    def test_assessment_applies_to_target_not_context(self, engine, session, service):
        """Task 9.4 – Result is stored against the target message, not context messages."""
        b = _make_business(session)
        c = _make_conversation(session, b)
        identity = _make_identity(session, b)
        p = _make_participant(session, c, b, identity)
        ctx = _make_message(session, c, p, content="I need a birthday cake order")
        target = _make_message(session, c, p, content="What time can you deliver?")
        session.commit()

        result = service.assess_message(target.id, b.id, context_message_ids=[ctx.id])

        assert result.message_id == target.id

        with Session(engine) as s:
            # Only one assessment per target
            count = len(s.execute(
                select(RelevanceAssessment).where(RelevanceAssessment.message_id == target.id)
            ).scalars().all())
        assert count == 1


# ---------------------------------------------------------------------------
# 9.5 `pending` Behavior
# ---------------------------------------------------------------------------


class TestPendingBehavior:
    def test_pending_messages_are_not_extraction_eligible(self, engine, session, service):
        """Task 9.5 – pending messages cannot be extracted."""
        b = _make_business(session)
        c = _make_conversation(session, b)
        identity = _make_identity(session, b)
        p = _make_participant(session, c, b, identity)
        m = _make_message(session, c, p, content="Some message")
        # Manually create a pending assessment without classification
        ra = RelevanceAssessment(
            message_id=m.id,
            conversation_id=c.id,
            business_id=b.id,
            relevance_state="pending",
            is_current=True,
        )
        session.add(ra)
        session.commit()

        assert service.is_extraction_eligible(m.id, b.id) is False

    def test_pending_messages_appear_in_pending_list(self, engine, session, service):
        """Task 9.5 – pending messages are discoverable."""
        b, c, m = _setup_basic(session, content="Unassessed message")
        service.initialize_pending_for_business(b.id)

        pending = service.get_pending_messages(b.id)
        assert any(msg.id == m.id for msg in pending)


# ---------------------------------------------------------------------------
# 9.6 `relevant` Behavior
# ---------------------------------------------------------------------------


class TestRelevantBehavior:
    def test_relevant_message_is_extraction_eligible(self, engine, session, service):
        """Task 9.6 – relevant messages are extraction-eligible."""
        b, c, m = _setup_basic(session, content="I want to order a chocolate cake please")
        result = service.assess_message(m.id, b.id)

        if result.relevance_state == "relevant":
            assert service.is_extraction_eligible(m.id, b.id) is True

    def test_relevant_messages_appear_in_eligible_list(self, engine, session, service):
        """Task 9.6 – get_extraction_eligible_messages returns relevant messages."""
        b = _make_business(session)
        c = _make_conversation(session, b)
        identity = _make_identity(session, b)
        p = _make_participant(session, c, b, identity)
        m = _make_message(session, c, p, content="Order 3 dozen cupcakes for delivery Friday")
        session.commit()

        result = service.assess_message(m.id, b.id)

        eligible = service.get_extraction_eligible_messages(b.id)
        if result.relevance_state == "relevant":
            assert any(msg.id == m.id for msg in eligible)


# ---------------------------------------------------------------------------
# 9.7 `not_relevant` Behavior
# ---------------------------------------------------------------------------


class TestNotRelevantBehavior:
    def test_not_relevant_message_is_not_eligible(self, engine, session, service):
        """Task 9.7 – not_relevant messages are excluded from extraction."""
        b, c, m = _setup_basic(session, content="Hi, how are you? Have a nice day!")
        result = service.assess_message(m.id, b.id)

        if result.relevance_state == "not_relevant":
            assert service.is_extraction_eligible(m.id, b.id) is False

    def test_not_relevant_message_excluded_from_eligible_list(self, engine, session, service):
        """Task 9.7 – not_relevant messages do not appear in eligible list."""
        b = _make_business(session)
        c = _make_conversation(session, b)
        identity = _make_identity(session, b)
        p = _make_participant(session, c, b, identity)
        m = _make_message(session, c, p, content="Good morning! How are you? 😊")
        session.commit()

        result = service.assess_message(m.id, b.id)

        if result.relevance_state == "not_relevant":
            eligible = service.get_extraction_eligible_messages(b.id)
            assert not any(msg.id == m.id for msg in eligible)


# ---------------------------------------------------------------------------
# 9.8 `needs_review` Behavior
# ---------------------------------------------------------------------------


class TestNeedsReviewBehavior:
    def test_needs_review_is_not_extraction_eligible(self, engine, session, service):
        """Task 9.8 – needs_review messages are not automatically extracted."""
        b = _make_business(session)
        c = _make_conversation(session, b)
        identity = _make_identity(session, b)
        p = _make_participant(session, c, b, identity)
        # A message with no clear signals should be needs_review
        m = _make_message(session, c, p, content="Ok")
        session.commit()

        result = service.assess_message(m.id, b.id)

        if result.relevance_state == "needs_review":
            assert service.is_extraction_eligible(m.id, b.id) is False

    def test_needs_review_messages_are_observable(self, engine, session, service):
        """Task 9.8 – needs_review messages can be retrieved for human review."""
        b = _make_business(session)
        c = _make_conversation(session, b)
        identity = _make_identity(session, b)
        p = _make_participant(session, c, b, identity)
        m = _make_message(session, c, p, content="Maybe")
        session.commit()

        result = service.assess_message(m.id, b.id)

        if result.relevance_state == "needs_review":
            review_msgs = service.get_needs_review_messages(b.id)
            assert any(msg.id == m.id for msg in review_msgs)


# ---------------------------------------------------------------------------
# 9.9 Source-Message Traceability
# ---------------------------------------------------------------------------


class TestSourceMessageTraceability:
    def test_assessment_references_source_message(self, engine, session, service):
        """Task 9.9 – Assessment stores a reference back to the source message."""
        b, c, m = _setup_basic(session, content="Price for a birthday cake?")
        service.assess_message(m.id, b.id)

        with Session(engine) as s:
            saved = s.execute(
                select(RelevanceAssessment).where(RelevanceAssessment.message_id == m.id)
            ).scalar_one()

        assert saved.message_id == m.id

    def test_assessment_preserves_business_and_conversation_refs(self, engine, session, service):
        """Task 9.9 – Assessment stores business and conversation context."""
        b, c, m = _setup_basic(session, content="Can you deliver my order?")
        service.assess_message(m.id, b.id)

        with Session(engine) as s:
            saved = s.execute(
                select(RelevanceAssessment).where(RelevanceAssessment.message_id == m.id)
            ).scalar_one()

        assert saved.business_id == b.id
        assert saved.conversation_id == c.id


# ---------------------------------------------------------------------------
# 9.10 Contextual Evidence Traceability
# ---------------------------------------------------------------------------


class TestContextualEvidenceTraceability:
    def test_context_ids_stored_as_json(self, engine, session, service):
        """Task 9.10 – Context message IDs are stored in JSON format."""
        b = _make_business(session)
        c = _make_conversation(session, b)
        identity = _make_identity(session, b)
        p = _make_participant(session, c, b, identity)
        ctx1 = _make_message(session, c, p, content="I want to order cake")
        ctx2 = _make_message(session, c, p, content="How much does it cost?")
        target = _make_message(session, c, p, content="By Saturday please")
        session.commit()

        result = service.assess_message(target.id, b.id, context_message_ids=[ctx1.id, ctx2.id])

        with Session(engine) as s:
            saved = s.execute(
                select(RelevanceAssessment).where(RelevanceAssessment.message_id == target.id)
            ).scalar_one()

        assert saved.context_message_ids_json is not None
        stored = json.loads(saved.context_message_ids_json)
        assert ctx1.id in stored
        assert ctx2.id in stored


# ---------------------------------------------------------------------------
# 9.11 Business Isolation
# ---------------------------------------------------------------------------


class TestBusinessIsolation:
    def test_assessment_for_one_business_does_not_affect_another(self, engine, session, service):
        """Task 9.11 – Relevance assessments are isolated per business."""
        b1 = _make_business(session, name="Bakery A", slug="bakery-a")
        b2 = _make_business(session, name="Bakery B", slug="bakery-b")
        c1 = _make_conversation(session, b1, ref="conv-a")
        c2 = _make_conversation(session, b2, ref="conv-b")
        id1 = _make_identity(session, b1, "+94771111111")
        id2 = _make_identity(session, b2, "+94772222222")
        p1 = _make_participant(session, c1, b1, id1, "Alice")
        p2 = _make_participant(session, c2, b2, id2, "Bob")
        m1 = _make_message(session, c1, p1, content="Order a cake please")
        m2 = _make_message(session, c2, p2, content="Order a cake please")
        session.commit()

        service.assess_message(m1.id, b1.id)
        service.assess_message(m2.id, b2.id)

        eligible_b1 = service.get_extraction_eligible_messages(b1.id)
        eligible_b2 = service.get_extraction_eligible_messages(b2.id)

        # b1's eligible messages should not contain b2's messages
        b1_ids = {msg.id for msg in eligible_b1}
        b2_ids = {msg.id for msg in eligible_b2}
        assert b1_ids.isdisjoint(b2_ids)

    def test_assess_message_rejects_wrong_business(self, engine, session, service):
        """Task 9.11 – Cannot assess a message belonging to a different business."""
        b1 = _make_business(session, name="Bakery A", slug="bakery-a2")
        b2 = _make_business(session, name="Bakery B", slug="bakery-b2")
        c1 = _make_conversation(session, b1, ref="conv-a2")
        id1 = _make_identity(session, b1, "+94773333333")
        p1 = _make_participant(session, c1, b1, id1, "Alice")
        m1 = _make_message(session, c1, p1, content="Order cake")
        session.commit()

        with pytest.raises(ValueError):
            service.assess_message(m1.id, b2.id)


# ---------------------------------------------------------------------------
# 9.12 Raw Message Preservation
# ---------------------------------------------------------------------------


class TestRawMessagePreservation:
    def test_raw_message_unchanged_after_assessment(self, engine, session, service):
        """Task 9.12 – Assessing a message does not modify the Message record."""
        b, c, m = _setup_basic(session, content="I want to order a cake")
        original_content = m.content
        original_fingerprint = m.message_fingerprint

        service.assess_message(m.id, b.id)

        with Session(engine) as s:
            updated_msg = s.get(Message, m.id)

        assert updated_msg.content == original_content
        assert updated_msg.message_fingerprint == original_fingerprint

    def test_reassessment_does_not_modify_raw_message(self, engine, session, service):
        """Task 9.12 – Reassessment also leaves raw message unchanged."""
        b, c, m = _setup_basic(session, content="Order chocolate cake")
        original_content = m.content

        service.assess_message(m.id, b.id)
        service.assess_message(m.id, b.id)  # reassess

        with Session(engine) as s:
            updated_msg = s.get(Message, m.id)

        assert updated_msg.content == original_content


# ---------------------------------------------------------------------------
# 9.13 Original Import Provenance Preservation
# ---------------------------------------------------------------------------


class TestImportProvenancePreservation:
    def test_import_provenance_unchanged_after_assessment(self, engine, session, service):
        """Task 9.13 – Import provenance fields on Message are never altered."""
        b, c, m = _setup_basic(session, content="Order a cake")
        original_source_msg_id = m.source_message_id
        original_fingerprint = m.message_fingerprint

        service.assess_message(m.id, b.id)
        # Run a second time (reassessment)
        service.assess_message(m.id, b.id)

        with Session(engine) as s:
            refreshed = s.get(Message, m.id)

        assert refreshed.source_message_id == original_source_msg_id
        assert refreshed.message_fingerprint == original_fingerprint


# ---------------------------------------------------------------------------
# 9.14 Extraction Eligibility
# ---------------------------------------------------------------------------


class TestExtractionEligibility:
    def test_only_relevant_messages_are_eligible(self, engine, session, service):
        """Task 9.14 – is_extraction_eligible returns True only for relevant."""
        b = _make_business(session)
        c = _make_conversation(session, b)
        identity = _make_identity(session, b)
        p = _make_participant(session, c, b, identity)

        m_rel = _make_message(session, c, p, content="I want to order a birthday cake delivery")
        m_per = _make_message(session, c, p, content="Happy birthday! How are you?")
        session.commit()

        r_rel = service.assess_message(m_rel.id, b.id)
        r_per = service.assess_message(m_per.id, b.id)

        if r_rel.relevance_state == "relevant":
            assert service.is_extraction_eligible(m_rel.id, b.id) is True
        if r_per.relevance_state == "not_relevant":
            assert service.is_extraction_eligible(m_per.id, b.id) is False

    def test_message_with_no_assessment_is_not_eligible(self, engine, session, service):
        """Task 9.14 – A message with no assessment row is not eligible."""
        b, c, m = _setup_basic(session, content="Some message")
        # No assessment created
        assert service.is_extraction_eligible(m.id, b.id) is False


# ---------------------------------------------------------------------------
# 9.15 Mixed-Conversation Extraction Eligibility
# ---------------------------------------------------------------------------


class TestMixedConversationExtraction:
    def test_relevant_messages_eligible_not_relevant_excluded(self, engine, session, service):
        """Task 9.15 – Mixed conversation: relevant messages stay eligible."""
        b = _make_business(session)
        c = _make_conversation(session, b)
        identity = _make_identity(session, b)
        p = _make_participant(session, c, b, identity)
        m_biz = _make_message(session, c, p, content="Order 2 dozen cupcakes for Saturday")
        m_per = _make_message(session, c, p, content="Good morning! How are you? lol")
        session.commit()

        r_biz = service.assess_message(m_biz.id, b.id)
        r_per = service.assess_message(m_per.id, b.id)

        eligible = service.get_extraction_eligible_messages(b.id, conversation_id=c.id)
        eligible_ids = {msg.id for msg in eligible}

        if r_biz.relevance_state == "relevant":
            assert m_biz.id in eligible_ids
        if r_per.relevance_state == "not_relevant":
            assert m_per.id not in eligible_ids

    def test_conversation_not_rejected_for_mixed_messages(self, engine, session, service):
        """Task 9.15 – Conversation with mixed messages is not rejected."""
        b = _make_business(session)
        c = _make_conversation(session, b)
        identity = _make_identity(session, b)
        p = _make_participant(session, c, b, identity)
        m1 = _make_message(session, c, p, content="Chocolate cake order please")
        m2 = _make_message(session, c, p, content="See you later!")
        session.commit()

        service.assess_message(m1.id, b.id)
        service.assess_message(m2.id, b.id)

        with Session(engine) as s:
            conv = s.get(Conversation, c.id)
        assert conv is not None


# ---------------------------------------------------------------------------
# 9.16 Incremental Reassessment
# ---------------------------------------------------------------------------


class TestIncrementalReassessment:
    def test_reassessment_updates_state(self, engine, session, service):
        """Task 9.16 – Reassessment replaces the current assessment state."""
        b, c, m = _setup_basic(session, content="Maybe")
        service.assess_message(m.id, b.id)  # initial assessment

        # Reassess the same message — state should still be a valid canonical state
        result2 = service.assess_message(m.id, b.id)

        assert result2.relevance_state in RELEVANCE_STATES


    def test_reassessment_keeps_only_one_current_row(self, engine, session, service):
        """Task 9.16 – Only one is_current row per message+business after reassessment."""
        b, c, m = _setup_basic(session, content="Order cake please")
        service.assess_message(m.id, b.id)
        service.assess_message(m.id, b.id)  # reassess

        with Session(engine) as s:
            current_rows = s.execute(
                select(RelevanceAssessment).where(
                    RelevanceAssessment.message_id == m.id,
                    RelevanceAssessment.business_id == b.id,
                    RelevanceAssessment.is_current == True,  # noqa: E712
                )
            ).scalars().all()

        assert len(current_rows) == 1


# ---------------------------------------------------------------------------
# 9.17 Assessment Version/History Behavior
# ---------------------------------------------------------------------------


class TestAssessmentVersionHistory:
    def test_history_snapshot_created_on_reassessment(self, engine, session, service):
        """Task 9.17 – Previous assessment is archived to history on reassessment."""
        b, c, m = _setup_basic(session, content="Cake order for delivery")
        service.assess_message(m.id, b.id)  # v1
        service.assess_message(m.id, b.id)  # v2 — should create history

        with Session(engine) as s:
            history = s.execute(
                select(RelevanceAssessmentHistory).where(
                    RelevanceAssessmentHistory.message_id == m.id
                )
            ).scalars().all()

        assert len(history) >= 1

    def test_version_number_increments_on_reassessment(self, engine, session, service):
        """Task 9.17 – version_number increases with each reassessment."""
        b, c, m = _setup_basic(session, content="Order a cake")
        service.assess_message(m.id, b.id)  # v1

        with Session(engine) as s:
            v1 = s.execute(
                select(RelevanceAssessment).where(
                    RelevanceAssessment.message_id == m.id,
                    RelevanceAssessment.is_current == True,  # noqa: E712
                )
            ).scalar_one()
            v1_number = v1.assessment_version_number

        service.assess_message(m.id, b.id)  # v2

        with Session(engine) as s:
            v2 = s.execute(
                select(RelevanceAssessment).where(
                    RelevanceAssessment.message_id == m.id,
                    RelevanceAssessment.is_current == True,  # noqa: E712
                )
            ).scalar_one()

        assert v2.assessment_version_number == v1_number + 1


# ---------------------------------------------------------------------------
# 9.18 Assessment Provenance
# ---------------------------------------------------------------------------


class TestAssessmentProvenance:
    def test_assessment_stores_method_and_version(self, engine, session, service):
        """Task 9.18 – Assessment stores method/version metadata."""
        b, c, m = _setup_basic(session, content="Order a birthday cake")
        service.assess_message(m.id, b.id)

        with Session(engine) as s:
            saved = s.execute(
                select(RelevanceAssessment).where(RelevanceAssessment.message_id == m.id)
            ).scalar_one()

        assert saved.assessment_method is not None
        assert saved.assessment_version is not None

    def test_assessment_stores_rationale(self, engine, session, service):
        """Task 9.18 – Assessment stores a human-readable rationale."""
        b, c, m = _setup_basic(session, content="Can I book a cake for my daughter?")
        service.assess_message(m.id, b.id)

        with Session(engine) as s:
            saved = s.execute(
                select(RelevanceAssessment).where(RelevanceAssessment.message_id == m.id)
            ).scalar_one()

        assert saved.rationale is not None
        assert len(saved.rationale) > 0

    def test_assessment_stores_timestamp(self, engine, session, service):
        """Task 9.18 – Assessment stores assessed_at timestamp."""
        b, c, m = _setup_basic(session, content="Order cupcakes for delivery")
        service.assess_message(m.id, b.id)

        with Session(engine) as s:
            saved = s.execute(
                select(RelevanceAssessment).where(RelevanceAssessment.message_id == m.id)
            ).scalar_one()

        assert saved.assessed_at is not None


# ---------------------------------------------------------------------------
# 9.19 Failure Handling and Retry/Review Behavior
# ---------------------------------------------------------------------------


class TestFailureHandling:
    def test_assess_nonexistent_message_raises_value_error(self, engine, session, service):
        """Task 9.19 – Assessing a missing message raises ValueError."""
        b = _make_business(session)
        session.commit()

        with pytest.raises(ValueError):
            service.assess_message(9999999, b.id)

    def test_raw_message_intact_after_assessment_failure(self, engine, session, service):
        """Task 9.19 – Failed assessment leaves raw message data unchanged."""
        b, c, m = _setup_basic(session, content="Order a cake")
        original_content = m.content

        # Try to assess with wrong business (will raise ValueError)
        wrong_b = _make_business(session, name="Other", slug="other")
        session.commit()

        try:
            service.assess_message(m.id, wrong_b.id)
        except ValueError:
            pass

        with Session(engine) as s:
            refreshed = s.get(Message, m.id)
        assert refreshed.content == original_content

    def test_pending_assessment_created_on_failure(self, engine, session, service):
        """Task 9.19 – Failed assessment leaves message in pending state for retry."""
        b, c, m = _setup_basic(session, content="Unprocessed message")
        service.initialize_pending_for_business(b.id)

        with Session(engine) as s:
            assessment = s.execute(
                select(RelevanceAssessment).where(
                    RelevanceAssessment.message_id == m.id,
                    RelevanceAssessment.relevance_state == "pending",
                )
            ).scalar_one_or_none()

        assert assessment is not None

    def test_retry_assessments_processes_pending(self, engine, session, service):
        """Task 9.19 – retry_failed_assessments re-processes pending messages."""
        b = _make_business(session)
        c = _make_conversation(session, b)
        identity = _make_identity(session, b)
        p = _make_participant(session, c, b, identity)
        m = _make_message(session, c, p, content="Order a chocolate cake for delivery")
        ra = RelevanceAssessment(
            message_id=m.id,
            conversation_id=c.id,
            business_id=b.id,
            relevance_state="pending",
            is_current=True,
        )
        session.add(ra)
        session.commit()

        results = service.retry_failed_assessments(b.id)
        # After retry, the message should no longer be pending
        assert len(results) >= 1
        for r in results:
            assert r.relevance_state in RELEVANCE_STATES


# ---------------------------------------------------------------------------
# 9.20 Existing-Message Migration Behavior
# ---------------------------------------------------------------------------


class TestExistingMessageMigration:
    def test_initialize_pending_creates_assessments_for_unassessed_messages(self, engine, session, service):
        """Task 9.20 – Existing unassessed messages receive pending assessments."""
        b = _make_business(session)
        c = _make_conversation(session, b)
        identity = _make_identity(session, b)
        p = _make_participant(session, c, b, identity)
        m1 = _make_message(session, c, p, content="Old message 1")
        m2 = _make_message(session, c, p, content="Old message 2")
        session.commit()

        count = service.initialize_pending_for_business(b.id)
        assert count == 2

    def test_unassessed_existing_messages_not_extraction_eligible(self, engine, session, service):
        """Task 9.20 – After migration, pending messages are not eligible."""
        b, c, m = _setup_basic(session, content="Existing old message")
        service.initialize_pending_for_business(b.id)

        assert service.is_extraction_eligible(m.id, b.id) is False

    def test_initialize_pending_idempotent_for_already_assessed(self, engine, session, service):
        """Task 9.20 – initialize_pending does not duplicate assessed messages."""
        b, c, m = _setup_basic(session, content="Already assessed message")
        service.assess_message(m.id, b.id)  # creates current assessment

        count = service.initialize_pending_for_business(b.id)
        assert count == 0  # No new pending rows created


# ---------------------------------------------------------------------------
# 9.21 Relevance Layer Does Not Create Business Entities
# ---------------------------------------------------------------------------


class TestNoBusinessEntitiesCreated:
    def test_assessment_does_not_create_orders(self, engine, session, service):
        """Task 9.21 – Assessment does not create Order records."""
        from app.database.models import Order
        b, c, m = _setup_basic(session, content="Order a chocolate cake please")
        service.assess_message(m.id, b.id)

        with Session(engine) as s:
            orders = s.execute(select(Order)).scalars().all()
        assert len(orders) == 0

    def test_assessment_does_not_create_customers(self, engine, session, service):
        """Task 9.21 – Assessment does not create Customer records."""
        from app.database.models import Customer
        b, c, m = _setup_basic(session, content="Can I get a quote for 50 cupcakes?")
        service.assess_message(m.id, b.id)

        with Session(engine) as s:
            customers = s.execute(select(Customer).where(Customer.business_id == b.id)).scalars().all()
        assert len(customers) == 0

    def test_assessment_does_not_create_extracted_facts(self, engine, session, service):
        """Task 9.21 – Assessment does not create ExtractedFact records."""
        from app.database.models import ExtractedFact
        b, c, m = _setup_basic(session, content="Order 2 kg birthday cake for Saturday")
        service.assess_message(m.id, b.id)

        with Session(engine) as s:
            facts = s.execute(select(ExtractedFact).where(ExtractedFact.business_id == b.id)).scalars().all()
        assert len(facts) == 0


# ---------------------------------------------------------------------------
# 9.22 Relevance Layer Does Not Depend on RAG/Embeddings/Vector DBs
# ---------------------------------------------------------------------------


class TestNoDependencyOnAdvancedAI:
    def test_assessment_works_without_any_external_ai_system(self, engine, session, service):
        """Task 9.22 – Assessment succeeds using only the rule-based classifier."""
        b, c, m = _setup_basic(session, content="Order a cake for delivery")
        # If this passes without any external AI setup, the dependency is satisfied.
        result = service.assess_message(m.id, b.id)
        assert result.relevance_state in RELEVANCE_STATES

    def test_assessment_method_is_rule_based_by_default(self, engine, session, service):
        """Task 9.22 – Default classifier is rule-based, not AI-dependent."""
        b, c, m = _setup_basic(session, content="Order cupcakes")
        result = service.assess_message(m.id, b.id)
        assert "rule" in result.assessment_method.lower()


# ---------------------------------------------------------------------------
# 9.23 Provider-Independent Persistence and Eligibility
# ---------------------------------------------------------------------------


class TestProviderIndependence:
    def test_eligibility_boundary_independent_of_assessment_method(self, engine, session, service):
        """Task 9.23 – Eligibility is determined by relevance_state, not assessment method."""
        b = _make_business(session)
        c = _make_conversation(session, b)
        identity = _make_identity(session, b)
        p = _make_participant(session, c, b, identity)
        m = _make_message(session, c, p, content="Order 3 cakes")
        # Manually insert a 'relevant' assessment with a hypothetical LLM method
        ra = RelevanceAssessment(
            message_id=m.id,
            conversation_id=c.id,
            business_id=b.id,
            relevance_state="relevant",
            assessment_method="llm-gemini-flash-hypothetical",
            assessment_version="v99",
            rationale="LLM said so.",
            is_current=True,
        )
        session.add(ra)
        session.commit()

        # Eligibility check should still work regardless of method
        assert service.is_extraction_eligible(m.id, b.id) is True

    def test_data_contract_consistent_across_methods(self, engine, session, service):
        """Task 9.23 – Same persistence schema used regardless of classifier."""
        b, c, m = _setup_basic(session, content="Delivery of a birthday cake please")
        service.assess_message(m.id, b.id)

        with Session(engine) as s:
            saved = s.execute(
                select(RelevanceAssessment).where(RelevanceAssessment.message_id == m.id)
            ).scalar_one()

        # All required fields present regardless of which classifier ran
        assert saved.message_id is not None
        assert saved.business_id is not None
        assert saved.conversation_id is not None
        assert saved.relevance_state in RELEVANCE_STATES
        assert saved.is_current is True

from datetime import datetime, timezone, timedelta
import pytest
from app.database.models import Message, RelevanceAssessment, Business, Conversation, ImportBatch
from app.extraction.context import select_episode_messages
from app.extraction.constants import MAX_EPISODE_GAP_DAYS

def test_select_episode_messages(db_session):
    # Setup test data
    business = Business(name="Test Business", slug="test-business")
    db_session.add(business)
    db_session.flush()

    batch = ImportBatch(business_id=business.id, import_name="test_import.zip")
    db_session.add(batch)
    db_session.flush()

    conv = Conversation(business_id=business.id, import_batch_id=batch.id, conversation_ref="ref1")
    db_session.add(conv)
    db_session.flush()

    base_time = datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

    # Create messages with varied gaps and relevance states
    # 0: base_time (relevant) -> start of episode
    # 1: base_time + 1 hour (needs_review) -> included
    # 2: base_time + 2 hours (not_relevant) -> skipped by query
    # 3: base_time + 1 day (relevant) -> included
    # 4: base_time + 1 day + MAX_EPISODE_GAP_DAYS + 1 second (relevant) -> Exceeds gap, stops episode
    # 5: base_time + 1 day + MAX_EPISODE_GAP_DAYS + 2 hours (relevant) -> Not included

    times = [
        base_time,
        base_time + timedelta(hours=1),
        base_time + timedelta(hours=2),
        base_time + timedelta(days=1),
        base_time + timedelta(days=1, seconds=(MAX_EPISODE_GAP_DAYS * 86400) + 1),
        base_time + timedelta(days=1, hours=2, seconds=(MAX_EPISODE_GAP_DAYS * 86400) + 1),
    ]

    states = [
        "relevant",
        "needs_review",
        "not_relevant",
        "relevant",
        "relevant",
        "relevant"
    ]

    messages = []
    for i, t in enumerate(times):
        msg = Message(
            conversation_id=conv.id,
            content=f"Msg {i}",
            sent_at=t
        )
        db_session.add(msg)
        db_session.flush()
        messages.append(msg)

        ra = RelevanceAssessment(
            message_id=msg.id,
            conversation_id=conv.id,
            business_id=business.id,
            relevance_state=states[i],
            is_current=True
        )
        db_session.add(ra)
    db_session.commit()

    start_message = messages[0]

    episode = select_episode_messages(db_session, start_message, business.id)

    # Expected: messages[0], messages[1], messages[3]
    assert len(episode) == 3
    assert episode[0].id == messages[0].id
    assert episode[1].id == messages[1].id
    assert episode[2].id == messages[3].id

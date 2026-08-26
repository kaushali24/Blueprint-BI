from datetime import timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.models import Message, RelevanceAssessment
from app.extraction.constants import (
    CONTEXT_ALLOWED_STATES,
    MAX_EPISODE_GAP_DAYS,
)

def select_episode_messages(session: Session, start_message: Message, business_id: int) -> list[Message]:
    """Select all messages belonging to the business episode starting at start_message."""
    
    # Query all eligible messages in the conversation from the start_message onwards
    stmt = (
        select(Message)
        .join(RelevanceAssessment, Message.id == RelevanceAssessment.message_id)
        .where(
            Message.conversation_id == start_message.conversation_id,
            Message.sent_at >= start_message.sent_at,
            RelevanceAssessment.business_id == business_id,
            RelevanceAssessment.is_current == True,
            RelevanceAssessment.relevance_state.in_(CONTEXT_ALLOWED_STATES),
        )
        .order_by(Message.sent_at.asc(), Message.id.asc())
    )
    
    candidate_messages = session.scalars(stmt).all()
    episode_messages = []
    
    for i, msg in enumerate(candidate_messages):
        if i > 0:
            prev_msg = episode_messages[-1]
            if msg.sent_at and prev_msg.sent_at:
                gap = msg.sent_at - prev_msg.sent_at
                if gap > timedelta(days=MAX_EPISODE_GAP_DAYS):
                    # Gap exceeds threshold, end of episode
                    break
        episode_messages.append(msg)
        
    return episode_messages

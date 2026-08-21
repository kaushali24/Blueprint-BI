from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.models import Message, RelevanceAssessment
from app.extraction.constants import (
    CONTEXT_ALLOWED_STATES,
    CONTEXT_WINDOW_BEFORE,
    CONTEXT_WINDOW_AFTER,
)

def select_context_window(session: Session, target_message: Message, business_id: int) -> tuple[Message, list[Message]]:
    """Select a bounded window of relevant context messages around a target message."""
    
    # Query all eligible messages in the conversation ordered by sent_at
    stmt = (
        select(Message)
        .join(RelevanceAssessment, Message.id == RelevanceAssessment.message_id)
        .where(
            Message.conversation_id == target_message.conversation_id,
            RelevanceAssessment.business_id == business_id,
            RelevanceAssessment.is_current == True,
            RelevanceAssessment.relevance_state.in_(CONTEXT_ALLOWED_STATES),
        )
        .order_by(Message.sent_at.asc(), Message.id.asc())
    )
    
    # Actually wait, Message doesn't have business_id?
    # Message has conversation_id. Conversation has business_id.
    # RelevanceAssessment has business_id.
    
    all_eligible = session.scalars(stmt).all()
    
    # Find the target message index
    target_idx = -1
    for i, msg in enumerate(all_eligible):
        if msg.id == target_message.id:
            target_idx = i
            break
            
    if target_idx == -1:
        # Target message might not be in the eligible list if it's somehow not in CONTEXT_ALLOWED_STATES,
        # but the spec says "Always includes the target message". So we must ensure it is included.
        # However, the task says: "Filters: include only messages with current RelevanceAssessment in CONTEXT_ALLOWED_STATES."
        # If target is eligible, it's found.
        # Just return target and only target if not found in list (shouldn't happen for eligible targets)
        return target_message, [target_message]
        
    start_idx = max(0, target_idx - CONTEXT_WINDOW_BEFORE)
    end_idx = min(len(all_eligible), target_idx + CONTEXT_WINDOW_AFTER + 1)
    
    context_messages = all_eligible[start_idx:end_idx]
    
    return target_message, list(context_messages)

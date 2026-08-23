from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.models import Message
from app.extraction.exceptions import ExtractionEvidenceError
from app.extraction.schemas import (
    CandidateOrder,
    CandidateOrderItem,
    CandidateInquiry,
    CandidateFeedback,
    CandidateFact
)

def validate_evidence_ids(session: Session, candidate: CandidateOrder | CandidateInquiry | CandidateFeedback | CandidateFact, conversation_id: int, business_id: int) -> None:
    """Validate that all evidence message IDs exist and belong to the correct conversation/business.
    
    Raises ExtractionEvidenceError if ANY ID is invalid.
    """
    evidence_ids = candidate.evidence_message_ids
    if not evidence_ids:
        raise ExtractionEvidenceError("Candidate has no evidence_message_ids")

    # Fetch messages
    stmt = select(Message).where(Message.id.in_(evidence_ids))
    messages = session.scalars(stmt).all()
    
    if len(messages) != len(set(evidence_ids)):
        # Some IDs don't exist
        found_ids = {m.id for m in messages}
        missing = set(evidence_ids) - found_ids
        raise ExtractionEvidenceError(f"Evidence message IDs not found: {missing}")
        
    for msg in messages:
        if msg.conversation_id != conversation_id:
            raise ExtractionEvidenceError(f"Evidence message {msg.id} belongs to wrong conversation {msg.conversation_id}")
        # Note: Message does not have business_id, we check Conversation.business_id
        # To avoid extra joins if we already know conversation_id is correct and the conversation
        # belongs to the correct business_id, we just check conversation_id. 
        # But wait, the task says: "belongs to the correct conversation AND business."
        # If conversation_id is checked against the target's conversation_id, and the target's conversation
        # belongs to the business, then it implicitly belongs to the business.
        # But to be completely safe, we can join Conversation.
        if msg.conversation.business_id != business_id:
            raise ExtractionEvidenceError(f"Evidence message {msg.id} belongs to wrong business")


def check_business_consistency(candidate: CandidateOrder | CandidateInquiry | CandidateFeedback | CandidateFact) -> list[str]:
    """Returns a list of error strings for a candidate."""
    errors = []
    
    if isinstance(candidate, CandidateOrder):
        if candidate.status == 'confirmed' and not candidate.items:
            errors.append("Confirmed order must have at least one item")
        for item in candidate.items:
            if not item.product_name or not item.product_name.strip():
                errors.append("OrderItem must have non-empty product_name")
            if item.quantity <= 0:
                errors.append("OrderItem quantity must be > 0")
            # unit_price = None is valid, line_total = None is valid
            
    elif isinstance(candidate, CandidateInquiry):
        if not candidate.inquiry_type or not candidate.inquiry_type.strip():
            errors.append("Inquiry must have non-empty inquiry_type")
        if not candidate.summary or not candidate.summary.strip():
            errors.append("Inquiry must have non-empty summary")
            
    elif isinstance(candidate, CandidateFeedback):
        if not candidate.sentiment or not candidate.sentiment.strip():
            errors.append("Feedback must have non-empty sentiment")
        if not candidate.topic or not candidate.topic.strip():
            errors.append("Feedback must have non-empty topic")
        if not candidate.comment or not candidate.comment.strip():
            errors.append("Feedback must have non-empty comment")
            
    return errors

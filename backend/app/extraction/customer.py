from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.models import Message, Participant, WhatsAppIdentity

def resolve_customer(session: Session, target_message: Message) -> int | None:
    """Resolve the customer_id associated with a message, if any."""
    if not target_message.participant_id:
        return None
        
    stmt = (
        select(WhatsAppIdentity.customer_id)
        .join(Participant, Participant.whatsapp_identity_id == WhatsAppIdentity.id)
        .where(Participant.id == target_message.participant_id)
    )
    
    return session.execute(stmt).scalar_one_or_none()

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.models import Message, Participant, WhatsAppIdentity, Customer, Conversation

def resolve_customer(session: Session, target_message: Message) -> int | None:
    """Resolve the customer_id associated with a conversation, creating one if needed."""
    
    # 1. Check if the conversation already has any participants linked to a Customer.
    stmt = (
        select(Customer.id)
        .join(WhatsAppIdentity, WhatsAppIdentity.customer_id == Customer.id)
        .join(Participant, Participant.whatsapp_identity_id == WhatsAppIdentity.id)
        .where(Participant.conversation_id == target_message.conversation_id)
    )
    existing_customer_id = session.execute(stmt).scalar_one_or_none()
    
    if existing_customer_id:
        return existing_customer_id

    # 2. If no customer exists, we need to create one for the "customer" participant.
    participants = session.execute(
        select(Participant, WhatsAppIdentity)
        .join(WhatsAppIdentity, Participant.whatsapp_identity_id == WhatsAppIdentity.id)
        .where(Participant.conversation_id == target_message.conversation_id)
    ).all()
    
    if not participants:
        return None
        
    conversation = session.execute(
        select(Conversation).where(Conversation.id == target_message.conversation_id)
    ).scalar_one_or_none()
    
    if not conversation:
        return None
        
    customer_participant = None
    
    # Heuristic 1: If the participant's display name is in the conversation_ref (e.g., "WhatsApp Chat with Dilhani")
    conv_ref_lower = conversation.conversation_ref.lower()
    for p, ident in participants:
        # Ignore common filler words in the ref
        if p.display_name.lower() in conv_ref_lower and p.display_name.lower() != "whatsapp":
            customer_participant = (p, ident)
            break
            
    # Heuristic 2: Pick the participant who sent the very first message in the conversation
    if not customer_participant:
        first_msg = session.execute(
            select(Message)
            .where(Message.conversation_id == target_message.conversation_id)
            .order_by(Message.sent_at.asc(), Message.id.asc())
            .limit(1)
        ).scalar_one_or_none()
        
        if first_msg and first_msg.participant_id:
            for p, ident in participants:
                if p.id == first_msg.participant_id:
                    customer_participant = (p, ident)
                    break
                    
    # Fallback: just pick the first participant
    if not customer_participant and participants:
        customer_participant = participants[0]
        
    if customer_participant:
        p, ident = customer_participant
        
        # Determine if the whatsapp_number is an actual number or just the display name fallback
        phone = ident.whatsapp_number if ident.whatsapp_number != p.display_name else None
        
        # Create the Customer
        new_customer = Customer(
            business_id=conversation.business_id,
            name=p.display_name,
            phone_number=phone
        )
        session.add(new_customer)
        session.flush()
        
        # Link the identity
        ident.customer_id = new_customer.id
        session.flush()
        
        return new_customer.id
        
    return None


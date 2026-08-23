from app.database.models import Message

def compile_extraction_prompt(target_message: Message, context_messages: list[Message]) -> str:
    """Compile the LLM prompt for extraction."""
    
    prompt = "Extract business entities from the target message, using the context messages for reference.\n\n"
    
    prompt += "CONTEXT MESSAGES:\n"
    for msg in context_messages:
        if msg.id == target_message.id:
            # We skip it here to make it distinct, or label it
            continue
        sender = msg.participant.display_name if msg.participant else "Unknown"
        time_str = msg.sent_at.isoformat() if msg.sent_at else "Unknown time"
        content = msg.content or ""
        prompt += f"[{time_str}] {sender} (ID: {msg.id}): {content}\n"
        
    prompt += "\nTARGET MESSAGE:\n"
    sender = target_message.participant.display_name if target_message.participant else "Unknown"
    time_str = target_message.sent_at.isoformat() if target_message.sent_at else "Unknown time"
    content = target_message.content or ""
    prompt += f"[{time_str}] {sender} (ID: {target_message.id}): {content}\n"
    
    prompt += """
EXTRACTION RULES:
1. Identify Orders, Inquiries, Feedback, or Facts based on the TARGET MESSAGE.
2. Provide evidence_message_ids. Only use message IDs from the context or target.
3. For Orders:
   - Must have at least one product with quantity > 0.
   - If price is not explicitly mentioned, omit it or use null.
   - Status must be one of: inquiry, pending, confirmed, cancelled.
4. If there is no clear business entity in the target message, return empty lists.
"""
    return prompt

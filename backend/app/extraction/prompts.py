from app.database.models import Message

def compile_extraction_prompt(context_messages: list[Message]) -> str:
    """Compile the LLM prompt for episode extraction."""
    
    prompt = "Extract the final, consolidated business state from the following business episode.\n\n"
    prompt += "A business episode is a sequence of related messages. The transaction may evolve, add items, cancel items, or change prices across these messages.\n"
    prompt += "Your job is to output the final, resolved state of the transaction. Do NOT output cancelled items. If an inquiry later became a confirmed order, output only the confirmed order.\n\n"
    
    prompt += "EPISODE MESSAGES:\n"
    for msg in context_messages:
        sender = msg.participant.display_name if msg.participant else "Unknown"
        time_str = msg.sent_at.isoformat() if msg.sent_at else "Unknown time"
        content = msg.content or ""
        prompt += f"[{time_str}] {sender} (ID: {msg.id}): {content}\n"
        
    prompt += """
EXTRACTION RULES:
1. Identify Orders, Inquiries, Feedback, or Facts based on the ENTIRE episode.
   - INQUIRY: The customer is primarily gathering information and there is not yet enough concrete purchase intent to represent an order candidate. (Return as CandidateInquiry, NOT an Order).
   - PENDING ORDER: There is a concrete order candidate or purchase intent (e.g. asking for a specific item, quantity, date, or requesting a quote) but it is not explicitly finalized or accepted.
   - CONFIRMED ORDER: There is sufficient explicit evidence that the order was accepted, confirmed, or agreed upon by both parties.
2. Provide evidence_message_ids that support the final entity state. Only use message IDs from the episode.
3. For Orders:
   - Must have at least one product with quantity > 0.
   - If price is not explicitly mentioned, omit it or use null. Do not guess.
   - Status must be one of: pending, confirmed, cancelled.
   - Exclude any items that the customer or business cancelled during the episode.
4. If there is no clear business entity in the episode, return empty lists.
"""
    return prompt

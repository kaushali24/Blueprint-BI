from sqlalchemy.orm import Session
from app.database.models import (
    Order, OrderItem, Inquiry, Feedback, ExtractedFact, ExtractionEvidence
)
from app.extraction.schemas import (
    CandidateOrder, CandidateInquiry, CandidateFeedback, CandidateFact
)
from app.extraction.constants import CONFIDENCE_REVIEW_THRESHOLD

def persist_extraction_results(
    session: Session,
    conversation_id: int,
    business_id: int,
    customer_id: int | None,
    orders: list[CandidateOrder],
    inquiries: list[CandidateInquiry],
    feedbacks: list[CandidateFeedback],
    facts: list[CandidateFact],
    extraction_target_id: int,
    model_name: str | None = None,
    model_version: str | None = None,
) -> None:
    """Persist all successfully validated extracted entities to the database."""
    
    # Collect all needed message IDs across all candidates
    all_message_ids = set()
    for candidate in orders:
        all_message_ids.update(candidate.evidence_message_ids)
        for item in candidate.items:
            all_message_ids.update(item.evidence_message_ids)
    for candidate in inquiries + feedbacks + facts:
        all_message_ids.update(candidate.evidence_message_ids)
        
    # Fetch message contents
    from sqlalchemy import select
    from app.database.models import Message
    message_contents = {}
    if all_message_ids:
        msgs = session.scalars(select(Message).where(Message.id.in_(all_message_ids))).all()
        message_contents = {m.id: m.content or "" for m in msgs}
        
    for candidate in orders:
        order = Order(
            business_id=business_id,
            conversation_id=conversation_id,
            customer_id=customer_id,
            status=candidate.status,
            total_amount=candidate.total_amount,
            extraction_target_id=extraction_target_id
        )
        session.add(order)
        session.flush() # get order.id
        
        # Collect all evidence IDs for the order and its items
        evidence_ids = set(candidate.evidence_message_ids)
        
        for candidate_item in candidate.items:
            line_total = None
            if candidate_item.unit_price is not None:
                line_total = candidate_item.quantity * candidate_item.unit_price
                
            item = OrderItem(
                order_id=order.id,
                product_name=candidate_item.product_name,
                quantity=candidate_item.quantity,
                unit_price=candidate_item.unit_price,
                line_total=line_total,
            )
            session.add(item)
            evidence_ids.update(candidate_item.evidence_message_ids)
            
        for msg_id in evidence_ids:
            evidence = ExtractionEvidence(
                message_id=msg_id, 
                order_id=order.id, 
                evidence_text=message_contents.get(msg_id, "")
            )
            session.add(evidence)
            
    for candidate in inquiries:
        status = candidate.status
        if candidate.confidence is not None and candidate.confidence < CONFIDENCE_REVIEW_THRESHOLD:
            status = 'needs_review'
            
        inquiry = Inquiry(
            business_id=business_id,
            conversation_id=conversation_id,
            customer_id=customer_id,
            inquiry_type=candidate.inquiry_type,
            summary=candidate.summary,
            status=status,
            extraction_target_id=extraction_target_id
        )
        session.add(inquiry)
        session.flush()
        
        for msg_id in set(candidate.evidence_message_ids):
            evidence = ExtractionEvidence(
                message_id=msg_id, 
                inquiry_id=inquiry.id,
                evidence_text=message_contents.get(msg_id, "")
            )
            session.add(evidence)
            
    for candidate in feedbacks:
        feedback = Feedback(
            business_id=business_id,
            conversation_id=conversation_id,
            customer_id=customer_id,
            sentiment=candidate.sentiment,
            topic=candidate.topic,
            comment=candidate.comment,
            extraction_target_id=extraction_target_id
        )
        session.add(feedback)
        session.flush()
        
        for msg_id in set(candidate.evidence_message_ids):
            evidence = ExtractionEvidence(
                message_id=msg_id, 
                feedback_id=feedback.id,
                evidence_text=message_contents.get(msg_id, "")
            )
            session.add(evidence)
            
    for candidate in facts:
        status = 'pending'
        if candidate.confidence is not None and candidate.confidence < CONFIDENCE_REVIEW_THRESHOLD:
            status = 'needs_review'
            
        fact = ExtractedFact(
            business_id=business_id,
            conversation_id=conversation_id,
            customer_id=customer_id,
            fact_type=candidate.fact_type,
            fact_value=candidate.fact_value,
            status=status,
            model_name=model_name,
            model_version=model_version,
            extraction_target_id=extraction_target_id
        )
        session.add(fact)
        session.flush()
        
        for msg_id in set(candidate.evidence_message_ids):
            evidence = ExtractionEvidence(
                message_id=msg_id, 
                extracted_fact_id=fact.id,
                evidence_text=message_contents.get(msg_id, "")
            )
            session.add(evidence)

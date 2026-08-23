from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.database.models import (
    Message, Conversation, ExtractionTarget, RelevanceAssessment,
    Order, Inquiry, Feedback, ExtractedFact
)
from app.extraction.context import select_episode_messages
from app.extraction.prompts import compile_extraction_prompt
from app.extraction.provider import LLMProvider
from app.extraction.schemas import ExtractionResult
from app.extraction.validation import validate_evidence_ids, check_business_consistency
from app.extraction.customer import resolve_customer
from app.extraction.persistence import persist_extraction_results
from app.extraction.exceptions import ExtractionEvidenceError, ExtractionConsistencyError
from app.extraction.constants import MAX_EPISODE_MESSAGES, CONTEXT_ALLOWED_STATES, MAX_EPISODE_GAP_DAYS

class ExtractionService:
    def __init__(self, provider: LLMProvider):
        self.provider = provider
        
    def find_episode_start_message(self, session: Session, msg: Message, business_id: int) -> Message | None:
        """Find the true starting message (must be 'relevant') of the business episode containing msg."""
        stmt = (
            select(Message, RelevanceAssessment.relevance_state)
            .join(RelevanceAssessment, Message.id == RelevanceAssessment.message_id)
            .where(
                Message.conversation_id == msg.conversation_id,
                Message.sent_at <= msg.sent_at,
                RelevanceAssessment.business_id == business_id,
                RelevanceAssessment.is_current == True,
                RelevanceAssessment.relevance_state.in_(CONTEXT_ALLOWED_STATES),
            )
            .order_by(Message.sent_at.desc(), Message.id.desc())
        )
        
        prior_messages = session.execute(stmt).all()
        if not prior_messages:
            return None
            
        episode_start_idx = 0
        for i in range(1, len(prior_messages)):
            prev_msg = prior_messages[i][0]
            curr_msg = prior_messages[i-1][0]
            
            if curr_msg.sent_at and prev_msg.sent_at:
                gap = curr_msg.sent_at - prev_msg.sent_at
                if gap > timedelta(days=MAX_EPISODE_GAP_DAYS):
                    break
            episode_start_idx = i
            
        # Walk forward from the start to find the first 'relevant' message.
        # prior_messages is descending, so episode_start_idx is the oldest message in the continuous chunk.
        # We walk backwards through the array (which is forwards in time)
        for i in range(episode_start_idx, -1, -1):
            m, state = prior_messages[i]
            if state == 'relevant':
                return m
                
        return None
        
    def extract_episode(self, session: Session, start_message: Message, business_id: int) -> ExtractionResult | None:
        """Run extraction pipeline for a full business episode starting at start_message."""
        
        # 1. Context Selection
        episode_msgs = select_episode_messages(session, start_message, business_id)
        if not episode_msgs:
            return None
            
        # Limit to configured budget
        if len(episode_msgs) > MAX_EPISODE_MESSAGES:
            episode_msgs = episode_msgs[:MAX_EPISODE_MESSAGES]
            
        end_message = episode_msgs[-1]
        
        # 2. Idempotency Check
        target_record = session.execute(
            select(ExtractionTarget).where(
                ExtractionTarget.conversation_id == start_message.conversation_id,
                ExtractionTarget.start_message_id == start_message.id,
                ExtractionTarget.business_id == business_id
            )
        ).scalar_one_or_none()
        
        if target_record is not None:
            if target_record.status == 'succeeded' and target_record.end_message_id == end_message.id:
                # Completely unchanged episode boundary
                return None
            
            target_record.status = 'pending'
            target_record.attempted_at = datetime.now(timezone.utc)
            target_record.end_message_id = end_message.id
        else:
            target_record = ExtractionTarget(
                business_id=business_id,
                conversation_id=start_message.conversation_id,
                start_message_id=start_message.id,
                end_message_id=end_message.id,
                status='pending',
                attempted_at=datetime.now(timezone.utc)
            )
            session.add(target_record)
            
        session.flush()
        
        try:
            # 3. Prompt Compilation
            prompt = compile_extraction_prompt(episode_msgs)
            schema = ExtractionResult.model_json_schema()
            
            # 4. LLM Call
            raw_response = self.provider.extract(prompt, schema)
            result = ExtractionResult.model_validate(raw_response)
            
            # 5. Validation
            valid_orders = []
            valid_inquiries = []
            valid_feedbacks = []
            valid_facts = []
            
            for order in result.orders:
                try:
                    validate_evidence_ids(session, order, start_message.conversation_id, business_id)
                    errors = check_business_consistency(order)
                    if errors:
                        raise ExtractionConsistencyError(str(errors))
                    valid_orders.append(order)
                except Exception:
                    pass
                    
            for inq in result.inquiries:
                try:
                    validate_evidence_ids(session, inq, start_message.conversation_id, business_id)
                    errors = check_business_consistency(inq)
                    if errors:
                        raise ExtractionConsistencyError(str(errors))
                    valid_inquiries.append(inq)
                except Exception:
                    pass
                    
            for fb in result.feedbacks:
                try:
                    validate_evidence_ids(session, fb, start_message.conversation_id, business_id)
                    errors = check_business_consistency(fb)
                    if errors:
                        raise ExtractionConsistencyError(str(errors))
                    valid_feedbacks.append(fb)
                except Exception:
                    pass
                    
            for fact in result.facts:
                try:
                    validate_evidence_ids(session, fact, start_message.conversation_id, business_id)
                    errors = check_business_consistency(fact)
                    if errors:
                        raise ExtractionConsistencyError(str(errors))
                    valid_facts.append(fact)
                except Exception:
                    pass
                    
            if not any([valid_orders, valid_inquiries, valid_feedbacks, valid_facts]):
                target_record.status = 'failed'
                target_record.failure_reason = "No valid candidates extracted"
                session.flush()
                return None
                
            # Atomic Replacement and Persistence
            with session.begin_nested():
                # 6. Delete previous derived records for this episode
                if target_record.id:
                    session.execute(delete(Order).where(Order.extraction_target_id == target_record.id))
                    session.execute(delete(Inquiry).where(Inquiry.extraction_target_id == target_record.id))
                    session.execute(delete(Feedback).where(Feedback.extraction_target_id == target_record.id))
                    session.execute(delete(ExtractedFact).where(ExtractedFact.extraction_target_id == target_record.id))
                    
                # 7. Customer Resolution
                customer_id = resolve_customer(session, start_message)
                
                # 8. Persistence
                model_name = getattr(self.provider, 'model_name', 'unknown')
                model_version = '1.0'
                
                persist_extraction_results(
                    session=session,
                    conversation_id=start_message.conversation_id,
                    business_id=business_id,
                    customer_id=customer_id,
                    orders=valid_orders,
                    inquiries=valid_inquiries,
                    feedbacks=valid_feedbacks,
                    facts=valid_facts,
                    extraction_target_id=target_record.id,
                    model_name=model_name,
                    model_version=model_version,
                )
                
                # 9. Mark Success
                target_record.status = 'succeeded'
                target_record.completed_at = datetime.now(timezone.utc)
            
            # Flush the completed state
            session.flush()
            
            final_result = ExtractionResult(
                target_message_id=start_message.id,
                context_message_ids=[m.id for m in episode_msgs],
                orders=valid_orders,
                inquiries=valid_inquiries,
                feedbacks=valid_feedbacks,
                facts=valid_facts,
            )
            return final_result
            
        except Exception as e:
            target_record.status = 'failed'
            target_record.failure_reason = str(e)
            session.flush()
            # If the provider fails, or insertion fails, previous valid state is preserved
            return None

    def extract_messages_for_import(self, session: Session, import_batch_id: int, business_id: int) -> int:
        """Extract all newly relevant episodes from a specific import batch.
        Returns the number of episodes successfully extracted.
        """
        # Find all current RelevanceAssessments for the batch that are 'relevant'
        relevant_messages = session.execute(
            select(Message)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .join(RelevanceAssessment, RelevanceAssessment.message_id == Message.id)
            .where(
                Message.import_batch_id == import_batch_id,
                Conversation.business_id == business_id,
                RelevanceAssessment.relevance_state == 'relevant',
                RelevanceAssessment.is_current == True
            )
            .order_by(Message.sent_at.asc(), Message.id.asc())
        ).scalars().all()
        
        extracted_count = 0
        processed_start_ids = set()
        
        for msg in relevant_messages:
            start_msg = self.find_episode_start_message(session, msg, business_id)
            if not start_msg:
                continue
                
            if start_msg.id in processed_start_ids:
                continue
            processed_start_ids.add(start_msg.id)
            
            try:
                with session.begin_nested():
                    result = self.extract_episode(session, start_msg, business_id)
                    if result is not None:
                        extracted_count += 1
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("Extraction failed for episode starting at msg %d: %s", start_msg.id, e)
                
        return extracted_count

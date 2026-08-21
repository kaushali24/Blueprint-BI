from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.models import Message, Conversation, ExtractionTarget, RelevanceAssessment
from app.extraction.context import select_context_window
from app.extraction.prompts import compile_extraction_prompt
from app.extraction.provider import LLMProvider
from app.extraction.schemas import ExtractionResult
from app.extraction.validation import validate_evidence_ids, check_business_consistency
from app.extraction.customer import resolve_customer
from app.extraction.persistence import persist_extraction_results
from app.extraction.exceptions import ExtractionEvidenceError, ExtractionConsistencyError

class ExtractionService:
    def __init__(self, provider: LLMProvider):
        self.provider = provider
        
    def is_eligible(self, session: Session, target_message: Message, business_id: int) -> bool:
        """Check if message is eligible for extraction."""
        ra = session.execute(
            select(RelevanceAssessment).where(
                RelevanceAssessment.message_id == target_message.id,
                RelevanceAssessment.business_id == business_id,
                RelevanceAssessment.is_current == True
            )
        ).scalar_one_or_none()
        
        return ra is not None and ra.relevance_state == 'relevant'
        
    def extract_from_message(self, session: Session, target_message: Message, business_id: int) -> ExtractionResult | None:
        """Run extraction pipeline for a single message."""
        
        # 1. Idempotency Check
        target_record = session.execute(
            select(ExtractionTarget).where(
                ExtractionTarget.message_id == target_message.id,
                ExtractionTarget.business_id == business_id
            )
        ).scalar_one_or_none()
        
        if target_record is not None:
            if target_record.status == 'succeeded':
                return None
            if target_record.status == 'failed':
                target_record.status = 'pending'
                target_record.attempted_at = datetime.now(timezone.utc)
        else:
            target_record = ExtractionTarget(
                message_id=target_message.id,
                business_id=business_id,
                status='pending',
                attempted_at=datetime.now(timezone.utc)
            )
            session.add(target_record)
            
        session.flush()
        
        try:
            # 2. Eligibility
            if not self.is_eligible(session, target_message, business_id):
                target_record.status = 'failed'
                target_record.failure_reason = "Message not eligible (not relevant)"
                session.flush()
                return None
                
            # 3. Context Selection
            t_msg, context_msgs = select_context_window(session, target_message, business_id)
            
            # 4. Prompt Compilation
            prompt = compile_extraction_prompt(t_msg, context_msgs)
            schema = ExtractionResult.model_json_schema()
            
            # 5. LLM Call
            raw_response = self.provider.extract(prompt, schema)
            result = ExtractionResult.model_validate(raw_response)
            
            # 6. Validation
            valid_orders = []
            valid_inquiries = []
            valid_feedbacks = []
            valid_facts = []
            
            for order in result.orders:
                try:
                    validate_evidence_ids(session, order, target_message.conversation_id, business_id)
                    errors = check_business_consistency(order)
                    if errors:
                        raise ExtractionConsistencyError(str(errors))
                    valid_orders.append(order)
                except Exception:
                    pass # Log or collect errors
                    
            for inq in result.inquiries:
                try:
                    validate_evidence_ids(session, inq, target_message.conversation_id, business_id)
                    errors = check_business_consistency(inq)
                    if errors:
                        raise ExtractionConsistencyError(str(errors))
                    valid_inquiries.append(inq)
                except Exception:
                    pass
                    
            for fb in result.feedbacks:
                try:
                    validate_evidence_ids(session, fb, target_message.conversation_id, business_id)
                    errors = check_business_consistency(fb)
                    if errors:
                        raise ExtractionConsistencyError(str(errors))
                    valid_feedbacks.append(fb)
                except Exception:
                    pass
                    
            for fact in result.facts:
                try:
                    validate_evidence_ids(session, fact, target_message.conversation_id, business_id)
                    errors = check_business_consistency(fact)
                    if errors:
                        raise ExtractionConsistencyError(str(errors))
                    valid_facts.append(fact)
                except Exception:
                    pass
                    
            if not any([valid_orders, valid_inquiries, valid_feedbacks, valid_facts]):
                # If everything was rejected or nothing was returned
                target_record.status = 'failed'
                target_record.failure_reason = "No valid candidates extracted"
                session.flush()
                return None
                
            # 7. Customer Resolution
            customer_id = resolve_customer(session, target_message)
            
            # 8. Persistence
            model_name = getattr(self.provider, 'model_name', 'unknown')
            model_version = '1.0' # Or from provider
            
            persist_extraction_results(
                session=session,
                conversation_id=target_message.conversation_id,
                business_id=business_id,
                customer_id=customer_id,
                orders=valid_orders,
                inquiries=valid_inquiries,
                feedbacks=valid_feedbacks,
                facts=valid_facts,
                model_name=model_name,
                model_version=model_version,
            )
            
            # 9. Mark Success
            target_record.status = 'succeeded'
            target_record.completed_at = datetime.now(timezone.utc)
            session.flush()
            
            # Create a new result representing only valid entities that were actually persisted
            final_result = ExtractionResult(
                target_message_id=target_message.id,
                context_message_ids=[m.id for m in context_msgs],
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
            return None

    def extract_messages_for_import(self, session: Session, import_batch_id: int, business_id: int) -> int:
        """Extract all newly relevant messages from a specific import batch.
        Returns the number of messages successfully extracted.
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
            .order_by(Message.id)
        ).scalars().all()
        
        extracted_count = 0
        for msg in relevant_messages:
            try:
                # We use a savepoint to ensure one failed extraction doesn't rollback the whole batch
                with session.begin_nested():
                    result = self.extract_from_message(session, msg, business_id)
                    if result is not None:
                        extracted_count += 1
            except Exception as e:
                # Log the exception, but continue with the next message
                import logging
                logging.getLogger(__name__).warning("Extraction failed for message %d: %s", msg.id, e)
                
        return extracted_count

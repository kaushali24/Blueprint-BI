import os
import sys
from dotenv import load_dotenv

# Add the backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.database.connection import session_scope
from app.extraction.service import ExtractionService
from app.extraction.provider import GeminiProvider
from app.database.models import Message, RelevanceAssessment, Conversation
from sqlalchemy import select

def main():
    load_dotenv()
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY is not set.")
        sys.exit(1)
        
    provider = GeminiProvider(api_key=api_key)
    service = ExtractionService(provider)
    
    business_id = 1
    
    with session_scope() as session:
        # Find all current RelevanceAssessments for the batch that are 'relevant'
        # We don't have import_batch_id, we just extract all relevant messages for Business 1
        relevant_messages = session.execute(
            select(Message)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .join(RelevanceAssessment, RelevanceAssessment.message_id == Message.id)
            .where(
                Conversation.business_id == business_id,
                RelevanceAssessment.relevance_state == 'relevant',
                RelevanceAssessment.is_current == True
            )
            .order_by(Message.sent_at.asc(), Message.id.asc())
        ).scalars().all()
        
        extracted_count = 0
        processed_start_ids = set()
        
        for msg in relevant_messages:
            start_msg = service.find_episode_start_message(session, msg, business_id)
            if not start_msg:
                continue
                
            if start_msg.id in processed_start_ids:
                continue
            processed_start_ids.add(start_msg.id)
            
            print(f"Extracting episode starting at message ID: {start_msg.id}")
            
            try:
                # Use subtransaction
                with session.begin_nested():
                    result = service.extract_episode(session, start_msg, business_id)
                    if result is not None:
                        extracted_count += 1
                        print(f"  -> Extracted successfully. Found {len(result.orders)} orders, {len(result.inquiries)} inquiries.")
                    else:
                        print(f"  -> Extracted successfully but no new entities or unchanged.")
            except Exception as e:
                print(f"  -> Extraction failed: {e}")
                
        session.commit()
        print(f"\nDone! Extracted {extracted_count} episodes.")

if __name__ == "__main__":
    main()

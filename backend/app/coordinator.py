import logging
import os
from sqlalchemy.engine import Engine

from app.database.connection import session_scope
from app.ingestion.service import IngestionService
from app.relevance.service import RelevanceService
from app.extraction.service import ExtractionService
from app.extraction.provider import GeminiProvider

logger = logging.getLogger(__name__)

class ImportCoordinator:
    """
    Coordinates the full pipeline: Ingestion -> Relevance -> Extraction.
    Ensures that each stage is isolated and failures in later stages
    do not roll back successful earlier stages.
    """

    def __init__(self, engine: Engine, extraction_provider=None):
        self.engine = engine
        self.extraction_provider = extraction_provider

    def process_import(self, business_id: int, file_bytes: bytes, import_name: str):
        # 1. Ingestion
        ingestion_service = IngestionService(self.engine)
        batch_result = ingestion_service.import_package(
            business_id=business_id,
            file_bytes=file_bytes,
            import_name=import_name,
        )

        if not batch_result.is_successful or batch_result.import_batch_id is None:
            return batch_result

        # 2. Relevance Assessment
        try:
            relevance_service = RelevanceService(self.engine)
            relevance_service.assess_messages_for_import(
                import_batch_id=batch_result.import_batch_id,
                business_id=business_id,
            )
        except Exception as exc:
            logger.warning(
                "Relevance assessment failed for import_batch_id=%d: %s",
                batch_result.import_batch_id,
                exc,
                exc_info=True,
            )
            batch_result.warnings.append(
                f"Relevance assessment could not be completed: {exc}"
            )
            # If relevance fails, we cannot extract anything new from this batch
            return batch_result

        try:
            from dotenv import load_dotenv
            load_dotenv()
            provider = self.extraction_provider or GeminiProvider(api_key=os.environ.get("GOOGLE_API_KEY", ""))
            extraction_service = ExtractionService(provider)
            with session_scope() as session:
                extracted_count = extraction_service.extract_messages_for_import(
                    session=session,
                    import_batch_id=batch_result.import_batch_id,
                    business_id=business_id,
                )
                session.commit()
                logger.info("Extracted entities from %d episodes for batch %d", extracted_count, batch_result.import_batch_id)
        except Exception as exc:
            logger.warning(
                "Extraction failed for import_batch_id=%d: %s",
                batch_result.import_batch_id,
                exc,
                exc_info=True,
            )
            batch_result.warnings.append(
                f"Extraction could not be completed: {exc}"
            )

        return batch_result

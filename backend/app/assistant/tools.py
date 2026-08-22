import json
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from app.analytics.service import AnalyticsService
from app.database.connection import session_scope
from app.database.models import ExtractionEvidence, Order
from sqlalchemy import select


def _get_business_id(config: RunnableConfig) -> int:
    business_id = config.get("configurable", {}).get("business_id")
    if not business_id:
        raise ValueError("business_id is missing from the execution context.")
    return business_id


@tool
def get_order_metrics(config: RunnableConfig) -> dict:
    """Retrieve aggregate order metrics and recent orders."""
    business_id = _get_business_id(config)
    with session_scope() as session:
        metrics = AnalyticsService.get_order_metrics(session, business_id)
        return json.loads(metrics.model_dump_json())


@tool
def get_product_metrics(config: RunnableConfig) -> dict:
    """Retrieve aggregate product metrics and top products."""
    business_id = _get_business_id(config)
    with session_scope() as session:
        metrics = AnalyticsService.get_product_metrics(session, business_id)
        return json.loads(metrics.model_dump_json())


@tool
def get_inquiry_metrics(config: RunnableConfig) -> dict:
    """Retrieve aggregate inquiry metrics and recent inquiries."""
    business_id = _get_business_id(config)
    with session_scope() as session:
        metrics = AnalyticsService.get_inquiry_metrics(session, business_id)
        return json.loads(metrics.model_dump_json())


@tool
def get_customer_metrics(config: RunnableConfig) -> dict:
    """Retrieve aggregate customer metrics including repeat customers."""
    business_id = _get_business_id(config)
    with session_scope() as session:
        metrics = AnalyticsService.get_customer_metrics(session, business_id)
        return json.loads(metrics.model_dump_json())


@tool
def get_feedback_metrics(config: RunnableConfig) -> dict:
    """Retrieve aggregate feedback metrics and sentiment counts."""
    business_id = _get_business_id(config)
    with session_scope() as session:
        metrics = AnalyticsService.get_feedback_metrics(session, business_id)
        return json.loads(metrics.model_dump_json())


@tool
def get_business_analytics_report(config: RunnableConfig) -> dict:
    """Retrieve a comprehensive analytics report across all domains."""
    business_id = _get_business_id(config)
    with session_scope() as session:
        metrics = AnalyticsService.get_business_analytics_report(session, business_id)
        return json.loads(metrics.model_dump_json())


@tool
def get_order_evidence(order_id: int, config: RunnableConfig) -> str:
    """Retrieve extracted evidence text for a specific order by its ID to explain why it was created."""
    business_id = _get_business_id(config)
    with session_scope() as session:
        query = select(ExtractionEvidence.evidence_text).join(
            Order, Order.id == ExtractionEvidence.order_id
        ).where(
            Order.id == order_id,
            Order.business_id == business_id
        )
        results = session.execute(query).scalars().all()
        if not results:
            return "Evidence is unavailable for that order."
        return "\n".join(results)

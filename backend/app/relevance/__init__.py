"""Business Relevance Detection package.

Provides message-level relevance assessment and extraction eligibility
boundary for imported WhatsApp conversations.

Exported surface:
    - :class:`RelevanceService`    – main assessment and eligibility service
    - :class:`AssessmentResult`    – value object returned by assess_message
    - :data:`RELEVANCE_STATES`     – tuple of canonical state strings
"""

from app.relevance.service import AssessmentResult, RelevanceService
from app.database.models import RELEVANCE_STATES

__all__ = [
    "RelevanceService",
    "AssessmentResult",
    "RELEVANCE_STATES",
]

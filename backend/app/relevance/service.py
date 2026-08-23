"""Business relevance assessment service.

Responsibilities
----------------
- Assess individual imported WhatsApp messages for business relevance
  using a rule-based classifier that can be replaced without changing
  the data contract (Task 2.9).
- Persist relevance assessments *separately* from raw message records
  (Tasks 3.6, 3.7).
- Provide an extraction eligibility boundary (Tasks 4.1–4.9).
- Support incremental reassessment with assessment history (Tasks 5.1–5.8).
- Handle failures without corrupting raw messages (Tasks 8.1–8.5).

Non-responsibilities
--------------------
- Creating business entities (orders, customers, products, etc.).
- Performing analytics, sentiment analysis, or RAG.
- Generating embeddings or using a vector database.
- Calling the WhatsApp API.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import session_scope
from app.database.models import (
    Business,
    Conversation,
    Message,
    RelevanceAssessment,
    RelevanceAssessmentHistory,
    RELEVANCE_STATES,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ASSESSMENT_METHOD = "rule-based"
ASSESSMENT_VERSION = "v1"

# Keywords that strongly indicate a business-relevant message (case-insensitive).
# This rule-based classifier is the default implementation and is fully
# replaceable without touching the persistence or eligibility contracts (Task 2.9).
_BUSINESS_KEYWORDS: frozenset[str] = frozenset(
    [
        # Order / booking signals
        "order", "orders", "ordering", "ordered",
        "book", "booking", "booked",
        "reserve", "reservation",
        "cancel", "cancellation", "cancelled",
        "confirm", "confirmation", "confirmed",
        # Product / pricing signals
        "price", "pricing", "cost", "charge", "quote", "quotation",
        "how much", "total", "amount", "payment", "pay",
        "cake", "cupcake", "pastry", "bread", "bun", "cookie",
        "dessert", "sweet", "bakery",
        # Availability / delivery
        "available", "availability", "stock",
        "deliver", "delivery", "pickup", "pick up", "collect",
        "ready", "when will", "by when",
        # Customer service
        "complaint", "issue", "problem", "broken", "damaged",
        "refund", "exchange", "return",
        "feedback", "review", "rating",
        "appointment", "schedule",
        # Transaction / inquiry
        "inquiry", "enquiry", "question",
        "size", "flavour", "flavor", "kg", "gram", "dozen",
    ]
)

# Phrases that are strong indicators of a purely personal message.
_PERSONAL_PHRASES: frozenset[str] = frozenset(
    [
        "how are you", "how r u", "good morning", "good night",
        "good evening", "happy birthday", "congratulations",
        "haha", "lol", "lmao", "😂", "❤️",
        "see you", "take care", "love you", "miss you",
        "party", "family",
    ]
)

# Threshold for classifying as needs_review when signals are mixed/absent.
# A message with no keyword match and no strong personal signal falls here.
_UNCERTAINTY_THRESHOLD = 0


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass
class AssessmentResult:
    """Result of a single message relevance assessment.

    This value object decouples the service output from the persistence
    model so that callers can inspect results before they are committed.
    """

    message_id: int
    business_id: int
    conversation_id: int
    relevance_state: str  # one of RELEVANCE_STATES
    rationale: str
    assessment_method: str = ASSESSMENT_METHOD
    assessment_version: str = ASSESSMENT_VERSION
    assessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    context_message_ids: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.relevance_state not in RELEVANCE_STATES:
            raise ValueError(
                f"Invalid relevance_state '{self.relevance_state}'. "
                f"Must be one of {RELEVANCE_STATES}."
            )


# ---------------------------------------------------------------------------
# Classifier (replaceable, Task 2.9)
# ---------------------------------------------------------------------------


def _classify_message(
    content: str,
    context_messages: list[str],
) -> tuple[str, str]:
    """Classify *content* using a simple keyword-based rule set.

    Parameters
    ----------
    content:
        The text content of the message being assessed.
    context_messages:
        Text content of neighbouring messages from the same conversation
        that may disambiguate the target message (Task 2.6, 2.7).

    Returns
    -------
    (relevance_state, rationale)
        Both are human-readable strings; relevance_state is one of
        RELEVANCE_STATES.

    Notes
    -----
    The assessment applies to the *target* message even when context is
    used to resolve ambiguity (Task 2.7).  The context is only consulted
    to help interpret the target message; the result is still stored
    against the target message alone.
    """
    content_lower = content.lower()

    # Count business keyword hits in the target message.
    business_hits = [kw for kw in _BUSINESS_KEYWORDS if kw in content_lower]

    # Check for personal phrase signals.
    personal_hits = [ph for ph in _PERSONAL_PHRASES if ph in content_lower]

    if business_hits:
        rationale = (
            f"Message contains business-relevant signals: "
            f"{', '.join(sorted(business_hits)[:5])}."
        )
        return "relevant", rationale

    if personal_hits and not business_hits:
        rationale = (
            f"Message contains personal/social signals and no business keywords: "
            f"{', '.join(sorted(personal_hits)[:5])}."
        )
        return "not_relevant", rationale

    # No clear signal in target message — consult context (Task 2.6).
    if context_messages:
        context_text = " ".join(context_messages).lower()
        context_hits = [kw for kw in _BUSINESS_KEYWORDS if kw in context_text]
        if context_hits:
            rationale = (
                "Message content alone is ambiguous; surrounding conversation "
                "context contains business signals. Classified as needs_review "
                "pending human confirmation."
            )
            return "needs_review", rationale

    # No signals detected at all.
    rationale = (
        "Message contains no detectable business or personal signals. "
        "Marked as needs_review pending human confirmation."
    )
    return "needs_review", rationale


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------


def _save_history_snapshot(
    session: Session,
    existing: RelevanceAssessment,
) -> None:
    """Copy *existing* assessment fields into the history table before update."""
    snapshot = RelevanceAssessmentHistory(
        relevance_assessment_id=existing.id,
        message_id=existing.message_id,
        business_id=existing.business_id,
        relevance_state=existing.relevance_state,
        assessed_at=existing.assessed_at,
        assessment_method=existing.assessment_method,
        assessment_version=existing.assessment_version,
        rationale=existing.rationale,
        context_message_ids_json=existing.context_message_ids_json,
        version_number=existing.assessment_version_number,
    )
    session.add(snapshot)


def _serialize_ids(ids: list[int]) -> str | None:
    if not ids:
        return None
    return json.dumps(ids)


# ---------------------------------------------------------------------------
# RelevanceService
# ---------------------------------------------------------------------------


class RelevanceService:
    """Message-level relevance assessment and extraction eligibility service.

    Separates raw WhatsApp evidence (Message) from derived relevance
    decisions (RelevanceAssessment).  The classification mechanism
    (rule-based by default) is internal and replaceable without changing
    the public contract.

    Parameters
    ----------
    engine:
        SQLAlchemy engine to use.  If *None*, the application default
        engine is used via :func:`app.database.connection.session_scope`.
    """

    def __init__(self, engine=None) -> None:
        self._engine = engine

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assess_message(
        self,
        message_id: int,
        business_id: int,
        *,
        context_message_ids: Optional[list[int]] = None,
    ) -> AssessmentResult:
        """Assess a single message for business relevance.

        The raw Message record is never modified (Tasks 3.6, 8.1).

        Parameters
        ----------
        message_id:
            Primary key of the :class:`~app.database.models.Message` to assess.
        business_id:
            Primary key of the owning :class:`~app.database.models.Business`.
            Enforces business-level data isolation (Task 3.8).
        context_message_ids:
            Optional list of additional Message IDs from the same conversation
            to use as contextual evidence (Tasks 2.6, 3.5).

        Returns
        -------
        AssessmentResult
            The assessment result.  Persisted to the database.

        Raises
        ------
        ValueError
            If the message does not exist or does not belong to *business_id*.
        RuntimeError
            On unexpected database errors.
        """
        context_message_ids = context_message_ids or []

        with session_scope(bind=self._engine) as session:
            result = self._assess_in_session(
                session, message_id, business_id, context_message_ids
            )
        return result

    def assess_messages_for_import(
        self,
        import_batch_id: int,
        business_id: int,
    ) -> list[AssessmentResult]:
        """Assess all messages from an import batch.

        Called after ingestion completes (Task 6.1, 6.2).  Failures for
        individual messages are logged and skipped so that partial success
        is possible without corrupting already-processed messages (Task 8.5).

        Parameters
        ----------
        import_batch_id:
            The ImportBatch to process.
        business_id:
            Owner business — used for isolation checks.

        Returns
        -------
        List of :class:`AssessmentResult` for successfully assessed messages.
        """
        results: list[AssessmentResult] = []

        with session_scope(bind=self._engine) as session:
            messages = session.execute(
                select(Message).where(
                    Message.import_batch_id == import_batch_id,
                    Message.conversation_id.in_(
                        select(Conversation.id).where(
                            Conversation.business_id == business_id
                        )
                    ),
                )
            ).scalars().all()

            for message in messages:
                try:
                    result = self._assess_in_session(
                        session, message.id, business_id, []
                    )
                    results.append(result)
                except Exception as exc:
                    logger.warning(
                        "Relevance assessment failed for message_id=%d: %s",
                        message.id,
                        exc,
                        exc_info=True,
                    )
                    # On failure, create a 'pending' placeholder so the
                    # message is still identifiable for retry (Task 8.2).
                    self._ensure_pending_assessment(session, message, business_id)

        return results

    def get_extraction_eligible_messages(
        self,
        business_id: int,
        conversation_id: Optional[int] = None,
    ) -> list[Message]:
        """Return messages eligible for downstream business extraction.

        Only messages whose current relevance state is ``relevant`` are
        returned (Tasks 4.1–4.3, 4.7).  Messages in any other state
        (``pending``, ``not_relevant``, ``needs_review``) are excluded
        (Tasks 4.4–4.6).

        The query is scoped to *business_id* to enforce business-level
        data isolation (Task 4.7).

        Parameters
        ----------
        business_id:
            Scope results to this business.
        conversation_id:
            Optional filter to restrict to a single conversation.

        Returns
        -------
        List of :class:`~app.database.models.Message` objects.
        """
        with session_scope(bind=self._engine) as session:
            query = (
                select(Message)
                .join(
                    RelevanceAssessment,
                    (RelevanceAssessment.message_id == Message.id)
                    & (RelevanceAssessment.business_id == business_id)
                    & (RelevanceAssessment.is_current == True)  # noqa: E712
                    & (RelevanceAssessment.relevance_state == "relevant"),
                )
                .join(
                    Conversation,
                    Conversation.id == Message.conversation_id,
                )
                .where(Conversation.business_id == business_id)
            )
            if conversation_id is not None:
                query = query.where(Message.conversation_id == conversation_id)

            return list(session.execute(query).scalars().all())

    def is_extraction_eligible(
        self,
        message_id: int,
        business_id: int,
    ) -> bool:
        """Check whether a single message is extraction-eligible (Task 4.1).

        Returns ``True`` only if the current relevance state is ``relevant``.
        """
        with session_scope(bind=self._engine) as session:
            assessment = session.execute(
                select(RelevanceAssessment).where(
                    RelevanceAssessment.message_id == message_id,
                    RelevanceAssessment.business_id == business_id,
                    RelevanceAssessment.is_current == True,  # noqa: E712
                )
            ).scalar_one_or_none()

            if assessment is None:
                return False
            return assessment.relevance_state == "relevant"

    def get_pending_messages(
        self,
        business_id: int,
        conversation_id: Optional[int] = None,
    ) -> list[Message]:
        """Return messages with a ``pending`` relevance assessment.

        Useful for scheduling or retrying assessments (Tasks 5.1, 8.4).
        """
        with session_scope(bind=self._engine) as session:
            query = (
                select(Message)
                .join(
                    RelevanceAssessment,
                    (RelevanceAssessment.message_id == Message.id)
                    & (RelevanceAssessment.business_id == business_id)
                    & (RelevanceAssessment.is_current == True)  # noqa: E712
                    & (RelevanceAssessment.relevance_state == "pending"),
                )
            )
            if conversation_id is not None:
                query = query.where(Message.conversation_id == conversation_id)
            return list(session.execute(query).scalars().all())

    def get_needs_review_messages(
        self,
        business_id: int,
        conversation_id: Optional[int] = None,
    ) -> list[Message]:
        """Return messages needing human review (Tasks 8.2, 2.4).

        These messages are *not* extraction-eligible by default (Task 4.6).
        """
        with session_scope(bind=self._engine) as session:
            query = (
                select(Message)
                .join(
                    RelevanceAssessment,
                    (RelevanceAssessment.message_id == Message.id)
                    & (RelevanceAssessment.business_id == business_id)
                    & (RelevanceAssessment.is_current == True)  # noqa: E712
                    & (RelevanceAssessment.relevance_state == "needs_review"),
                )
            )
            if conversation_id is not None:
                query = query.where(Message.conversation_id == conversation_id)
            return list(session.execute(query).scalars().all())

    def reassess_conversation(
        self,
        conversation_id: int,
        business_id: int,
    ) -> list[AssessmentResult]:
        """Reassess all messages in a conversation.

        Intended for use after new messages are imported into an existing
        conversation (Tasks 5.2, 5.3, 6.3).  Raw message records are
        never modified (Task 5.4).

        The previous assessment is snapshotted to history before being
        updated (Tasks 5.5, 5.6).

        Returns the list of updated :class:`AssessmentResult` objects.
        """
        results: list[AssessmentResult] = []

        with session_scope(bind=self._engine) as session:
            messages = session.execute(
                select(Message).where(
                    Message.conversation_id == conversation_id,
                    Conversation.business_id == business_id,
                ).join(Conversation)
            ).scalars().all()

            # Gather all message contents for context.
            context_map: dict[int, str] = {
                m.id: (m.content or "") for m in messages
            }

            for message in messages:
                ctx_ids = [mid for mid in context_map if mid != message.id]
                try:
                    result = self._assess_in_session(
                        session, message.id, business_id, ctx_ids
                    )
                    results.append(result)
                except Exception as exc:
                    logger.warning(
                        "Reassessment failed for message_id=%d: %s",
                        message.id,
                        exc,
                        exc_info=True,
                    )

        return results

    def retry_failed_assessments(
        self,
        business_id: int,
        conversation_id: Optional[int] = None,
    ) -> list[AssessmentResult]:
        """Retry relevance assessment for all ``pending`` messages (Task 8.4).

        Messages that failed previously will have remained in ``pending``
        state.  This method finds them and retries assessment.
        """
        pending = self.get_pending_messages(business_id, conversation_id)
        results: list[AssessmentResult] = []

        with session_scope(bind=self._engine) as session:
            for message in pending:
                try:
                    result = self._assess_in_session(
                        session, message.id, business_id, []
                    )
                    results.append(result)
                except Exception as exc:
                    logger.warning(
                        "Retry failed for message_id=%d: %s",
                        message.id,
                        exc,
                        exc_info=True,
                    )

        return results

    def initialize_pending_for_business(
        self,
        business_id: int,
    ) -> int:
        """Create ``pending`` assessments for messages that have none yet.

        Used for migration: existing messages imported before this capability
        was introduced are initialized as ``pending`` so they are never
        silently treated as extraction-eligible (Tasks 7.2, 7.3).

        Returns the number of assessments created.
        """
        created = 0

        with session_scope(bind=self._engine) as session:
            # Find messages in this business that have no assessment yet.
            assessed_ids = select(RelevanceAssessment.message_id).where(
                RelevanceAssessment.business_id == business_id
            )
            unassessed_messages = session.execute(
                select(Message)
                .join(Conversation, Conversation.id == Message.conversation_id)
                .where(
                    Conversation.business_id == business_id,
                    Message.id.not_in(assessed_ids),
                )
            ).scalars().all()

            for message in unassessed_messages:
                self._ensure_pending_assessment(session, message, business_id)
                created += 1

        return created

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _assess_in_session(
        self,
        session: Session,
        message_id: int,
        business_id: int,
        context_message_ids: list[int],
    ) -> AssessmentResult:
        """Core assessment logic executed within an existing session."""
        # Verify the message exists and belongs to the correct business (Task 3.8).
        message = session.get(Message, message_id)
        if message is None:
            raise ValueError(f"Message {message_id} not found.")

        conversation = session.get(Conversation, message.conversation_id)
        if conversation is None or conversation.business_id != business_id:
            raise ValueError(
                f"Message {message_id} does not belong to business {business_id}."
            )

        # Fetch context message content (Task 2.6).
        context_texts: list[str] = []
        if context_message_ids:
            ctx_messages = session.execute(
                select(Message).where(
                    Message.id.in_(context_message_ids),
                    Message.conversation_id == message.conversation_id,
                )
            ).scalars().all()
            context_texts = [m.content or "" for m in ctx_messages]

        # Classify (replaceable — Task 2.9).
        relevance_state, rationale = _classify_message(
            message.content or "", context_texts
        )

        now = datetime.now(timezone.utc)

        # Find any existing current assessment for this message+business.
        existing = session.execute(
            select(RelevanceAssessment).where(
                RelevanceAssessment.message_id == message_id,
                RelevanceAssessment.business_id == business_id,
                RelevanceAssessment.is_current == True,  # noqa: E712
            )
        ).scalar_one_or_none()

        if existing is not None:
            # Archive previous version before updating (Tasks 5.5, 5.6, 1.6).
            _save_history_snapshot(session, existing)

            existing.relevance_state = relevance_state
            existing.assessed_at = now
            existing.assessment_method = ASSESSMENT_METHOD
            existing.assessment_version = ASSESSMENT_VERSION
            existing.rationale = rationale
            existing.context_message_ids_json = _serialize_ids(context_message_ids)
            existing.assessment_version_number += 1
            session.flush()
        else:
            # Create a new assessment row.
            assessment = RelevanceAssessment(
                message_id=message_id,
                conversation_id=message.conversation_id,
                business_id=business_id,
                relevance_state=relevance_state,
                assessed_at=now,
                assessment_method=ASSESSMENT_METHOD,
                assessment_version=ASSESSMENT_VERSION,
                rationale=rationale,
                context_message_ids_json=_serialize_ids(context_message_ids),
                assessment_version_number=1,
                is_current=True,
            )
            session.add(assessment)
            session.flush()

        return AssessmentResult(
            message_id=message_id,
            business_id=business_id,
            conversation_id=message.conversation_id,
            relevance_state=relevance_state,
            rationale=rationale,
            assessment_method=ASSESSMENT_METHOD,
            assessment_version=ASSESSMENT_VERSION,
            assessed_at=now,
            context_message_ids=context_message_ids,
        )

    def _ensure_pending_assessment(
        self,
        session: Session,
        message: Message,
        business_id: int,
    ) -> RelevanceAssessment:
        """Get-or-create a ``pending`` assessment row for *message*.

        Used during failure handling and migration (Tasks 7.2, 8.2).
        Does not overwrite an existing non-pending assessment.
        """
        existing = session.execute(
            select(RelevanceAssessment).where(
                RelevanceAssessment.message_id == message.id,
                RelevanceAssessment.business_id == business_id,
                RelevanceAssessment.is_current == True,  # noqa: E712
            )
        ).scalar_one_or_none()

        if existing is not None:
            return existing

        conversation = session.get(Conversation, message.conversation_id)
        assessment = RelevanceAssessment(
            message_id=message.id,
            conversation_id=message.conversation_id,
            business_id=business_id,
            relevance_state="pending",
            assessed_at=None,
            assessment_method=None,
            assessment_version=None,
            rationale="Assessment pending.",
            context_message_ids_json=None,
            assessment_version_number=1,
            is_current=True,
        )
        session.add(assessment)
        session.flush()
        return assessment

"""Repository boundary plus in-memory and SQLAlchemy implementations."""

from copy import deepcopy
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from threading import RLock
from typing import Protocol, cast

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.conversation.domain import (
    ChatMessage,
    ConversationContext,
    ConversationState,
    MessageSender,
    QuickReply,
)
from app.modules.conversation.models import (
    ConversationMessageRecord,
    ConversationRecord,
    ReservationDraftRecord,
)
from app.modules.nlp.taxonomy import Intent


class ConversationRepository(Protocol):
    """Storage operations needed by the conversation service."""

    def create(self, context: ConversationContext) -> None:
        """Store a new conversation."""

    def get(self, conversation_id: str) -> ConversationContext | None:
        """Return a detached snapshot when the conversation exists."""

    def save(self, context: ConversationContext) -> None:
        """Replace an existing conversation snapshot."""


class InMemoryConversationRepository:
    """Thread-safe test double for isolated service and API tests."""

    def __init__(self) -> None:
        self._contexts: dict[str, ConversationContext] = {}
        self._lock = RLock()

    def create(self, context: ConversationContext) -> None:
        with self._lock:
            if context.conversation_id in self._contexts:
                raise ValueError("Conversation ID already exists.")
            self._contexts[context.conversation_id] = deepcopy(context)

    def get(self, conversation_id: str) -> ConversationContext | None:
        with self._lock:
            context = self._contexts.get(conversation_id)
            return deepcopy(context) if context is not None else None

    def save(self, context: ConversationContext) -> None:
        with self._lock:
            if context.conversation_id not in self._contexts:
                raise KeyError(context.conversation_id)
            self._contexts[context.conversation_id] = deepcopy(context)


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _aware_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _json_safe(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    raise TypeError(f"Unsupported JSON value: {type(value).__name__}")


def _context_payload(context: ConversationContext) -> dict[str, object]:
    return {
        "quick_replies": [
            {"label": reply.label, "value": reply.value} for reply in context.quick_replies
        ],
        "reservation_summary": _json_safe(context.reservation_summary),
        "price_breakdown": _json_safe(context.price_breakdown),
        "ticket": _json_safe(context.ticket),
        "reservation_confirmed": context.reservation_confirmed,
        "last_intent": context.last_intent.value if context.last_intent is not None else None,
        "last_confidence": context.last_confidence,
    }


def _draft_status(state: ConversationState) -> str:
    if state is ConversationState.CANCELLED or state is ConversationState.WELCOME:
        return "CANCELLED"
    if state is ConversationState.TICKET_CREATED:
        return "CONFIRMED"
    return "ACTIVE"


class SqlAlchemyConversationRepository:
    """MySQL-compatible repository using one SQLAlchemy session per request."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, context: ConversationContext) -> None:
        try:
            conversation = ConversationRecord(
                id=context.conversation_id,
                locale=context.locale,
                state=context.state.value,
                context=_context_payload(context),
                created_at=_naive_utc(context.created_at),
                updated_at=_naive_utc(context.updated_at),
            )
            self._session.add(conversation)
            self._session.flush((conversation,))
            self._append_messages(context, start_index=0)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

    def get(self, conversation_id: str) -> ConversationContext | None:
        row = self._session.get(ConversationRecord, conversation_id)
        if row is None:
            return None

        message_rows = self._session.scalars(
            select(ConversationMessageRecord)
            .where(ConversationMessageRecord.conversation_id == conversation_id)
            .order_by(ConversationMessageRecord.turn_index)
        ).all()
        draft = self._session.scalar(
            select(ReservationDraftRecord).where(
                ReservationDraftRecord.conversation_id == conversation_id
            )
        )
        payload = row.context
        quick_replies_value = payload.get("quick_replies", [])
        quick_replies = tuple(
            QuickReply(label=str(item["label"]), value=str(item["value"]))
            for item in quick_replies_value
            if isinstance(item, dict) and "label" in item and "value" in item
        )
        last_intent_value = payload.get("last_intent")
        last_confidence_value = payload.get("last_confidence")
        return ConversationContext(
            conversation_id=row.id,
            locale=row.locale,
            state=ConversationState(row.state),
            messages=tuple(
                ChatMessage(
                    id=message.id,
                    sender=MessageSender(message.sender),
                    text=message.content,
                    created_at=_aware_utc(message.created_at),
                    client_message_id=message.client_message_id,
                )
                for message in message_rows
            ),
            quick_replies=quick_replies,
            created_at=_aware_utc(row.created_at),
            updated_at=_aware_utc(row.updated_at),
            collected_slots=dict(draft.slots) if draft is not None else {},
            reservation_summary=cast(
                dict[str, object] | None,
                payload.get("reservation_summary"),
            ),
            price_breakdown=cast(
                dict[str, object] | None,
                payload.get("price_breakdown"),
            ),
            ticket=cast(dict[str, object] | None, payload.get("ticket")),
            reservation_confirmed=bool(payload.get("reservation_confirmed", False)),
            last_intent=Intent(str(last_intent_value)) if last_intent_value is not None else None,
            last_confidence=(
                float(last_confidence_value) if last_confidence_value is not None else None
            ),
        )

    def save(self, context: ConversationContext) -> None:
        try:
            row = self._session.scalar(
                select(ConversationRecord)
                .where(ConversationRecord.id == context.conversation_id)
                .with_for_update()
            )
            if row is None:
                raise KeyError(context.conversation_id)

            existing_message_count = self._session.scalar(
                select(func.count())
                .select_from(ConversationMessageRecord)
                .where(ConversationMessageRecord.conversation_id == context.conversation_id)
            )
            message_count = int(existing_message_count or 0)
            if message_count > len(context.messages):
                raise ValueError("Persisted history is longer than the supplied context.")

            row.locale = context.locale
            row.state = context.state.value
            row.context = _context_payload(context)
            row.updated_at = _naive_utc(context.updated_at)
            self._append_messages(context, start_index=message_count)
            self._upsert_draft(context)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

    def _append_messages(self, context: ConversationContext, *, start_index: int) -> None:
        for turn_index, message in enumerate(
            context.messages[start_index:],
            start=start_index,
        ):
            self._session.add(
                ConversationMessageRecord(
                    id=message.id,
                    conversation_id=context.conversation_id,
                    turn_index=turn_index,
                    client_message_id=message.client_message_id,
                    sender=message.sender.value,
                    content=message.text,
                    created_at=_naive_utc(message.created_at),
                )
            )

    def _upsert_draft(self, context: ConversationContext) -> None:
        draft = self._session.scalar(
            select(ReservationDraftRecord).where(
                ReservationDraftRecord.conversation_id == context.conversation_id
            )
        )
        service_type_value = context.collected_slots.get("service_type")
        if draft is None and service_type_value is None:
            return

        slots = cast(dict[str, object], _json_safe(context.collected_slots))
        price_snapshot = cast(
            dict[str, object] | None,
            _json_safe(context.price_breakdown),
        )
        if draft is None:
            self._session.add(
                ReservationDraftRecord(
                    id=context.conversation_id,
                    conversation_id=context.conversation_id,
                    service_type=str(service_type_value),
                    status=_draft_status(context.state),
                    slots=slots,
                    price_snapshot=price_snapshot,
                    created_at=_naive_utc(context.created_at),
                    updated_at=_naive_utc(context.updated_at),
                )
            )
            return

        if service_type_value is not None:
            draft.service_type = str(service_type_value)
        draft.status = _draft_status(context.state)
        draft.slots = slots
        draft.price_snapshot = price_snapshot
        draft.updated_at = _naive_utc(context.updated_at)

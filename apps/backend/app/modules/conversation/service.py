"""Application service for session lifecycle and FAQ turns."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Protocol

from fastapi import status

from app.modules.conversation.domain import (
    ChatMessage,
    ConversationContext,
    ConversationState,
    MessageSender,
    QuickReply,
)
from app.modules.conversation.faq import (
    DIRECT_INTENTS,
    FALLBACK_REPLIES,
    FALLBACK_TEXT,
    FAQ_ANSWERS,
    INFO_MENU_REPLIES,
    INFO_MENU_TEXT,
    SELECT_SERVICE_REPLIES,
    SELECT_SERVICE_TEXT,
    TICKET_LOOKUP_TEXT,
    WELCOME_REPLIES,
    WELCOME_TEXT,
)
from app.modules.conversation.ids import generate_ulid
from app.modules.conversation.repository import ConversationRepository
from app.modules.nlp.model import IntentPrediction
from app.modules.nlp.taxonomy import Intent
from app.shared.errors import ApplicationError

Clock = Callable[[], datetime]
IdFactory = Callable[[datetime], str]


class IntentPredictor(Protocol):
    """Minimal NLP interface required by conversation routing."""

    def predict(self, text: str, *, threshold: float | None = None) -> IntentPrediction:
        """Return the top intent and runtime fallback decision."""


@dataclass(frozen=True, slots=True)
class ConversationResult:
    """Updated context and messages created by the current operation."""

    context: ConversationContext
    new_messages: tuple[ChatMessage, ...]


def utc_now() -> datetime:
    """Return a timezone-aware clock value."""

    return datetime.now(UTC)


class ConversationService:
    """Coordinate state transitions without owning persistence infrastructure."""

    def __init__(
        self,
        repository: ConversationRepository,
        *,
        predictor: IntentPredictor | None = None,
        clock: Clock = utc_now,
        id_factory: IdFactory = generate_ulid,
    ) -> None:
        self._repository = repository
        self._predictor = predictor
        self._clock = clock
        self._id_factory = id_factory

    def _message(self, sender: MessageSender, text: str, now: datetime) -> ChatMessage:
        return ChatMessage(
            id=self._id_factory(now),
            sender=sender,
            text=text,
            created_at=now,
        )

    def create_conversation(self, *, locale: str = "id-ID") -> ConversationResult:
        now = self._clock()
        welcome = self._message(MessageSender.BOT, WELCOME_TEXT, now)
        context = ConversationContext(
            conversation_id=self._id_factory(now),
            locale=locale,
            state=ConversationState.WELCOME,
            messages=(welcome,),
            quick_replies=WELCOME_REPLIES,
            created_at=now,
            updated_at=now,
        )
        self._repository.create(context)
        return ConversationResult(context=context, new_messages=(welcome,))

    def get_conversation(self, conversation_id: str) -> ConversationContext:
        context = self._repository.get(conversation_id)
        if context is None:
            raise ApplicationError(
                code="CONVERSATION_NOT_FOUND",
                message="Maaf, sesi percakapan tersebut belum ditemukan.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return context

    def process_message(self, conversation_id: str, text: str) -> ConversationResult:
        context = self.get_conversation(conversation_id)
        now = self._clock()
        user_message = self._message(MessageSender.USER, text, now)
        normalized = text.casefold().strip()
        state: ConversationState
        response_text: str
        quick_replies: tuple[QuickReply, ...]
        intent: Intent | None
        confidence: float | None

        if normalized == "info":
            state = ConversationState.INFO_MODE
            response_text = INFO_MENU_TEXT
            quick_replies = INFO_MENU_REPLIES
            intent = None
            confidence = None
        elif normalized in {"reservation", "reservasi"}:
            state = ConversationState.SELECT_SERVICE
            response_text = SELECT_SERVICE_TEXT
            quick_replies = SELECT_SERVICE_REPLIES
            intent = Intent.START_RESERVATION
            confidence = 1.0
        elif context.state is ConversationState.SELECT_SERVICE:
            state = ConversationState.SELECT_SERVICE
            response_text = SELECT_SERVICE_TEXT
            quick_replies = SELECT_SERVICE_REPLIES
            intent = None
            confidence = None
        elif context.state is ConversationState.TICKET_LOOKUP:
            state = ConversationState.TICKET_LOOKUP
            response_text = TICKET_LOOKUP_TEXT
            quick_replies = ()
            intent = None
            confidence = None
        else:
            state, response_text, quick_replies, intent, confidence = self._route_faq(
                text,
                normalized,
            )

        bot_message = self._message(MessageSender.BOT, response_text, now)
        new_messages = (user_message, bot_message)
        updated = replace(
            context,
            state=state,
            messages=(*context.messages, *new_messages),
            quick_replies=quick_replies,
            updated_at=now,
            last_intent=intent,
            last_confidence=confidence,
        )
        self._repository.save(updated)
        return ConversationResult(context=updated, new_messages=new_messages)

    def _route_faq(
        self,
        text: str,
        normalized: str,
    ) -> tuple[ConversationState, str, tuple[QuickReply, ...], Intent | None, float | None]:
        direct_intent = DIRECT_INTENTS.get(normalized)
        if direct_intent is not None:
            answer = FAQ_ANSWERS[direct_intent]
            return answer.state, answer.text, answer.quick_replies, direct_intent, 1.0

        if self._predictor is None:
            raise ApplicationError(
                code="NLP_MODEL_UNAVAILABLE",
                message=(
                    "Maaf, layanan pemahaman pertanyaan sedang belum tersedia. Silakan coba lagi."
                ),
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                retryable=True,
            )
        prediction = self._predictor.predict(text)
        if prediction.is_fallback or prediction.intent is None:
            return (
                ConversationState.FALLBACK,
                FALLBACK_TEXT,
                FALLBACK_REPLIES,
                None,
                prediction.confidence,
            )

        answer = FAQ_ANSWERS[prediction.intent]
        return (
            answer.state,
            answer.text,
            answer.quick_replies,
            prediction.intent,
            prediction.confidence,
        )

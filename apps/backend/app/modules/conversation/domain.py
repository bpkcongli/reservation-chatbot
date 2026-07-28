"""Conversation state and context owned by the conversation module."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from app.modules.nlp.taxonomy import Intent


class ConversationState(StrEnum):
    """All states declared by the normative API contract."""

    WELCOME = "WELCOME"
    INFO_MODE = "INFO_MODE"
    FALLBACK = "FALLBACK"
    SELECT_SERVICE = "SELECT_SERVICE"
    BORONGAN_ASK_CUSTOMER_ID = "BORONGAN_ASK_CUSTOMER_ID"
    BORONGAN_ASK_PHONE = "BORONGAN_ASK_PHONE"
    BORONGAN_ASK_BUILDING = "BORONGAN_ASK_BUILDING"
    BORONGAN_ASK_ADDRESS = "BORONGAN_ASK_ADDRESS"
    BORONGAN_ASK_SURVEY_DATE = "BORONGAN_ASK_SURVEY_DATE"
    BORONGAN_ASK_SURVEY_TIME = "BORONGAN_ASK_SURVEY_TIME"
    BORONGAN_ASK_BUDGET = "BORONGAN_ASK_BUDGET"
    HARIAN_ASK_CUSTOMER_ID = "HARIAN_ASK_CUSTOMER_ID"
    HARIAN_ASK_PHONE = "HARIAN_ASK_PHONE"
    HARIAN_ASK_SPECIALIZATION = "HARIAN_ASK_SPECIALIZATION"
    HARIAN_ASK_DESCRIPTION = "HARIAN_ASK_DESCRIPTION"
    HARIAN_ASK_WORKER_COUNT = "HARIAN_ASK_WORKER_COUNT"
    HARIAN_ASK_START_DATE = "HARIAN_ASK_START_DATE"
    HARIAN_ASK_END_DATE = "HARIAN_ASK_END_DATE"
    HARIAN_ASK_SESSION = "HARIAN_ASK_SESSION"
    HARIAN_ASK_PHOTO = "HARIAN_ASK_PHOTO"
    HARIAN_ASK_ADDRESS = "HARIAN_ASK_ADDRESS"
    CALCULATE_PRICE = "CALCULATE_PRICE"
    CONFIRM_RESERVATION = "CONFIRM_RESERVATION"
    EDIT_SLOT = "EDIT_SLOT"
    TICKET_LOOKUP = "TICKET_LOOKUP"
    TICKET_CREATED = "TICKET_CREATED"
    CANCELLED = "CANCELLED"


class MessageSender(StrEnum):
    """Supported chat-message authors."""

    USER = "user"
    BOT = "bot"


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """One immutable message in conversation history."""

    id: str
    sender: MessageSender
    text: str
    created_at: datetime
    client_message_id: str | None = None


@dataclass(frozen=True, slots=True)
class QuickReply:
    """A label shown to users and its canonical submitted value."""

    label: str
    value: str


@dataclass(frozen=True, slots=True)
class ConversationContext:
    """Current server-owned state and safe response snapshot."""

    conversation_id: str
    locale: str
    state: ConversationState
    messages: tuple[ChatMessage, ...]
    quick_replies: tuple[QuickReply, ...]
    created_at: datetime
    updated_at: datetime
    collected_slots: dict[str, object] = field(default_factory=dict)
    reservation_summary: dict[str, object] | None = None
    price_breakdown: dict[str, object] | None = None
    ticket: dict[str, object] | None = None
    last_intent: Intent | None = None
    last_confidence: float | None = None

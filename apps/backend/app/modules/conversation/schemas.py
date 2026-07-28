"""HTTP request and response DTOs for conversation endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.conversation.domain import ConversationState, MessageSender


class ConversationSchema(BaseModel):
    """Strict base schema matching OpenAPI additionalProperties=false."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class CreateConversationRequest(ConversationSchema):
    """Optional settings accepted while opening a chat session."""

    locale: Literal["id-ID"] = "id-ID"


class SendMessageRequest(ConversationSchema):
    """One user message with a client-owned idempotency key."""

    client_message_id: str = Field(min_length=8, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    text: str = Field(min_length=1, max_length=1000)

    @field_validator("text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message text cannot be blank.")
        return value.strip()


class SuccessStatus(ConversationSchema):
    """Success metadata used by the normative API envelope."""

    code: Literal[120000000, 120100000]
    message: str
    error_details: list[object] = Field(default_factory=list, alias="errorDetails")


class ChatMessageData(ConversationSchema):
    """Serialized chat message."""

    id: str = Field(min_length=26, max_length=26)
    sender: MessageSender
    text: str = Field(min_length=1, max_length=2000)
    created_at: datetime


class QuickReplyData(ConversationSchema):
    """Serialized quick-reply option."""

    label: str = Field(min_length=1, max_length=80)
    value: str = Field(min_length=1, max_length=80)


class ConversationData(ConversationSchema):
    """Conversation snapshot safe for rendering by the frontend."""

    conversation_id: str = Field(min_length=26, max_length=26)
    state: ConversationState
    messages: list[ChatMessageData]
    quick_replies: list[QuickReplyData]
    collected_slots: dict[str, object]
    reservation_summary: dict[str, object] | None = None
    price_breakdown: dict[str, object] | None = None
    ticket: dict[str, object] | None = None


class ConversationResponse(ConversationSchema):
    """Success response envelope for all conversation endpoints."""

    status: SuccessStatus
    data: ConversationData

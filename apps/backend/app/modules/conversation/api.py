"""FastAPI endpoints for conversation session and message routing."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.modules.conversation.domain import ChatMessage, ConversationContext
from app.modules.conversation.repository import (
    ConversationRepository,
    InMemoryConversationRepository,
)
from app.modules.conversation.schemas import (
    ChatMessageData,
    ConversationData,
    ConversationResponse,
    CreateConversationRequest,
    QuickReplyData,
    SendMessageRequest,
    SuccessStatus,
)
from app.modules.conversation.service import (
    ConversationResult,
    ConversationService,
    IntentPredictor,
)
from app.modules.nlp.model import IntentModel, ModelArtifactError, load_intent_model
from app.shared.config import get_settings
from app.shared.errors import ApplicationError

router = APIRouter(prefix="/conversations", tags=["conversations"])
_repository = InMemoryConversationRepository()


async def get_conversation_repository() -> ConversationRepository:
    """Return the process-local repository; replace with SQL in CONV-08."""

    return _repository


@lru_cache
def _load_intent_predictor() -> IntentModel:
    try:
        return load_intent_model(get_settings().model_path)
    except ModelArtifactError as error:
        raise ApplicationError(
            code="NLP_MODEL_UNAVAILABLE",
            message=(
                "Maaf, layanan pemahaman pertanyaan sedang belum tersedia. Silakan coba lagi."
            ),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            retryable=True,
        ) from error


async def get_intent_predictor() -> IntentModel:
    """Load and cache the versioned NLP model on first FAQ message."""

    return _load_intent_predictor()


def _message_data(message: ChatMessage) -> ChatMessageData:
    return ChatMessageData(
        id=message.id,
        sender=message.sender,
        text=message.text,
        created_at=message.created_at,
    )


def _conversation_data(
    context: ConversationContext,
    *,
    messages: tuple[ChatMessage, ...] | None = None,
) -> ConversationData:
    selected_messages = context.messages if messages is None else messages
    return ConversationData(
        conversation_id=context.conversation_id,
        state=context.state,
        messages=[_message_data(message) for message in selected_messages],
        quick_replies=[
            QuickReplyData(label=reply.label, value=reply.value) for reply in context.quick_replies
        ],
        collected_slots=context.collected_slots,
        reservation_summary=context.reservation_summary,
        price_breakdown=context.price_breakdown,
        ticket=context.ticket,
    )


def _response(
    result: ConversationResult,
    *,
    created: bool = False,
) -> ConversationResponse:
    return ConversationResponse(
        status=SuccessStatus(
            code=120100000 if created else 120000000,
            message="Created." if created else "Success.",
        ),
        data=_conversation_data(result.context, messages=result.new_messages),
    )


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    repository: Annotated[ConversationRepository, Depends(get_conversation_repository)],
    payload: CreateConversationRequest | None = None,
) -> ConversationResponse:
    request = payload or CreateConversationRequest()
    result = ConversationService(repository).create_conversation(locale=request.locale)
    return _response(result, created=True)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    repository: Annotated[ConversationRepository, Depends(get_conversation_repository)],
) -> ConversationResponse:
    context = ConversationService(repository).get_conversation(conversation_id)
    return ConversationResponse(
        status=SuccessStatus(code=120000000, message="Success."),
        data=_conversation_data(context),
    )


@router.post("/{conversation_id}/messages", response_model=ConversationResponse)
async def send_message(
    conversation_id: str,
    payload: SendMessageRequest,
    repository: Annotated[ConversationRepository, Depends(get_conversation_repository)],
    predictor: Annotated[IntentPredictor, Depends(get_intent_predictor)],
) -> ConversationResponse:
    result = ConversationService(repository, predictor=predictor).process_message(
        conversation_id,
        payload.text,
    )
    return _response(result)

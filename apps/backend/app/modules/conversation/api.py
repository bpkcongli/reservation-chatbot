"""FastAPI endpoints for conversation session and message routing."""

from functools import lru_cache
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.modules.conversation.domain import ChatMessage, ConversationContext
from app.modules.conversation.logger import (
    ConversationTurnLogger,
    JsonlConversationLogger,
)
from app.modules.conversation.repository import (
    ConversationRepository,
    SqlAlchemyConversationRepository,
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
from app.shared.database import get_db_session
from app.shared.errors import ApplicationError

router = APIRouter(prefix="/conversations", tags=["conversations"])


async def get_conversation_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> ConversationRepository:
    """Return a transactional repository backed by configured MySQL."""

    return SqlAlchemyConversationRepository(session)


@lru_cache
def _load_conversation_logger() -> JsonlConversationLogger:
    return JsonlConversationLogger(get_settings().conversation_log_dir)


async def get_conversation_logger() -> ConversationTurnLogger:
    """Return the process-wide append-only logger."""

    return _load_conversation_logger()


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
    turn_logger: Annotated[ConversationTurnLogger, Depends(get_conversation_logger)],
) -> ConversationResponse:
    result = ConversationService(
        repository,
        predictor=predictor,
        turn_logger=turn_logger,
        timezone=ZoneInfo(get_settings().app_timezone),
    ).process_message(
        conversation_id,
        payload.text,
        client_message_id=payload.client_message_id,
    )
    return _response(result)

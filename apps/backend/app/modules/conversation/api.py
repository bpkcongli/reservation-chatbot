"""FastAPI endpoints for conversation session and message routing."""

from functools import lru_cache
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.modules.attachment.repository import (
    AttachmentRepository,
    SqlAlchemyAttachmentRepository,
)
from app.modules.attachment.service import AttachmentService, LocalAttachmentStorage
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
    AttachmentData,
    AttachmentUploadData,
    AttachmentUploadResponse,
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
    ReservationFinalizer,
    TicketLookup,
)
from app.modules.nlp.model import IntentModel, ModelArtifactError, load_intent_model
from app.modules.reservation.repository import SqlAlchemyReservationFinalizer
from app.modules.ticketing.repository import SqlAlchemyTicketRepository
from app.modules.ticketing.service import TicketService
from app.shared.config import get_settings
from app.shared.database import get_db_session
from app.shared.errors import ApplicationError

router = APIRouter(prefix="/conversations", tags=["conversations"])


async def get_conversation_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> ConversationRepository:
    """Return a transactional repository backed by configured MySQL."""

    return SqlAlchemyConversationRepository(session)


async def get_attachment_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> AttachmentRepository:
    """Return attachment metadata storage in the request transaction."""

    return SqlAlchemyAttachmentRepository(session)


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


async def get_ticket_lookup(
    session: Annotated[Session, Depends(get_db_session)],
) -> TicketLookup:
    """Return ticket lookup backed by the request database session."""

    return TicketService(SqlAlchemyTicketRepository(session))


async def get_reservation_finalizer(
    session: Annotated[Session, Depends(get_db_session)],
) -> ReservationFinalizer:
    """Use the same request session as conversation persistence."""

    return SqlAlchemyReservationFinalizer(session)


@router.post(
    "/{conversation_id}/attachments",
    response_model=AttachmentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    conversation_id: str,
    file: Annotated[UploadFile, File()],
    conversation_repository: Annotated[
        ConversationRepository,
        Depends(get_conversation_repository),
    ],
    attachment_repository: Annotated[
        AttachmentRepository,
        Depends(get_attachment_repository),
    ],
) -> AttachmentUploadResponse:
    settings = get_settings()
    max_size_bytes = settings.max_upload_mb * 1024 * 1024
    original_filename = file.filename
    declared_content_type = file.content_type
    try:
        content = await file.read(max_size_bytes + 1)
    finally:
        await file.close()
    attachment = AttachmentService(
        conversation_repository,
        attachment_repository,
        LocalAttachmentStorage(settings.upload_dir),
        max_size_bytes=max_size_bytes,
    ).upload(
        conversation_id,
        original_filename=original_filename,
        declared_content_type=declared_content_type,
        content=content,
    )
    return AttachmentUploadResponse(
        status=SuccessStatus(code=120100000, message="Created."),
        data=AttachmentUploadData(
            conversation_id=conversation_id,
            attachment=AttachmentData(
                attachment_id=attachment.id,
                content_type=attachment.content_type,
                size_bytes=attachment.size_bytes,
            ),
        ),
    )


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
    ticket_lookup: Annotated[TicketLookup, Depends(get_ticket_lookup)],
    reservation_finalizer: Annotated[
        ReservationFinalizer,
        Depends(get_reservation_finalizer),
    ],
) -> ConversationResponse:
    result = ConversationService(
        repository,
        predictor=predictor,
        turn_logger=turn_logger,
        ticket_lookup=ticket_lookup,
        reservation_finalizer=reservation_finalizer,
        timezone=ZoneInfo(get_settings().app_timezone),
    ).process_message(
        conversation_id,
        payload.text,
        client_message_id=payload.client_message_id,
    )
    return _response(result)

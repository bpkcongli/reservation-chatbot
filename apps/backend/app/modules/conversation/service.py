"""Application service for session lifecycle and FAQ turns."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Protocol
from zoneinfo import ZoneInfo

from fastapi import status

from app.modules.conversation.commands import GlobalCommand, parse_global_command
from app.modules.conversation.dialog import (
    is_reservation_state,
    process_reservation_turn,
    prompt_for_state,
    start_reservation,
)
from app.modules.conversation.domain import (
    ChatMessage,
    ConversationContext,
    ConversationState,
    MessageSender,
    QuickReply,
)
from app.modules.conversation.extractors import extract_ticket_number
from app.modules.conversation.faq import (
    DIRECT_INTENTS,
    FALLBACK_REPLIES,
    FALLBACK_TEXT,
    FAQ_ANSWERS,
    INFO_MENU_REPLIES,
    INFO_MENU_TEXT,
    SELECT_SERVICE_REPLIES,
    SELECT_SERVICE_TEXT,
    WELCOME_REPLIES,
    WELCOME_TEXT,
)
from app.modules.conversation.ids import generate_ulid
from app.modules.conversation.logger import (
    ConversationTurnEvent,
    ConversationTurnLogger,
    mask_extracted_slots,
    mask_pii_text,
    normalize_log_text,
)
from app.modules.conversation.repository import ConversationRepository
from app.modules.nlp.model import IntentPrediction
from app.modules.nlp.taxonomy import Intent
from app.shared.errors import ApplicationError

Clock = Callable[[], datetime]
IdFactory = Callable[[datetime], str]
JAKARTA_TIMEZONE = ZoneInfo("Asia/Jakarta")


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
        turn_logger: ConversationTurnLogger | None = None,
        timezone: ZoneInfo = JAKARTA_TIMEZONE,
        clock: Clock = utc_now,
        id_factory: IdFactory = generate_ulid,
    ) -> None:
        self._repository = repository
        self._predictor = predictor
        self._turn_logger = turn_logger
        self._timezone = timezone
        self._clock = clock
        self._id_factory = id_factory

    def _message(
        self,
        sender: MessageSender,
        text: str,
        now: datetime,
        *,
        client_message_id: str | None = None,
    ) -> ChatMessage:
        return ChatMessage(
            id=self._id_factory(now),
            sender=sender,
            text=text,
            created_at=now,
            client_message_id=client_message_id,
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

    def process_message(
        self,
        conversation_id: str,
        text: str,
        *,
        client_message_id: str | None = None,
    ) -> ConversationResult:
        context = self.get_conversation(conversation_id)
        if client_message_id is not None:
            previous_result = self._find_idempotent_result(
                context,
                client_message_id=client_message_id,
                text=text,
            )
            if previous_result is not None:
                return previous_result

        now = self._clock()
        user_message = self._message(
            MessageSender.USER,
            text,
            now,
            client_message_id=client_message_id,
        )
        normalized = text.casefold().strip()
        state: ConversationState
        response_text: str
        quick_replies: tuple[QuickReply, ...]
        intent: Intent | None
        confidence: float | None
        collected_slots = dict(context.collected_slots)
        validation_field: str | None = None

        command = parse_global_command(text)
        if command is not None:
            (
                state,
                response_text,
                quick_replies,
                collected_slots,
            ) = self._handle_global_command(context, command)
            intent = None
            confidence = None
        elif is_reservation_state(context.state):
            decision = process_reservation_turn(
                context,
                text,
                today=now.astimezone(self._timezone).date(),
            )
            state = decision.state
            response_text = decision.text
            quick_replies = decision.quick_replies
            collected_slots = decision.collected_slots
            validation_field = decision.validation_field
            intent = None
            confidence = None
        elif context.state is ConversationState.SELECT_SERVICE and normalized in {
            "borongan",
            "harian",
        }:
            decision = start_reservation(normalized)
            state = decision.state
            response_text = decision.text
            quick_replies = decision.quick_replies
            collected_slots = decision.collected_slots
            intent = Intent.START_RESERVATION
            confidence = 1.0
        elif context.state is ConversationState.SELECT_SERVICE:
            state = ConversationState.SELECT_SERVICE
            response_text = (
                "Maaf, pilihan layanannya belum dikenali. Silakan pilih Jasa Borongan "
                "atau Tukang Harian agar kami dapat melanjutkan reservasi."
            )
            quick_replies = SELECT_SERVICE_REPLIES
            intent = None
            confidence = None
        elif context.state is ConversationState.TICKET_LOOKUP:
            ticket_number = extract_ticket_number(text)
            state = ConversationState.TICKET_LOOKUP
            quick_replies = ()
            intent = None
            confidence = None
            if ticket_number is None:
                response_text = (
                    "Maaf, nomor tiketnya belum sesuai. Format yang dapat digunakan: "
                    "TKT-YYYYMMDD-XXXXXX, misalnya TKT-20260728-AB12CD. Mohon masukkan "
                    "kembali agar kami dapat melanjutkan pemeriksaan."
                )
                validation_field = "ticket_number"
            else:
                collected_slots["ticket_number"] = ticket_number
                response_text = (
                    f"Baik, nomor tiket {ticket_number} sudah sesuai format. "
                    "Pemeriksaan status tiket akan dilanjutkan pada langkah berikutnya."
                )
        elif normalized == "info":
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
        elif context.state in {
            ConversationState.CALCULATE_PRICE,
            ConversationState.CONFIRM_RESERVATION,
        }:
            state = context.state
            response_text = (
                "Data reservasi sudah lengkap. Silakan ketik “batal”, “menu”, "
                "“bantuan”, atau “mulai ulang” bila Anda ingin mengubah alur saat ini."
            )
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
            collected_slots=collected_slots,
            last_intent=intent,
            last_confidence=confidence,
        )
        self._repository.save(updated)
        self._log_turn(
            before=context,
            after=updated,
            raw_text=text,
            response_text=response_text,
            now=now,
        )
        if validation_field is not None:
            raise ApplicationError(
                code="INVALID_SLOT",
                message=response_text,
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                field=validation_field,
            )
        return ConversationResult(context=updated, new_messages=new_messages)

    def _find_idempotent_result(
        self,
        context: ConversationContext,
        *,
        client_message_id: str,
        text: str,
    ) -> ConversationResult | None:
        for index, message in enumerate(context.messages):
            if message.client_message_id != client_message_id:
                continue
            if message.text != text:
                raise ApplicationError(
                    code="CLIENT_MESSAGE_ID_CONFLICT",
                    message=(
                        "ID pesan tersebut sudah digunakan untuk isi pesan yang berbeda. "
                        "Mohon kirim ulang dengan ID pesan baru."
                    ),
                    status_code=status.HTTP_409_CONFLICT,
                    field="client_message_id",
                )
            new_messages = context.messages[index : index + 2]
            return ConversationResult(context=context, new_messages=new_messages)
        return None

    def _log_turn(
        self,
        *,
        before: ConversationContext,
        after: ConversationContext,
        raw_text: str,
        response_text: str,
        now: datetime,
    ) -> None:
        if self._turn_logger is None:
            return

        extracted_slots = {
            field: value
            for field, value in after.collected_slots.items()
            if before.collected_slots.get(field) != value
        }
        masked_raw_text = mask_pii_text(raw_text, state=before.state)
        model_version_value = getattr(self._predictor, "model_version", None)
        model_version = str(model_version_value) if model_version_value is not None else None
        self._turn_logger.append(
            ConversationTurnEvent(
                event_id=self._id_factory(now),
                timestamp=now.astimezone(self._timezone).isoformat(),
                conversation_id=after.conversation_id,
                turn=sum(message.sender is MessageSender.USER for message in after.messages),
                sender=MessageSender.USER.value,
                raw_text=masked_raw_text,
                normalized_text=normalize_log_text(masked_raw_text),
                predicted_intent=(
                    after.last_intent.value if after.last_intent is not None else None
                ),
                confidence=after.last_confidence,
                state_before=before.state.value,
                state_after=after.state.value,
                extracted_slots=mask_extracted_slots(extracted_slots),
                response_text=mask_pii_text(response_text),
                model_version=model_version,
            )
        )

    def _handle_global_command(
        self,
        context: ConversationContext,
        command: GlobalCommand,
    ) -> tuple[ConversationState, str, tuple[QuickReply, ...], dict[str, object]]:
        if command is GlobalCommand.CANCEL:
            return (
                ConversationState.CANCELLED,
                (
                    "Baik, proses reservasi dibatalkan dan tidak ada tiket yang dibuat. "
                    "Ada hal lain yang dapat saya bantu?"
                ),
                WELCOME_REPLIES,
                {},
            )
        if command is GlobalCommand.MENU:
            return (
                ConversationState.WELCOME,
                (
                    "Baik, Anda sudah kembali ke menu utama. Silakan pilih informasi "
                    "layanan atau mulai reservasi."
                ),
                WELCOME_REPLIES,
                {},
            )
        if command is GlobalCommand.RESTART:
            return (
                ConversationState.WELCOME,
                (
                    "Baik, percakapan dan data reservasi sementara sudah dimulai ulang. "
                    "Silakan pilih kebutuhan Anda dari awal."
                ),
                WELCOME_REPLIES,
                {},
            )

        current_prompt = prompt_for_state(context.state)
        progress = (
            f" Saat ini Anda berada pada langkah berikut: {current_prompt}"
            if current_prompt is not None
            else ""
        )
        return (
            context.state,
            (
                "Saya siap membantu. Anda dapat mengetik “menu” untuk kembali ke menu "
                "utama, “batal” untuk membatalkan reservasi, atau “mulai ulang” untuk "
                f"memulai dari awal.{progress}"
            ),
            context.quick_replies,
            dict(context.collected_slots),
        )

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

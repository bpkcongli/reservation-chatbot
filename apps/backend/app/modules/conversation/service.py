"""Application service for session lifecycle and FAQ turns."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Protocol
from zoneinfo import ZoneInfo

from fastapi import status

from app.modules.conversation.commands import GlobalCommand, parse_global_command
from app.modules.conversation.dialog import (
    CONFIRMATION_REPLIES,
    begin_slot_edit,
    confirmation_prompt,
    edit_prompt,
    edit_replies,
    is_reservation_state,
    parse_edit_field,
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
from app.modules.reservation.summary import build_confirmation_snapshot
from app.modules.ticketing.domain import TicketView
from app.shared.errors import ApplicationError

Clock = Callable[[], datetime]
IdFactory = Callable[[datetime], str]
JAKARTA_TIMEZONE = ZoneInfo("Asia/Jakarta")


class IntentPredictor(Protocol):
    """Minimal NLP interface required by conversation routing."""

    def predict(self, text: str, *, threshold: float | None = None) -> IntentPrediction:
        """Return the top intent and runtime fallback decision."""


class TicketLookup(Protocol):
    def get(self, ticket_number: str) -> TicketView:
        """Return a safe ticket view or raise an application error."""


class ReservationFinalizer(Protocol):
    def finalize(
        self,
        context: ConversationContext,
        *,
        created_at: datetime,
    ) -> TicketView:
        """Stage one reservation and ticket in the current transaction."""


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
        ticket_lookup: TicketLookup | None = None,
        reservation_finalizer: ReservationFinalizer | None = None,
        turn_logger: ConversationTurnLogger | None = None,
        timezone: ZoneInfo = JAKARTA_TIMEZONE,
        clock: Clock = utc_now,
        id_factory: IdFactory = generate_ulid,
    ) -> None:
        self._repository = repository
        self._predictor = predictor
        self._ticket_lookup = ticket_lookup
        self._reservation_finalizer = reservation_finalizer
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
        reservation_summary = context.reservation_summary
        price_breakdown = context.price_breakdown
        ticket = context.ticket
        reservation_confirmed = context.reservation_confirmed
        validation_field: str | None = None

        command = parse_global_command(text)
        if command is not None:
            (
                state,
                response_text,
                quick_replies,
                collected_slots,
            ) = self._handle_global_command(context, command)
            if command in {
                GlobalCommand.CANCEL,
                GlobalCommand.MENU,
                GlobalCommand.RESTART,
            }:
                reservation_summary = None
                price_breakdown = None
                ticket = None
                reservation_confirmed = False
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
            if validation_field is None and state in {
                ConversationState.CALCULATE_PRICE,
                ConversationState.CONFIRM_RESERVATION,
            }:
                reservation_summary, price_breakdown = build_confirmation_snapshot(
                    collected_slots,
                    today=now.astimezone(self._timezone).date(),
                )
                state = ConversationState.CONFIRM_RESERVATION
                response_text = confirmation_prompt(str(collected_slots.get("service_type", "")))
                quick_replies = CONFIRMATION_REPLIES
                reservation_confirmed = False
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
            reservation_summary = None
            price_breakdown = None
            ticket = None
            reservation_confirmed = False
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
        elif context.state is ConversationState.CONFIRM_RESERVATION:
            service_type = str(context.collected_slots.get("service_type", ""))
            edit_field = parse_edit_field(text, service_type)
            if normalized in {"ya", "iya", "setuju", "konfirmasi"}:
                if self._reservation_finalizer is None:
                    raise ApplicationError(
                        code="RESERVATION_SERVICE_UNAVAILABLE",
                        message="Maaf, layanan konfirmasi reservasi sedang belum tersedia.",
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        retryable=True,
                    )
                finalized_ticket = self._reservation_finalizer.finalize(
                    context,
                    created_at=now.astimezone(self._timezone),
                )
                state = ConversationState.TICKET_CREATED
                response_text = (
                    f"Reservasi berhasil dikonfirmasi. Nomor tiket Anda "
                    f"{finalized_ticket.ticket_number} dengan status "
                    f"{finalized_ticket.status.value}. Estimasi harga fixed "
                    f"Rp{finalized_ticket.estimated_price:,}. Pengiriman email "
                    "masih berupa simulasi."
                )
                quick_replies = ()
                reservation_confirmed = True
                ticket = {
                    "ticket_number": finalized_ticket.ticket_number,
                    "service_type": finalized_ticket.service_type.value,
                    "status": finalized_ticket.status.value,
                    "pricing_version": finalized_ticket.pricing_version,
                    "estimated_price": finalized_ticket.estimated_price,
                    "budget": finalized_ticket.budget,
                    "created_at": finalized_ticket.created_at.astimezone(
                        self._timezone
                    ).isoformat(),
                    "email_delivery": finalized_ticket.email_delivery.value,
                }
            elif normalized in {"ubah", "edit", "tidak"}:
                state = ConversationState.EDIT_SLOT
                response_text = edit_prompt(service_type)
                quick_replies = edit_replies(service_type)
                reservation_confirmed = False
            elif edit_field is not None:
                decision = begin_slot_edit(context, edit_field)
                state = decision.state
                response_text = decision.text
                quick_replies = decision.quick_replies
                collected_slots = decision.collected_slots
                reservation_summary = None
                price_breakdown = None
                reservation_confirmed = False
            else:
                state = ConversationState.CONFIRM_RESERVATION
                response_text = (
                    "Maaf, pilihan konfirmasinya belum dikenali. Silakan pilih ya, "
                    "ubah data, atau batal."
                )
                quick_replies = CONFIRMATION_REPLIES
            intent = None
            confidence = None
        elif context.state is ConversationState.EDIT_SLOT:
            service_type = str(context.collected_slots.get("service_type", ""))
            edit_field = parse_edit_field(text, service_type)
            if edit_field is None:
                state = ConversationState.EDIT_SLOT
                response_text = edit_prompt(service_type)
                quick_replies = edit_replies(service_type)
            else:
                decision = begin_slot_edit(context, edit_field)
                state = decision.state
                response_text = decision.text
                quick_replies = decision.quick_replies
                collected_slots = decision.collected_slots
                reservation_summary = None
                price_breakdown = None
                reservation_confirmed = False
            intent = None
            confidence = None
        elif context.state is ConversationState.TICKET_LOOKUP:
            ticket_number = extract_ticket_number(text)
            intent = None
            confidence = None
            if ticket_number is None:
                state = ConversationState.TICKET_LOOKUP
                quick_replies = ()
                response_text = (
                    "Maaf, nomor tiketnya belum sesuai. Format yang dapat digunakan: "
                    "TKT-YYYYMMDD-XXXXXX, misalnya TKT-20260728-AB12CD. Mohon masukkan "
                    "kembali agar kami dapat melanjutkan pemeriksaan."
                )
                validation_field = "ticket_number"
            else:
                if self._ticket_lookup is None:
                    raise ApplicationError(
                        code="TICKET_SERVICE_UNAVAILABLE",
                        message="Maaf, layanan pemeriksaan tiket sedang belum tersedia.",
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        retryable=True,
                    )
                found_ticket = self._ticket_lookup.get(ticket_number)
                ticket = {
                    "ticket_number": found_ticket.ticket_number,
                    "service_type": found_ticket.service_type.value,
                    "status": found_ticket.status.value,
                    "pricing_version": found_ticket.pricing_version,
                    "estimated_price": found_ticket.estimated_price,
                    "budget": found_ticket.budget,
                    "created_at": found_ticket.created_at.astimezone(self._timezone).isoformat(),
                    "email_delivery": found_ticket.email_delivery.value,
                }
                collected_slots["ticket_number"] = ticket_number
                state = ConversationState.INFO_MODE
                quick_replies = INFO_MENU_REPLIES
                response_text = (
                    f"Tiket {ticket_number} ditemukan dengan status "
                    f"{found_ticket.status.value}. Estimasi harga fixed adalah "
                    f"Rp{found_ticket.estimated_price:,}. Pengiriman email masih "
                    "berupa simulasi."
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
            reservation_summary = None
            price_breakdown = None
            ticket = None
            reservation_confirmed = False
            intent = Intent.START_RESERVATION
            confidence = 1.0
        elif context.state is ConversationState.CALCULATE_PRICE:
            reservation_summary, price_breakdown = build_confirmation_snapshot(
                collected_slots,
                today=now.astimezone(self._timezone).date(),
            )
            state = ConversationState.CONFIRM_RESERVATION
            response_text = confirmation_prompt(str(collected_slots.get("service_type", "")))
            quick_replies = CONFIRMATION_REPLIES
            reservation_confirmed = False
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
            reservation_summary=reservation_summary,
            price_breakdown=price_breakdown,
            ticket=ticket,
            reservation_confirmed=reservation_confirmed,
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

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from app.modules.catalog.domain import ServiceType
from app.modules.conversation.domain import ConversationState, MessageSender
from app.modules.conversation.faq import FALLBACK_TEXT, WELCOME_TEXT
from app.modules.conversation.logger import ConversationTurnEvent
from app.modules.conversation.repository import InMemoryConversationRepository
from app.modules.conversation.service import ConversationService
from app.modules.nlp.model import IntentPrediction
from app.modules.nlp.taxonomy import Intent
from app.modules.ticketing.domain import (
    EmailDelivery,
    TicketStatus,
    TicketView,
)
from app.shared.errors import ApplicationError

FIXED_NOW = datetime(2026, 7, 29, 9, 0, tzinfo=UTC)


class StubPredictor:
    def __init__(self, prediction: IntentPrediction) -> None:
        self.prediction = prediction
        self.received_texts: list[str] = []

    def predict(self, text: str, *, threshold: float | None = None) -> IntentPrediction:
        self.received_texts.append(text)
        return self.prediction


class CapturingTurnLogger:
    def __init__(self) -> None:
        self.events: list[ConversationTurnEvent] = []

    def append(self, event: ConversationTurnEvent) -> None:
        self.events.append(event)


class StubTicketLookup:
    def __init__(self, ticket: TicketView) -> None:
        self.ticket = ticket

    def get(self, ticket_number: str) -> TicketView:
        assert ticket_number == self.ticket.ticket_number
        return self.ticket


def id_factory() -> Iterator[str]:
    for index in range(1, 50):
        yield f"01K1A2B3C4D5E6F7G8H9J{index:04d}"


def build_service(
    *,
    predictor: StubPredictor | None = None,
    turn_logger: CapturingTurnLogger | None = None,
    ticket_lookup: StubTicketLookup | None = None,
) -> tuple[ConversationService, InMemoryConversationRepository]:
    identifiers = id_factory()
    repository = InMemoryConversationRepository()
    service = ConversationService(
        repository,
        predictor=predictor,
        turn_logger=turn_logger,
        ticket_lookup=ticket_lookup,
        clock=lambda: FIXED_NOW,
        id_factory=lambda _: next(identifiers),
    )
    return service, repository


def test_create_and_get_conversation_returns_welcome_context() -> None:
    service, _ = build_service()

    created = service.create_conversation()
    restored = service.get_conversation(created.context.conversation_id)

    assert restored.state is ConversationState.WELCOME
    assert restored.locale == "id-ID"
    assert restored.messages == created.context.messages
    assert restored.messages[0].sender is MessageSender.BOT
    assert restored.messages[0].text == WELCOME_TEXT
    assert [reply.value for reply in restored.quick_replies] == ["info", "reservation"]
    assert restored.collected_slots == {}
    assert restored.reservation_summary is None


def test_unknown_conversation_returns_customer_friendly_not_found() -> None:
    service, _ = build_service()

    with pytest.raises(ApplicationError) as error:
        service.get_conversation("01K1A2B3C4D5E6F7G8H9J0000")

    assert error.value.status_code == 404
    assert error.value.detail.code == "CONVERSATION_NOT_FOUND"
    assert "belum ditemukan" in error.value.detail.message


def test_info_quick_reply_opens_information_menu_without_model() -> None:
    service, _ = build_service()
    created = service.create_conversation()

    result = service.process_message(created.context.conversation_id, "info")

    assert result.context.state is ConversationState.INFO_MODE
    assert len(result.new_messages) == 2
    assert len(result.context.messages) == 3
    assert [reply.value for reply in result.context.quick_replies] == [
        "borongan",
        "harian",
        "harga",
        "reservation",
    ]


def test_confident_intent_returns_faq_answer_and_keeps_info_mode() -> None:
    predictor = StubPredictor(
        IntentPrediction(
            intent=Intent.HARIAN_INFO,
            top_intent=Intent.HARIAN_INFO,
            confidence=0.81,
            is_fallback=False,
        )
    )
    service, _ = build_service(predictor=predictor)
    created = service.create_conversation()

    result = service.process_message(
        created.context.conversation_id,
        "Spesialisasi tukang apa saja?",
    )

    assert predictor.received_texts == ["Spesialisasi tukang apa saja?"]
    assert result.context.state is ConversationState.INFO_MODE
    assert "cat, genteng, AC, listrik, keramik, dan pipa" in result.new_messages[1].text
    assert result.context.last_intent is Intent.HARIAN_INFO
    assert result.context.last_confidence == 0.81


def test_low_confidence_prediction_returns_directed_fallback() -> None:
    predictor = StubPredictor(
        IntentPrediction(
            intent=None,
            top_intent=Intent.SERVICE_OVERVIEW,
            confidence=0.14,
            is_fallback=True,
        )
    )
    service, _ = build_service(predictor=predictor)
    created = service.create_conversation()

    result = service.process_message(created.context.conversation_id, "Bantu hal lain")

    assert result.context.state is ConversationState.FALLBACK
    assert result.new_messages[1].text == FALLBACK_TEXT
    assert result.context.last_intent is None
    assert result.context.last_confidence == 0.14
    assert [reply.value for reply in result.context.quick_replies] == [
        "borongan",
        "harian",
        "harga",
        "reservation",
    ]


def test_start_reservation_intent_transitions_to_service_selection() -> None:
    predictor = StubPredictor(
        IntentPrediction(
            intent=Intent.START_RESERVATION,
            top_intent=Intent.START_RESERVATION,
            confidence=0.72,
            is_fallback=False,
        )
    )
    service, _ = build_service(predictor=predictor)
    created = service.create_conversation()

    result = service.process_message(created.context.conversation_id, "Saya mau booking")

    assert result.context.state is ConversationState.SELECT_SERVICE
    assert [reply.value for reply in result.context.quick_replies] == ["borongan", "harian"]


def test_help_has_priority_over_active_slot_and_preserves_progress() -> None:
    service, _ = build_service()
    created = service.create_conversation()
    service.process_message(created.context.conversation_id, "reservation")
    service.process_message(created.context.conversation_id, "borongan")
    progressed = service.process_message(created.context.conversation_id, "0123456789")

    helped = service.process_message(created.context.conversation_id, "bantuan")

    assert progressed.context.state is ConversationState.BORONGAN_ASK_PHONE
    assert helped.context.state is ConversationState.BORONGAN_ASK_PHONE
    assert helped.context.collected_slots["customer_id"] == "0123456789"
    assert "081234567890" in helped.new_messages[1].text
    assert "mulai ulang" in helped.new_messages[1].text


def test_cancel_clears_draft_without_creating_ticket() -> None:
    service, _ = build_service()
    created = service.create_conversation()
    service.process_message(created.context.conversation_id, "reservation")
    service.process_message(created.context.conversation_id, "harian")
    service.process_message(created.context.conversation_id, "0123456789")

    cancelled = service.process_message(created.context.conversation_id, "batal")

    assert cancelled.context.state is ConversationState.CANCELLED
    assert cancelled.context.collected_slots == {}
    assert cancelled.context.ticket is None
    assert "tidak ada tiket yang dibuat" in cancelled.new_messages[1].text


def test_invalid_slot_keeps_state_and_previously_collected_slots() -> None:
    service, repository = build_service()
    created = service.create_conversation()
    service.process_message(created.context.conversation_id, "reservation")
    service.process_message(created.context.conversation_id, "borongan")
    service.process_message(created.context.conversation_id, "0123456789")

    with pytest.raises(ApplicationError) as error:
        service.process_message(created.context.conversation_id, "12345")

    restored = repository.get(created.context.conversation_id)
    assert error.value.status_code == 422
    assert error.value.detail.field == "phone_number"
    assert "081234567890" in error.value.detail.message
    assert restored is not None
    assert restored.state is ConversationState.BORONGAN_ASK_PHONE
    assert restored.collected_slots == {
        "service_type": "borongan",
        "customer_id": "0123456789",
    }


def test_borongan_slot_priority_reaches_confirmation_state() -> None:
    service, _ = build_service()
    created = service.create_conversation()
    messages = (
        "reservation",
        "borongan",
        "0123456789",
        "0812 3456 7890",
        "rumah",
        "Jalan Melati No. 10 Jakarta",
        "2 Agustus 2026",
        "09:00",
        "20 juta",
    )

    result = created
    for message in messages:
        result = service.process_message(created.context.conversation_id, message)

    assert result.context.state is ConversationState.CONFIRM_RESERVATION
    assert result.context.collected_slots == {
        "service_type": "borongan",
        "customer_id": "0123456789",
        "phone_number": "+6281234567890",
        "building_type": "rumah",
        "survey_address": "Jalan Melati No. 10 Jakarta",
        "survey_date": "2026-08-02",
        "survey_time": "09:00",
        "budget": 20_000_000,
    }
    assert result.context.reservation_summary is not None
    assert result.context.reservation_summary["phone_number_masked"] == "+62812****7890"
    assert result.context.price_breakdown is not None
    assert result.context.price_breakdown["estimated_price"] == 5_125_000
    assert [reply.value for reply in result.context.quick_replies] == ["ya", "ubah", "batal"]


def test_confirmation_can_edit_building_and_recalculate_price() -> None:
    service, _ = build_service()
    created = service.create_conversation()
    for message in (
        "reservation",
        "borongan",
        "0123456789",
        "081234567890",
        "rumah",
        "Jalan Melati No. 10 Jakarta",
        "2 Agustus 2026",
        "09:00",
        "20 juta",
    ):
        service.process_message(created.context.conversation_id, message)

    edit_menu = service.process_message(created.context.conversation_id, "ubah")
    edit_field = service.process_message(
        created.context.conversation_id,
        "ubah:building_type",
    )
    updated = service.process_message(created.context.conversation_id, "ruko")

    assert edit_menu.context.state is ConversationState.EDIT_SLOT
    assert edit_field.context.state is ConversationState.BORONGAN_ASK_BUILDING
    assert "building_type" not in edit_field.context.collected_slots
    assert edit_field.context.reservation_summary is None
    assert updated.context.state is ConversationState.CONFIRM_RESERVATION
    assert updated.context.collected_slots["building_type"] == "ruko"
    assert updated.context.price_breakdown is not None
    assert updated.context.price_breakdown["estimated_price"] == 7_625_000


def test_yes_records_confirmation_without_creating_ticket_before_finalization() -> None:
    service, _ = build_service()
    created = service.create_conversation()
    for message in (
        "reservation",
        "borongan",
        "0123456789",
        "081234567890",
        "rumah",
        "Jalan Melati No. 10 Jakarta",
        "2 Agustus 2026",
        "09:00",
        "20 juta",
    ):
        service.process_message(created.context.conversation_id, message)

    confirmed = service.process_message(created.context.conversation_id, "ya")

    assert confirmed.context.state is ConversationState.CONFIRM_RESERVATION
    assert confirmed.context.reservation_confirmed is True
    assert confirmed.context.ticket is None
    assert "siap difinalisasi" in confirmed.new_messages[1].text


def test_cancel_from_confirmation_clears_summary_and_price() -> None:
    service, _ = build_service()
    created = service.create_conversation()
    for message in (
        "reservation",
        "borongan",
        "0123456789",
        "081234567890",
        "rumah",
        "Jalan Melati No. 10 Jakarta",
        "2 Agustus 2026",
        "09:00",
        "20 juta",
    ):
        service.process_message(created.context.conversation_id, message)

    cancelled = service.process_message(created.context.conversation_id, "batal")

    assert cancelled.context.state is ConversationState.CANCELLED
    assert cancelled.context.reservation_summary is None
    assert cancelled.context.price_breakdown is None
    assert cancelled.context.ticket is None


def test_ticket_status_flow_returns_lookup_result() -> None:
    ticket = TicketView(
        ticket_number="TKT-20260729-AB12CD",
        service_type=ServiceType.BORONGAN,
        status=TicketStatus.MENUNGGU_PEMBAYARAN,
        pricing_version="pricing-v1",
        estimated_price=5_125_000,
        budget=20_000_000,
        created_at=FIXED_NOW,
        email_delivery=EmailDelivery.NOT_IMPLEMENTED,
    )
    service, _ = build_service(ticket_lookup=StubTicketLookup(ticket))
    created = service.create_conversation()

    lookup_prompt = service.process_message(created.context.conversation_id, "status")
    result = service.process_message(
        created.context.conversation_id,
        "tkt-20260729-ab12cd",
    )

    assert lookup_prompt.context.state is ConversationState.TICKET_LOOKUP
    assert result.context.state is ConversationState.INFO_MODE
    assert result.context.ticket is not None
    assert result.context.ticket["status"] == "MENUNGGU_PEMBAYARAN"
    assert "TKT-20260729-AB12CD" in result.new_messages[1].text


def test_harian_turn_can_fill_worker_dates_and_session_at_once() -> None:
    service, _ = build_service()
    created = service.create_conversation()
    messages = (
        "reservation",
        "harian",
        "0123456789",
        "081234567890",
        "pipa",
        "Pipa dapur bocor sejak kemarin",
    )
    for message in messages:
        service.process_message(created.context.conversation_id, message)

    result = service.process_message(
        created.context.conversation_id,
        "dua tukang dari tanggal 2 sampai 3 Agustus 2026 sesi pagi",
    )

    assert result.context.state is ConversationState.HARIAN_ASK_PHOTO
    assert result.context.collected_slots["worker_count"] == 2
    assert result.context.collected_slots["start_date"] == "2026-08-02"
    assert result.context.collected_slots["end_date"] == "2026-08-03"
    assert result.context.collected_slots["work_session"] == "morning"


def test_every_processed_turn_emits_one_masked_log_event() -> None:
    turn_logger = CapturingTurnLogger()
    service, _ = build_service(turn_logger=turn_logger)
    created = service.create_conversation()
    conversation_id = created.context.conversation_id
    service.process_message(conversation_id, "reservation")
    service.process_message(conversation_id, "borongan")
    service.process_message(conversation_id, "0123456789")
    service.process_message(conversation_id, "nomor saya 0812 3456 7890")

    assert len(turn_logger.events) == 4
    event = turn_logger.events[-1]
    assert event.turn == 4
    assert event.state_before == "BORONGAN_ASK_PHONE"
    assert event.state_after == "BORONGAN_ASK_BUILDING"
    assert "0812 3456 7890" not in event.raw_text
    assert event.extracted_slots == {"phone_number": "+62812****7890"}


def test_invalid_slot_still_emits_event_without_overwriting_extracted_slots() -> None:
    turn_logger = CapturingTurnLogger()
    service, _ = build_service(turn_logger=turn_logger)
    created = service.create_conversation()
    conversation_id = created.context.conversation_id
    service.process_message(conversation_id, "reservation")
    service.process_message(conversation_id, "borongan")

    with pytest.raises(ApplicationError):
        service.process_message(conversation_id, "123")

    event = turn_logger.events[-1]
    assert event.state_before == "BORONGAN_ASK_CUSTOMER_ID"
    assert event.state_after == "BORONGAN_ASK_CUSTOMER_ID"
    assert event.extracted_slots == {}
    assert "0123456789" not in event.response_text

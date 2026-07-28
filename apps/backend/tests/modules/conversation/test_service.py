from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from app.modules.conversation.domain import ConversationState, MessageSender
from app.modules.conversation.faq import FALLBACK_TEXT, WELCOME_TEXT
from app.modules.conversation.repository import InMemoryConversationRepository
from app.modules.conversation.service import ConversationService
from app.modules.nlp.model import IntentPrediction
from app.modules.nlp.taxonomy import Intent
from app.shared.errors import ApplicationError

FIXED_NOW = datetime(2026, 7, 29, 9, 0, tzinfo=UTC)


class StubPredictor:
    def __init__(self, prediction: IntentPrediction) -> None:
        self.prediction = prediction
        self.received_texts: list[str] = []

    def predict(self, text: str, *, threshold: float | None = None) -> IntentPrediction:
        self.received_texts.append(text)
        return self.prediction


def id_factory() -> Iterator[str]:
    for index in range(1, 20):
        yield f"01K1A2B3C4D5E6F7G8H9J{index:04d}"


def build_service(
    *,
    predictor: StubPredictor | None = None,
) -> tuple[ConversationService, InMemoryConversationRepository]:
    identifiers = id_factory()
    repository = InMemoryConversationRepository()
    service = ConversationService(
        repository,
        predictor=predictor,
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

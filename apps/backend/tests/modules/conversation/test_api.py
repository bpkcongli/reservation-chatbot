from collections.abc import Iterator

import pytest
from app.main import app
from app.modules.conversation.api import (
    get_conversation_logger,
    get_conversation_repository,
    get_intent_predictor,
)
from app.modules.conversation.logger import NullConversationTurnLogger
from app.modules.conversation.repository import InMemoryConversationRepository
from app.modules.nlp.model import IntentPrediction
from app.modules.nlp.taxonomy import Intent
from httpx import ASGITransport, AsyncClient


class StubPredictor:
    def __init__(self, prediction: IntentPrediction) -> None:
        self.prediction = prediction

    def predict(self, text: str, *, threshold: float | None = None) -> IntentPrediction:
        return self.prediction


@pytest.fixture(autouse=True)
def conversation_dependencies() -> Iterator[InMemoryConversationRepository]:
    repository = InMemoryConversationRepository()
    predictor = StubPredictor(
        IntentPrediction(
            intent=Intent.BORONGAN_INFO,
            top_intent=Intent.BORONGAN_INFO,
            confidence=0.82,
            is_fallback=False,
        )
    )
    app.dependency_overrides.clear()

    async def override_repository() -> InMemoryConversationRepository:
        return repository

    async def override_predictor() -> StubPredictor:
        return predictor

    async def override_logger() -> NullConversationTurnLogger:
        return NullConversationTurnLogger()

    app.dependency_overrides[get_conversation_repository] = override_repository
    app.dependency_overrides[get_intent_predictor] = override_predictor
    app.dependency_overrides[get_conversation_logger] = override_logger
    yield repository
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_and_restore_conversation_contract() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post("/api/v1/conversations")
        conversation_id = create_response.json()["data"]["conversation_id"]
        get_response = await client.get(f"/api/v1/conversations/{conversation_id}")

    assert create_response.status_code == 201
    assert create_response.json()["status"] == {
        "code": 120100000,
        "message": "Created.",
        "errorDetails": [],
    }
    assert len(conversation_id) == 26
    assert create_response.json()["data"]["state"] == "WELCOME"
    assert [reply["value"] for reply in create_response.json()["data"]["quick_replies"]] == [
        "info",
        "reservation",
    ]
    assert create_response.json()["data"]["reservation_summary"] is None

    assert get_response.status_code == 200
    assert get_response.json()["data"]["conversation_id"] == conversation_id
    assert len(get_response.json()["data"]["messages"]) == 1


@pytest.mark.asyncio
async def test_message_response_contains_only_new_turn_but_get_restores_history() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post("/api/v1/conversations")
        conversation_id = create_response.json()["data"]["conversation_id"]
        message_response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"client_message_id": "web-message-001", "text": "info"},
        )
        get_response = await client.get(f"/api/v1/conversations/{conversation_id}")

    assert message_response.status_code == 200
    assert message_response.json()["data"]["state"] == "INFO_MODE"
    assert [message["sender"] for message in message_response.json()["data"]["messages"]] == [
        "user",
        "bot",
    ]
    assert len(get_response.json()["data"]["messages"]) == 3


@pytest.mark.asyncio
async def test_free_text_is_routed_through_intent_model() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post("/api/v1/conversations")
        conversation_id = create_response.json()["data"]["conversation_id"]
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={
                "client_message_id": "web-message-002",
                "text": "Bagaimana proses survei borongan?",
            },
        )

    assert response.status_code == 200
    assert response.json()["data"]["state"] == "INFO_MODE"
    assert "rumah, apartemen, atau ruko" in response.json()["data"]["messages"][1]["text"]


@pytest.mark.asyncio
async def test_low_confidence_response_has_fallback_state_and_topics() -> None:
    fallback_predictor = StubPredictor(
        IntentPrediction(
            intent=None,
            top_intent=Intent.SERVICE_OVERVIEW,
            confidence=0.13,
            is_fallback=True,
        )
    )

    async def override_fallback_predictor() -> StubPredictor:
        return fallback_predictor

    app.dependency_overrides[get_intent_predictor] = override_fallback_predictor

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post("/api/v1/conversations")
        conversation_id = create_response.json()["data"]["conversation_id"]
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"client_message_id": "web-message-003", "text": "Di luar topik"},
        )

    assert response.status_code == 200
    assert response.json()["data"]["state"] == "FALLBACK"
    assert "belum yakin memahami" in response.json()["data"]["messages"][1]["text"]
    assert [reply["value"] for reply in response.json()["data"]["quick_replies"]] == [
        "borongan",
        "harian",
        "harga",
        "reservation",
    ]


@pytest.mark.asyncio
async def test_unknown_conversation_returns_structured_not_found() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/conversations/01K1A2B3C4D5E6F7G8H9J0000")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"
    assert response.json()["error"]["message"] == (
        "Maaf, sesi percakapan tersebut belum ditemukan."
    )


@pytest.mark.asyncio
async def test_blank_message_is_rejected_without_advancing_history() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post("/api/v1/conversations")
        conversation_id = create_response.json()["data"]["conversation_id"]
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"client_message_id": "web-message-004", "text": "   "},
        )
        restored = await client.get(f"/api/v1/conversations/{conversation_id}")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_ERROR"
    assert len(restored.json()["data"]["messages"]) == 1


@pytest.mark.asyncio
async def test_invalid_reservation_slot_returns_feedback_and_preserves_state() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post("/api/v1/conversations")
        conversation_id = create_response.json()["data"]["conversation_id"]
        await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"client_message_id": "web-message-101", "text": "reservation"},
        )
        await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"client_message_id": "web-message-102", "text": "borongan"},
        )
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"client_message_id": "web-message-103", "text": "123"},
        )
        restored = await client.get(f"/api/v1/conversations/{conversation_id}")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_SLOT"
    assert response.json()["error"]["field"] == "customer_id"
    assert "0123456789" in response.json()["error"]["message"]
    assert restored.json()["data"]["state"] == "BORONGAN_ASK_CUSTOMER_ID"
    assert restored.json()["data"]["collected_slots"] == {"service_type": "borongan"}


@pytest.mark.asyncio
async def test_retried_client_message_id_returns_original_turn_without_duplicate_history() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post("/api/v1/conversations")
        conversation_id = create_response.json()["data"]["conversation_id"]
        payload = {"client_message_id": "web-message-301", "text": "reservation"}
        first = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json=payload,
        )
        retried = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json=payload,
        )
        restored = await client.get(f"/api/v1/conversations/{conversation_id}")

    assert first.status_code == 200
    assert retried.status_code == 200
    assert retried.json()["data"]["messages"] == first.json()["data"]["messages"]
    assert len(restored.json()["data"]["messages"]) == 3

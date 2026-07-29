"""API integration coverage for both transactional reservation flows."""

from collections.abc import AsyncIterator, Iterator
from datetime import datetime
from pathlib import Path

import pytest
from app.main import app
from app.modules.attachment.models import AttachmentRecord
from app.modules.catalog.models import ServiceRecord
from app.modules.conversation.api import (
    get_conversation_logger,
    get_intent_predictor,
)
from app.modules.conversation.logger import NullConversationTurnLogger
from app.modules.conversation.models import ReservationDraftRecord
from app.modules.nlp.model import IntentPrediction
from app.modules.nlp.taxonomy import Intent
from app.modules.reservation.models import ReservationRecord
from app.modules.ticketing.models import TicketRecord
from app.modules.ticketing.service import TicketNumberExhaustedError, TicketService
from app.shared.config import get_settings
from app.shared.database import Base, get_db_session
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\rIDAT\x08\xd7c\xf8\xcf\xc0\xf0\x1f\x00\x05\x00\x01"
    b"\x89\x99=\x1d\x00\x00\x00\x00IEND\xaeB`\x82"
)


class UnusedPredictor:
    def predict(self, text: str, *, threshold: float | None = None) -> IntentPrediction:
        return IntentPrediction(
            intent=Intent.START_RESERVATION,
            top_intent=Intent.START_RESERVATION,
            confidence=1.0,
            is_fallback=False,
        )


@pytest.fixture
def integration_app(
    sqlite_engine: Engine,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Engine]:
    with sqlite_engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(sqlite_engine)
    created_at = datetime(2026, 7, 29, 0, 0)
    with Session(sqlite_engine) as session:
        session.add_all(
            [
                ServiceRecord(
                    id=1,
                    code="borongan",
                    name="Jasa Borongan",
                    description="Borongan",
                    is_active=True,
                    created_at=created_at,
                    updated_at=created_at,
                ),
                ServiceRecord(
                    id=2,
                    code="harian",
                    name="Tukang Harian",
                    description="Harian",
                    is_active=True,
                    created_at=created_at,
                    updated_at=created_at,
                ),
            ]
        )
        session.commit()

    async def override_session() -> AsyncIterator[Session]:
        with Session(sqlite_engine, expire_on_commit=False) as session:
            yield session

    async def override_predictor() -> UnusedPredictor:
        return UnusedPredictor()

    async def override_logger() -> NullConversationTurnLogger:
        return NullConversationTurnLogger()

    app.dependency_overrides.clear()
    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_intent_predictor] = override_predictor
    app.dependency_overrides[get_conversation_logger] = override_logger
    monkeypatch.setattr(get_settings(), "upload_dir", tmp_path / "uploads")
    monkeypatch.setattr(get_settings(), "max_upload_mb", 1)
    yield sqlite_engine
    app.dependency_overrides.clear()
    Base.metadata.drop_all(sqlite_engine)


async def _create_conversation(client: AsyncClient) -> str:
    response = await client.post("/api/v1/conversations")
    assert response.status_code == 201
    return str(response.json()["data"]["conversation_id"])


async def _send(
    client: AsyncClient,
    conversation_id: str,
    sequence: int,
    text: str,
) -> object:
    return await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "client_message_id": f"integration-message-{sequence:03d}",
            "text": text,
        },
    )


@pytest.mark.asyncio
async def test_borongan_happy_path_creates_one_reservation_and_ticket_transactionally(
    integration_app: Engine,
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        conversation_id = await _create_conversation(client)
        messages = (
            "reservation",
            "borongan",
            "0123456789",
            "081234567890",
            "rumah",
            "Jalan Melati No. 10 Jakarta",
            "2 Agustus 2026",
            "09:00",
            "20 juta",
        )
        for sequence, message in enumerate(messages, start=1):
            response = await _send(client, conversation_id, sequence, message)
            assert response.status_code == 200

        confirmation = await _send(client, conversation_id, 10, "ya")
        retry = await _send(client, conversation_id, 10, "ya")
        ticket_number = confirmation.json()["data"]["ticket"]["ticket_number"]
        lookup = await client.get(f"/api/v1/tickets/{ticket_number}")

    assert confirmation.status_code == 200
    assert confirmation.json()["data"]["state"] == "TICKET_CREATED"
    assert confirmation.json()["data"]["ticket"]["service_type"] == "borongan"
    assert confirmation.json()["data"]["ticket"]["budget"] == 20_000_000
    assert retry.json()["data"]["messages"] == confirmation.json()["data"]["messages"]
    assert lookup.status_code == 200
    assert lookup.json()["data"]["ticket_number"] == ticket_number

    with Session(integration_app) as session:
        assert session.scalar(select(func.count()).select_from(ReservationRecord)) == 1
        assert session.scalar(select(func.count()).select_from(TicketRecord)) == 1


@pytest.mark.asyncio
async def test_harian_happy_path_links_safe_optional_photo_to_final_reservation(
    integration_app: Engine,
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        conversation_id = await _create_conversation(client)
        messages = (
            "reservation",
            "harian",
            "0123456789",
            "081234567890",
            "listrik",
            "Instalasi listrik sering turun mendadak",
            "2 orang",
            "2 Agustus 2026",
            "3 Agustus 2026",
            "pagi",
        )
        for sequence, message in enumerate(messages, start=1):
            response = await _send(client, conversation_id, sequence, message)
            assert response.status_code == 200
        assert response.json()["data"]["state"] == "HARIAN_ASK_PHOTO"

        upload = await client.post(
            f"/api/v1/conversations/{conversation_id}/attachments",
            files={"file": ("nama-asli.png", PNG_1X1, "image/png")},
        )
        restored = await client.get(f"/api/v1/conversations/{conversation_id}")
        address = await _send(
            client,
            conversation_id,
            11,
            "Jalan Mawar No. 20 Jakarta Selatan",
        )
        confirmation = await _send(client, conversation_id, 12, "ya")

    assert upload.status_code == 201
    attachment_data = upload.json()["data"]["attachment"]
    assert set(attachment_data) == {
        "attachment_id",
        "content_type",
        "size_bytes",
        "status",
    }
    assert restored.json()["data"]["state"] == "HARIAN_ASK_ADDRESS"
    assert address.json()["data"]["state"] == "CONFIRM_RESERVATION"
    assert address.json()["data"]["reservation_summary"]["attachment"] == attachment_data
    assert confirmation.json()["data"]["state"] == "TICKET_CREATED"
    assert confirmation.json()["data"]["ticket"]["service_type"] == "harian"
    assert confirmation.json()["data"]["ticket"]["budget"] is None

    with Session(integration_app) as session:
        reservation = session.scalar(select(ReservationRecord))
        attachment = session.scalar(select(AttachmentRecord))
        assert reservation is not None
        assert attachment is not None
        assert attachment.reservation_id == reservation.id
        assert attachment.stored_name != "nama-asli.png"
        stored_file = get_settings().upload_dir / attachment.stored_name
        assert stored_file.read_bytes() == PNG_1X1


@pytest.mark.asyncio
async def test_ticket_failure_rolls_back_reservation_and_keeps_confirmation_state(
    integration_app: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_ticket_issue(
        self: TicketService,
        reservation_id: str,
        *,
        created_at: datetime,
    ) -> object:
        raise TicketNumberExhaustedError

    monkeypatch.setattr(TicketService, "issue", fail_ticket_issue)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        conversation_id = await _create_conversation(client)
        messages = (
            "reservation",
            "borongan",
            "0123456789",
            "081234567890",
            "rumah",
            "Jalan Melati No. 10 Jakarta",
            "2 Agustus 2026",
            "09:00",
            "20 juta",
        )
        for sequence, message in enumerate(messages, start=1):
            assert (await _send(client, conversation_id, sequence, message)).status_code == 200
        confirmation = await _send(client, conversation_id, 10, "ya")
        restored = await client.get(f"/api/v1/conversations/{conversation_id}")

    assert confirmation.status_code == 503
    assert confirmation.json()["error"]["code"] == "TICKET_NUMBER_UNAVAILABLE"
    assert restored.json()["data"]["state"] == "CONFIRM_RESERVATION"
    with Session(integration_app) as session:
        draft = session.scalar(select(ReservationDraftRecord))
        assert draft is not None
        assert draft.status == "ACTIVE"
        assert session.scalar(select(func.count()).select_from(ReservationRecord)) == 0
        assert session.scalar(select(func.count()).select_from(TicketRecord)) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("service_type", ["borongan", "harian"])
async def test_invalid_slot_and_cancellation_create_no_transaction_records(
    integration_app: Engine,
    service_type: str,
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        conversation_id = await _create_conversation(client)
        assert (await _send(client, conversation_id, 1, "reservation")).status_code == 200
        assert (await _send(client, conversation_id, 2, service_type)).status_code == 200
        invalid = await _send(client, conversation_id, 3, "123")
        cancelled = await _send(client, conversation_id, 4, "batal")

    assert invalid.status_code == 422
    assert invalid.json()["error"]["field"] == "customer_id"
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["state"] == "CANCELLED"
    assert cancelled.json()["data"]["ticket"] is None
    with Session(integration_app) as session:
        assert session.scalar(select(func.count()).select_from(ReservationRecord)) == 0
        assert session.scalar(select(func.count()).select_from(TicketRecord)) == 0


@pytest.mark.asyncio
async def test_upload_rejects_spoofed_photo_without_advancing_draft(
    integration_app: Engine,
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        conversation_id = await _create_conversation(client)
        messages = (
            "reservation",
            "harian",
            "0123456789",
            "081234567890",
            "pipa",
            "Pipa dapur bocor sejak tadi malam",
            "1 orang",
            "2 Agustus 2026",
            "2 Agustus 2026",
            "sehari penuh",
        )
        for sequence, message in enumerate(messages, start=1):
            assert (await _send(client, conversation_id, sequence, message)).status_code == 200

        upload = await client.post(
            f"/api/v1/conversations/{conversation_id}/attachments",
            files={"file": ("foto.jpg", PNG_1X1, "image/jpeg")},
        )
        restored = await client.get(f"/api/v1/conversations/{conversation_id}")

    assert upload.status_code == 415
    assert upload.json()["error"]["code"] == "UNSUPPORTED_ATTACHMENT_TYPE"
    assert restored.json()["data"]["state"] == "HARIAN_ASK_PHOTO"
    with Session(integration_app) as session:
        assert session.scalar(select(func.count()).select_from(AttachmentRecord)) == 0

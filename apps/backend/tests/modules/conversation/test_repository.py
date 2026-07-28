from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from app.modules.conversation.domain import ConversationState
from app.modules.conversation.models import ReservationDraftRecord
from app.modules.conversation.repository import SqlAlchemyConversationRepository
from app.modules.conversation.service import ConversationService
from app.shared.database import Base
from app.shared.errors import ApplicationError
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

FIXED_NOW = datetime(2026, 7, 29, 9, 0, tzinfo=UTC)


def id_factory() -> Iterator[str]:
    for index in range(1, 50):
        yield f"01K1A2B3C4D5E6F7G8H9J{index:04d}"


def test_sqlalchemy_repository_restores_state_history_and_draft(
    sqlite_engine: Engine,
) -> None:
    with sqlite_engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(sqlite_engine)
    identifiers = id_factory()

    with Session(sqlite_engine, expire_on_commit=False) as first_session:
        service = ConversationService(
            SqlAlchemyConversationRepository(first_session),
            clock=lambda: FIXED_NOW,
            id_factory=lambda _: next(identifiers),
        )
        created = service.create_conversation()
        conversation_id = created.context.conversation_id
        service.process_message(
            conversation_id,
            "reservation",
            client_message_id="web-message-201",
        )
        service.process_message(
            conversation_id,
            "borongan",
            client_message_id="web-message-202",
        )
        service.process_message(
            conversation_id,
            "0123456789",
            client_message_id="web-message-203",
        )
        with pytest.raises(ApplicationError):
            service.process_message(
                conversation_id,
                "123",
                client_message_id="web-message-204",
            )

    with Session(sqlite_engine, expire_on_commit=False) as restored_session:
        restored = SqlAlchemyConversationRepository(restored_session).get(conversation_id)

        assert restored is not None
        assert restored.state is ConversationState.BORONGAN_ASK_PHONE
        assert restored.collected_slots == {
            "service_type": "borongan",
            "customer_id": "0123456789",
        }
        assert len(restored.messages) == 9
        assert restored.messages[-4].client_message_id == "web-message-203"
        assert restored.messages[-2].client_message_id == "web-message-204"
        draft = restored_session.scalar(
            select(ReservationDraftRecord).where(
                ReservationDraftRecord.conversation_id == conversation_id
            )
        )
        assert draft is not None
        assert draft.status == "ACTIVE"

    Base.metadata.drop_all(sqlite_engine)


def test_cancelled_draft_is_restored_empty_and_marked_cancelled(
    sqlite_engine: Engine,
) -> None:
    with sqlite_engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(sqlite_engine)
    identifiers = id_factory()

    with Session(sqlite_engine, expire_on_commit=False) as session:
        repository = SqlAlchemyConversationRepository(session)
        service = ConversationService(
            repository,
            clock=lambda: FIXED_NOW,
            id_factory=lambda _: next(identifiers),
        )
        created = service.create_conversation()
        conversation_id = created.context.conversation_id
        service.process_message(conversation_id, "reservation")
        service.process_message(conversation_id, "harian")
        service.process_message(conversation_id, "0123456789")
        service.process_message(conversation_id, "batal")

    with Session(sqlite_engine, expire_on_commit=False) as restored_session:
        restored = SqlAlchemyConversationRepository(restored_session).get(conversation_id)
        draft = restored_session.scalar(
            select(ReservationDraftRecord).where(
                ReservationDraftRecord.conversation_id == conversation_id
            )
        )

        assert restored is not None
        assert restored.state is ConversationState.CANCELLED
        assert restored.collected_slots == {}
        assert draft is not None
        assert draft.status == "CANCELLED"
        assert draft.slots == {}

    Base.metadata.drop_all(sqlite_engine)

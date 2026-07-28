from datetime import datetime

from app.modules.catalog.models import ServiceRecord
from app.modules.conversation.models import (
    ConversationRecord,
    ReservationDraftRecord,
)
from app.modules.reservation.models import ReservationRecord
from app.modules.ticketing.models import TicketRecord
from app.modules.ticketing.repository import SqlAlchemyTicketRepository
from app.shared.database import Base
from sqlalchemy import Engine
from sqlalchemy.orm import Session


def test_sql_repository_joins_ticket_to_safe_reservation_snapshot(
    sqlite_engine: Engine,
) -> None:
    Base.metadata.create_all(sqlite_engine)
    created_at = datetime(2026, 7, 29, 9, 0)
    conversation_id = "01K1A2B3C4D5E6F7G8H9J0K1M2"
    reservation_id = "01K1A2B3C4D5E6F7G8H9J0K1M3"
    with Session(sqlite_engine) as session:
        session.add(
            ServiceRecord(
                id=1,
                code="borongan",
                name="Jasa Borongan",
                description="Borongan",
                is_active=True,
                created_at=created_at,
                updated_at=created_at,
            )
        )
        session.add(
            ConversationRecord(
                id=conversation_id,
                locale="id-ID",
                state="TICKET_CREATED",
                context={},
                created_at=created_at,
                updated_at=created_at,
            )
        )
        session.add(
            ReservationDraftRecord(
                id=conversation_id,
                conversation_id=conversation_id,
                service_type="borongan",
                status="CONFIRMED",
                slots={},
                price_snapshot=None,
                created_at=created_at,
                updated_at=created_at,
            )
        )
        session.add(
            ReservationRecord(
                id=reservation_id,
                reservation_draft_id=conversation_id,
                service_id=1,
                customer_id="0123456789",
                phone_number_encrypted="<ciphertext>",
                details={
                    "service_type": "borongan",
                    "pricing_version": "pricing-v1",
                    "budget": 20_000_000,
                },
                estimated_price=5_125_000,
                created_at=created_at,
            )
        )
        session.add(
            TicketRecord(
                id="01K1A2B3C4D5E6F7G8H9J0K1M4",
                reservation_id=reservation_id,
                ticket_number="TKT-20260729-AB12CD",
                status="MENUNGGU_PEMBAYARAN",
                created_at=created_at,
            )
        )
        session.commit()

        ticket = SqlAlchemyTicketRepository(session).find_by_number("TKT-20260729-AB12CD")

    assert ticket is not None
    assert ticket.service_type == "borongan"
    assert ticket.estimated_price == 5_125_000
    assert ticket.budget == 20_000_000
    assert ticket.email_delivery == "NOT_IMPLEMENTED"
    Base.metadata.drop_all(sqlite_engine)

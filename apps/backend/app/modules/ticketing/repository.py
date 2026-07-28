"""Ticket persistence boundary and implementations."""

from copy import deepcopy
from datetime import UTC
from threading import RLock
from typing import Literal, Protocol, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalog.domain import ServiceType
from app.modules.catalog.models import ServiceRecord
from app.modules.reservation.models import ReservationRecord
from app.modules.ticketing.domain import EmailDelivery, Ticket, TicketStatus, TicketView
from app.modules.ticketing.models import TicketRecord


class TicketRepository(Protocol):
    def exists(self, ticket_number: str) -> bool:
        """Check uniqueness before attempting an insert."""

    def add(self, ticket: Ticket) -> None:
        """Persist a new ticket."""

    def find_by_number(self, ticket_number: str) -> TicketView | None:
        """Return a PII-safe view for lookup."""


class InMemoryTicketRepository:
    def __init__(self) -> None:
        self._tickets: dict[str, TicketView] = {}
        self._issued: dict[str, Ticket] = {}
        self._lock = RLock()

    def exists(self, ticket_number: str) -> bool:
        with self._lock:
            return ticket_number in self._tickets or ticket_number in self._issued

    def add(self, ticket: Ticket) -> None:
        with self._lock:
            if self.exists(ticket.ticket_number):
                raise ValueError("Ticket number already exists.")
            self._issued[ticket.ticket_number] = deepcopy(ticket)

    def add_view(self, ticket: TicketView) -> None:
        with self._lock:
            if ticket.ticket_number in self._tickets:
                raise ValueError("Ticket number already exists.")
            self._tickets[ticket.ticket_number] = deepcopy(ticket)

    def find_by_number(self, ticket_number: str) -> TicketView | None:
        with self._lock:
            ticket = self._tickets.get(ticket_number)
            return deepcopy(ticket) if ticket is not None else None


class SqlAlchemyTicketRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def exists(self, ticket_number: str) -> bool:
        return (
            self._session.scalar(
                select(TicketRecord.id).where(TicketRecord.ticket_number == ticket_number)
            )
            is not None
        )

    def add(self, ticket: Ticket) -> None:
        self._session.add(
            TicketRecord(
                id=ticket.id,
                reservation_id=ticket.reservation_id,
                ticket_number=ticket.ticket_number,
                status=ticket.status.value,
                created_at=ticket.created_at.astimezone(UTC).replace(tzinfo=None),
            )
        )

    def find_by_number(self, ticket_number: str) -> TicketView | None:
        row = self._session.execute(
            select(TicketRecord, ReservationRecord, ServiceRecord)
            .join(ReservationRecord, ReservationRecord.id == TicketRecord.reservation_id)
            .join(ServiceRecord, ServiceRecord.id == ReservationRecord.service_id)
            .where(TicketRecord.ticket_number == ticket_number)
        ).one_or_none()
        if row is None:
            return None

        ticket, reservation, service = row
        details = cast(dict[str, object], reservation.details)
        raw_budget = details.get("budget")
        raw_pricing_version = details.get("pricing_version")
        if not isinstance(raw_pricing_version, str):
            raise ValueError("Reservation details are missing ticket lookup metadata.")
        if raw_pricing_version != "pricing-v1":
            raise ValueError("Unsupported reservation pricing version.")
        if raw_budget is not None and (
            isinstance(raw_budget, bool) or not isinstance(raw_budget, int)
        ):
            raise ValueError("Reservation budget must be an integer or null.")
        return TicketView(
            ticket_number=ticket.ticket_number,
            service_type=ServiceType(service.code),
            status=TicketStatus(ticket.status),
            pricing_version=cast(Literal["pricing-v1"], raw_pricing_version),
            estimated_price=reservation.estimated_price,
            budget=raw_budget,
            created_at=ticket.created_at.replace(tzinfo=UTC),
            email_delivery=EmailDelivery.NOT_IMPLEMENTED,
        )

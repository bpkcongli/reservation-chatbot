"""Ticket issuance and lookup application service."""

from collections.abc import Callable
from datetime import datetime

from fastapi import status

from app.modules.conversation.ids import generate_ulid
from app.modules.ticketing.domain import (
    SuffixFactory,
    Ticket,
    TicketStatus,
    TicketView,
    generate_ticket_number,
    random_ticket_suffix,
)
from app.modules.ticketing.repository import TicketRepository
from app.shared.errors import ApplicationError

IdFactory = Callable[[datetime], str]


class TicketNumberExhaustedError(RuntimeError):
    """Raised when all generated candidates collide."""


class TicketService:
    def __init__(
        self,
        repository: TicketRepository,
        *,
        id_factory: IdFactory = generate_ulid,
        suffix_factory: SuffixFactory = random_ticket_suffix,
        max_generation_attempts: int = 10,
    ) -> None:
        self._repository = repository
        self._id_factory = id_factory
        self._suffix_factory = suffix_factory
        self._max_generation_attempts = max_generation_attempts

    def issue(self, reservation_id: str, *, created_at: datetime) -> Ticket:
        for _ in range(self._max_generation_attempts):
            ticket_number = generate_ticket_number(
                created_at,
                suffix_factory=self._suffix_factory,
            )
            if self._repository.exists(ticket_number):
                continue
            ticket = Ticket(
                id=self._id_factory(created_at),
                reservation_id=reservation_id,
                ticket_number=ticket_number,
                status=TicketStatus.MENUNGGU_PEMBAYARAN,
                created_at=created_at,
            )
            self._repository.add(ticket)
            return ticket
        raise TicketNumberExhaustedError("Unable to generate a unique ticket number.")

    def get(self, ticket_number: str) -> TicketView:
        ticket = self._repository.find_by_number(ticket_number)
        if ticket is None:
            raise ApplicationError(
                code="TICKET_NOT_FOUND",
                message="Maaf, tiket dengan nomor tersebut belum ditemukan.",
                status_code=status.HTTP_404_NOT_FOUND,
                field="ticket_number",
            )
        return ticket

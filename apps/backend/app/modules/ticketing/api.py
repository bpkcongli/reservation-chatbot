"""Ticket lookup endpoint."""

from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.modules.ticketing.repository import SqlAlchemyTicketRepository, TicketRepository
from app.modules.ticketing.schemas import TicketData, TicketResponse
from app.modules.ticketing.service import TicketService
from app.shared.config import get_settings
from app.shared.database import get_db_session

router = APIRouter(prefix="/tickets", tags=["tickets"])


async def get_ticket_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> TicketRepository:
    return SqlAlchemyTicketRepository(session)


@router.get("/{ticket_number}", response_model=TicketResponse)
async def get_ticket(
    ticket_number: Annotated[str, Path(pattern=r"^TKT-[0-9]{8}-[A-Z0-9]{6}$")],
    repository: Annotated[TicketRepository, Depends(get_ticket_repository)],
) -> TicketResponse:
    ticket = TicketService(repository).get(ticket_number)
    return TicketResponse(
        data=TicketData(
            ticket_number=ticket.ticket_number,
            service_type=ticket.service_type,
            status=ticket.status,
            pricing_version=ticket.pricing_version,
            estimated_price=ticket.estimated_price,
            budget=ticket.budget,
            created_at=ticket.created_at.astimezone(ZoneInfo(get_settings().app_timezone)),
            email_delivery=ticket.email_delivery,
        )
    )

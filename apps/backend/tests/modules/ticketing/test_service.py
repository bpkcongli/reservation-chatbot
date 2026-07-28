from datetime import UTC, datetime

import pytest
from app.modules.catalog.domain import ServiceType
from app.modules.ticketing.domain import (
    EmailDelivery,
    TicketStatus,
    TicketView,
    generate_ticket_number,
)
from app.modules.ticketing.repository import InMemoryTicketRepository
from app.modules.ticketing.service import TicketService
from app.shared.errors import ApplicationError

CREATED_AT = datetime(2026, 7, 29, 9, 0, tzinfo=UTC)


def ticket_view(ticket_number: str) -> TicketView:
    return TicketView(
        ticket_number=ticket_number,
        service_type=ServiceType.BORONGAN,
        status=TicketStatus.MENUNGGU_PEMBAYARAN,
        pricing_version="pricing-v1",
        estimated_price=5_125_000,
        budget=20_000_000,
        created_at=CREATED_AT,
        email_delivery=EmailDelivery.NOT_IMPLEMENTED,
    )


def test_ticket_number_uses_required_date_and_suffix_format() -> None:
    assert (
        generate_ticket_number(
            CREATED_AT,
            suffix_factory=lambda: "ab12cd",
        )
        == "TKT-20260729-AB12CD"
    )

    with pytest.raises(ValueError):
        generate_ticket_number(CREATED_AT, suffix_factory=lambda: "ABC")


def test_ticket_service_retries_collision_and_sets_initial_status() -> None:
    repository = InMemoryTicketRepository()
    repository.add_view(ticket_view("TKT-20260729-AB12CD"))
    suffixes = iter(("AB12CD", "ZX90QW"))
    service = TicketService(
        repository,
        id_factory=lambda _: "01K1A2B3C4D5E6F7G8H9J0K1M2",
        suffix_factory=lambda: next(suffixes),
    )

    issued = service.issue(
        "01K1A2B3C4D5E6F7G8H9J0K1M3",
        created_at=CREATED_AT,
    )

    assert issued.ticket_number == "TKT-20260729-ZX90QW"
    assert issued.status is TicketStatus.MENUNGGU_PEMBAYARAN
    assert repository.exists(issued.ticket_number)


def test_ticket_lookup_returns_safe_view_or_not_found() -> None:
    repository = InMemoryTicketRepository()
    expected = ticket_view("TKT-20260729-AB12CD")
    repository.add_view(expected)
    service = TicketService(repository)

    assert service.get(expected.ticket_number) == expected
    with pytest.raises(ApplicationError) as error:
        service.get("TKT-20260729-ZZZZZZ")
    assert error.value.status_code == 404
    assert error.value.detail.code == "TICKET_NOT_FOUND"

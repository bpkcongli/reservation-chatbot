from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from app.main import app
from app.modules.catalog.domain import ServiceType
from app.modules.ticketing.api import get_ticket_repository
from app.modules.ticketing.domain import EmailDelivery, TicketStatus, TicketView
from app.modules.ticketing.repository import InMemoryTicketRepository
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def ticket_dependency() -> Iterator[None]:
    repository = InMemoryTicketRepository()
    repository.add_view(
        TicketView(
            ticket_number="TKT-20260729-AB12CD",
            service_type=ServiceType.BORONGAN,
            status=TicketStatus.MENUNGGU_PEMBAYARAN,
            pricing_version="pricing-v1",
            estimated_price=5_125_000,
            budget=20_000_000,
            created_at=datetime(2026, 7, 29, 9, 0, tzinfo=UTC),
            email_delivery=EmailDelivery.NOT_IMPLEMENTED,
        )
    )
    app.dependency_overrides[get_ticket_repository] = lambda: repository
    yield
    app.dependency_overrides.pop(get_ticket_repository, None)


@pytest.mark.asyncio
async def test_ticket_endpoint_returns_safe_contract() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/tickets/TKT-20260729-AB12CD")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "ticket_number": "TKT-20260729-AB12CD",
        "service_type": "borongan",
        "status": "MENUNGGU_PEMBAYARAN",
        "pricing_version": "pricing-v1",
        "estimated_price": 5_125_000,
        "budget": 20_000_000,
        "created_at": "2026-07-29T16:00:00+07:00",
        "email_delivery": "NOT_IMPLEMENTED",
    }


@pytest.mark.asyncio
async def test_ticket_endpoint_distinguishes_invalid_and_unknown_number() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        invalid = await client.get("/api/v1/tickets/not-a-ticket")
        unknown = await client.get("/api/v1/tickets/TKT-20260729-ZZZZZZ")

    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "REQUEST_VALIDATION_ERROR"
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "TICKET_NOT_FOUND"

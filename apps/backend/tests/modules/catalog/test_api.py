from collections.abc import Iterator
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from app.main import app
from app.modules.catalog.api import get_catalog_repository
from app.modules.catalog.domain import SERVICE_SEEDS, ServiceCatalogItem
from httpx import ASGITransport, AsyncClient


class StubCatalogRepository:
    def list_active_services(self) -> tuple[ServiceCatalogItem, ...]:
        return SERVICE_SEEDS


@pytest.fixture(autouse=True)
def catalog_dependency() -> Iterator[None]:
    async def override_repository() -> StubCatalogRepository:
        return StubCatalogRepository()

    app.dependency_overrides[get_catalog_repository] = override_repository
    yield
    app.dependency_overrides.pop(get_catalog_repository, None)


@pytest.mark.asyncio
async def test_services_endpoint_returns_seeded_contract() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/catalog/services")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["pricing_version"] == "pricing-v1"
    assert [service["value"] for service in payload["data"]["services"]] == [
        "borongan",
        "harian",
    ]
    assert [option["value"] for option in payload["data"]["services"][1]["specializations"]] == [
        "cat",
        "genteng",
        "ac",
        "listrik",
        "keramik",
        "pipa",
    ]


@pytest.mark.asyncio
async def test_survey_slots_endpoint_returns_two_slots_for_one_day() -> None:
    today = datetime.now(ZoneInfo("Asia/Jakarta")).date()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/catalog/survey-slots",
            params={"date_from": today.isoformat(), "date_to": today.isoformat()},
        )

    assert response.status_code == 200
    assert [slot["time"] for slot in response.json()["data"]["slots"]] == [
        "09:00",
        "13:00",
    ]

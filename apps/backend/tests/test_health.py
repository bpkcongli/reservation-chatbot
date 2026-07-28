import pytest
from app.main import app
from app.shared.health import get_engine
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Engine, create_engine


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> None:
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health(sqlite_engine: Engine) -> None:
    async def override_engine() -> Engine:
        return sqlite_engine

    app.dependency_overrides[get_engine] = override_engine

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_ready_checks_database(sqlite_engine: Engine) -> None:
    async def override_engine() -> Engine:
        return sqlite_engine

    app.dependency_overrides[get_engine] = override_engine

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"database": "ok"}}


@pytest.mark.asyncio
async def test_ready_returns_structured_error_when_database_is_unavailable() -> None:
    unavailable_engine = create_engine(
        "sqlite+pysqlite:////nonexistent-reservation-chatbot/readiness.sqlite"
    )

    async def override_engine() -> Engine:
        return unavailable_engine

    app.dependency_overrides[get_engine] = override_engine

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/ready")

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "SERVICE_NOT_READY",
            "message": "Database belum siap.",
            "field": None,
            "retryable": True,
        }
    }


@pytest.mark.asyncio
async def test_not_found_uses_error_envelope() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Resource tidak ditemukan.",
            "field": None,
            "retryable": False,
        }
    }

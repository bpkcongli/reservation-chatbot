from typing import Annotated, Literal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.shared.database import engine
from app.shared.errors import ApplicationError

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadinessChecks(BaseModel):
    database: Literal["ok"]


class ReadinessResponse(BaseModel):
    status: Literal["ready"]
    checks: ReadinessChecks


async def get_engine() -> Engine:
    return engine


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Dependency unavailable"}},
)
async def ready(
    database_engine: Annotated[Engine, Depends(get_engine)],
) -> ReadinessResponse:
    try:
        with database_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise ApplicationError(
            code="SERVICE_NOT_READY",
            message="Database belum siap.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            retryable=True,
        ) from exc

    return ReadinessResponse(status="ready", checks=ReadinessChecks(database="ok"))

"""FastAPI endpoints for services and deterministic survey slots."""

from datetime import date, datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.modules.catalog.domain import SurveyAvailabilityError
from app.modules.catalog.repository import CatalogRepository, SqlAlchemyCatalogRepository
from app.modules.catalog.schemas import (
    CatalogOptionData,
    ServiceCatalogData,
    ServiceCatalogItemData,
    ServiceCatalogResponse,
    SurveyAvailabilityData,
    SurveySlotData,
    SurveySlotResponse,
)
from app.modules.catalog.service import CatalogService
from app.shared.config import get_settings
from app.shared.database import get_db_session
from app.shared.errors import ApplicationError

router = APIRouter(prefix="/catalog", tags=["catalog"])


async def get_catalog_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> CatalogRepository:
    return SqlAlchemyCatalogRepository(session)


@router.get("/services", response_model=ServiceCatalogResponse)
async def list_services(
    repository: Annotated[CatalogRepository, Depends(get_catalog_repository)],
) -> ServiceCatalogResponse:
    services = CatalogService(repository).list_services()
    return ServiceCatalogResponse(
        data=ServiceCatalogData(
            services=[
                ServiceCatalogItemData(
                    value=service.value,
                    label=service.label,
                    description=service.description,
                    specializations=[
                        CatalogOptionData(value=option.value, label=option.label)
                        for option in service.specializations
                    ],
                    work_sessions=[
                        CatalogOptionData(value=option.value, label=option.label)
                        for option in service.work_sessions
                    ],
                )
                for service in services
            ]
        )
    )


@router.get("/survey-slots", response_model=SurveySlotResponse)
async def list_survey_slots(
    repository: Annotated[CatalogRepository, Depends(get_catalog_repository)],
    date_from: Annotated[date, Query()],
    date_to: Annotated[date, Query()],
) -> SurveySlotResponse:
    timezone = ZoneInfo(get_settings().app_timezone)
    today = datetime.now(timezone).date()
    try:
        slots = CatalogService(repository).list_survey_slots(
            date_from,
            date_to,
            today=today,
        )
    except SurveyAvailabilityError as error:
        raise ApplicationError(
            code="INVALID_SURVEY_RANGE",
            message=str(error),
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            field=error.field,
        ) from error
    return SurveySlotResponse(
        data=SurveyAvailabilityData(
            slots=[
                SurveySlotData(date=slot.date, time=slot.time, available=slot.available)
                for slot in slots
            ]
        )
    )

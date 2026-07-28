"""Application service for catalog queries."""

from datetime import date

from app.modules.catalog.domain import ServiceCatalogItem, SurveySlot, list_survey_availability
from app.modules.catalog.repository import CatalogRepository


class CatalogService:
    def __init__(self, repository: CatalogRepository) -> None:
        self._repository = repository

    def list_services(self) -> tuple[ServiceCatalogItem, ...]:
        return self._repository.list_active_services()

    def list_survey_slots(
        self,
        date_from: date,
        date_to: date,
        *,
        today: date,
    ) -> tuple[SurveySlot, ...]:
        return list_survey_availability(date_from, date_to, today=today)

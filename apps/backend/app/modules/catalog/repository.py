"""Catalog persistence boundary."""

from collections import defaultdict
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalog.domain import (
    CatalogOption,
    ServiceCatalogItem,
    ServiceType,
)
from app.modules.catalog.models import (
    ServiceRecord,
    SpecializationRecord,
    WorkSessionRecord,
)


class CatalogRepository(Protocol):
    def list_active_services(self) -> tuple[ServiceCatalogItem, ...]:
        """Return active services and their active child options."""


class SqlAlchemyCatalogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_active_services(self) -> tuple[ServiceCatalogItem, ...]:
        services = tuple(
            self._session.scalars(
                select(ServiceRecord)
                .where(ServiceRecord.is_active.is_(True))
                .order_by(ServiceRecord.id)
            )
        )
        if not services:
            return ()

        service_ids = [service.id for service in services]
        specialization_rows = self._session.scalars(
            select(SpecializationRecord)
            .where(
                SpecializationRecord.service_id.in_(service_ids),
                SpecializationRecord.is_active.is_(True),
            )
            .order_by(SpecializationRecord.id)
        )
        work_session_rows = self._session.scalars(
            select(WorkSessionRecord)
            .where(
                WorkSessionRecord.service_id.in_(service_ids),
                WorkSessionRecord.is_active.is_(True),
            )
            .order_by(WorkSessionRecord.id)
        )

        specializations: dict[int, list[CatalogOption]] = defaultdict(list)
        for specialization_row in specialization_rows:
            specializations[specialization_row.service_id].append(
                CatalogOption(specialization_row.code, specialization_row.name)
            )
        work_sessions: dict[int, list[CatalogOption]] = defaultdict(list)
        for work_session_row in work_session_rows:
            work_sessions[work_session_row.service_id].append(
                CatalogOption(work_session_row.code, work_session_row.name)
            )

        return tuple(
            ServiceCatalogItem(
                value=ServiceType(service.code),
                label=service.name,
                description=service.description,
                specializations=tuple(specializations[service.id]),
                work_sessions=tuple(work_sessions[service.id]),
            )
            for service in services
        )

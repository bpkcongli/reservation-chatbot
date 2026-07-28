from datetime import datetime

from app.modules.catalog.models import (
    ServiceRecord,
    SpecializationRecord,
    WorkSessionRecord,
)
from app.modules.catalog.repository import SqlAlchemyCatalogRepository
from app.shared.database import Base
from sqlalchemy import Engine
from sqlalchemy.orm import Session


def test_repository_returns_only_active_catalog_items(sqlite_engine: Engine) -> None:
    Base.metadata.create_all(sqlite_engine)
    seeded_at = datetime(2026, 7, 29, 12, 0)
    with Session(sqlite_engine) as session:
        session.add_all(
            [
                ServiceRecord(
                    id=1,
                    code="borongan",
                    name="Jasa Borongan",
                    description="Borongan",
                    is_active=True,
                    created_at=seeded_at,
                    updated_at=seeded_at,
                ),
                ServiceRecord(
                    id=2,
                    code="harian",
                    name="Tukang Harian",
                    description="Harian",
                    is_active=True,
                    created_at=seeded_at,
                    updated_at=seeded_at,
                ),
                SpecializationRecord(
                    id=1,
                    service_id=2,
                    code="cat",
                    name="Spesialis Cat",
                    is_active=True,
                    created_at=seeded_at,
                    updated_at=seeded_at,
                ),
                SpecializationRecord(
                    id=2,
                    service_id=2,
                    code="pipa",
                    name="Spesialis Pipa",
                    is_active=False,
                    created_at=seeded_at,
                    updated_at=seeded_at,
                ),
                WorkSessionRecord(
                    id=1,
                    service_id=2,
                    code="full_day",
                    name="Sehari penuh",
                    is_active=True,
                    created_at=seeded_at,
                    updated_at=seeded_at,
                ),
            ]
        )
        session.commit()

        services = SqlAlchemyCatalogRepository(session).list_active_services()

    assert [service.value for service in services] == ["borongan", "harian"]
    assert services[0].specializations == ()
    assert [option.value for option in services[1].specializations] == ["cat"]
    assert [option.value for option in services[1].work_sessions] == ["full_day"]
    Base.metadata.drop_all(sqlite_engine)

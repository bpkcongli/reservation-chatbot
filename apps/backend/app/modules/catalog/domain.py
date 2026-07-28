"""Canonical catalog values and deterministic survey availability."""

from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum


class ServiceType(StrEnum):
    BORONGAN = "borongan"
    HARIAN = "harian"


class Specialization(StrEnum):
    CAT = "cat"
    GENTENG = "genteng"
    AC = "ac"
    LISTRIK = "listrik"
    KERAMIK = "keramik"
    PIPA = "pipa"


class WorkSession(StrEnum):
    FULL_DAY = "full_day"
    MORNING = "morning"
    AFTERNOON = "afternoon"


class BuildingType(StrEnum):
    RUMAH = "rumah"
    APARTEMEN = "apartemen"
    RUKO = "ruko"


@dataclass(frozen=True, slots=True)
class CatalogOption:
    value: str
    label: str


@dataclass(frozen=True, slots=True)
class ServiceCatalogItem:
    value: ServiceType
    label: str
    description: str
    specializations: tuple[CatalogOption, ...] = ()
    work_sessions: tuple[CatalogOption, ...] = ()


@dataclass(frozen=True, slots=True)
class SurveySlot:
    date: date
    time: str
    available: bool = True


SPECIALIZATION_OPTIONS = (
    CatalogOption(Specialization.CAT, "Spesialis Cat"),
    CatalogOption(Specialization.GENTENG, "Spesialis Genteng"),
    CatalogOption(Specialization.AC, "Spesialis AC"),
    CatalogOption(Specialization.LISTRIK, "Spesialis Listrik"),
    CatalogOption(Specialization.KERAMIK, "Spesialis Keramik"),
    CatalogOption(Specialization.PIPA, "Spesialis Pipa"),
)

WORK_SESSION_OPTIONS = (
    CatalogOption(WorkSession.FULL_DAY, "Sehari penuh"),
    CatalogOption(WorkSession.MORNING, "Pagi"),
    CatalogOption(WorkSession.AFTERNOON, "Siang"),
)

SERVICE_SEEDS = (
    ServiceCatalogItem(
        value=ServiceType.BORONGAN,
        label="Jasa Borongan",
        description="Permintaan pekerjaan berdasarkan survei dan budget.",
    ),
    ServiceCatalogItem(
        value=ServiceType.HARIAN,
        label="Tukang Harian",
        description="Tukang berdasarkan spesialisasi, durasi, dan sesi.",
        specializations=SPECIALIZATION_OPTIONS,
        work_sessions=WORK_SESSION_OPTIONS,
    ),
)

SURVEY_TIMES = ("09:00", "13:00")
SURVEY_MAX_RANGE_DAYS = 31


class SurveyAvailabilityError(ValueError):
    """Invalid date range or survey time."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field


def list_survey_availability(
    date_from: date,
    date_to: date,
    *,
    today: date,
) -> tuple[SurveySlot, ...]:
    """Generate fixed demo slots for an inclusive date range."""

    if date_from < today:
        raise SurveyAvailabilityError(
            "date_from",
            "Tanggal awal pencarian tidak boleh berada di masa lalu.",
        )
    if date_to < date_from:
        raise SurveyAvailabilityError(
            "date_to",
            "Tanggal akhir tidak boleh lebih awal dari tanggal awal.",
        )
    if (date_to - date_from).days > SURVEY_MAX_RANGE_DAYS:
        raise SurveyAvailabilityError(
            "date_to",
            "Rentang pencarian maksimal 31 hari setelah tanggal awal.",
        )

    slots: list[SurveySlot] = []
    current = date_from
    while current <= date_to:
        slots.extend(SurveySlot(date=current, time=slot_time) for slot_time in SURVEY_TIMES)
        current += timedelta(days=1)
    return tuple(slots)


def is_survey_slot_available(
    survey_date: date,
    survey_time: str,
    *,
    today: date,
) -> bool:
    """Check a submitted slot against the same deterministic availability source."""

    return survey_date >= today and survey_time in SURVEY_TIMES

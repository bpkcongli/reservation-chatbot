"""Cross-field and configurable reservation rules."""

from collections.abc import Collection
from dataclasses import dataclass
from datetime import date

from app.modules.catalog.domain import (
    SPECIALIZATION_OPTIONS,
    WORK_SESSION_OPTIONS,
    Specialization,
    WorkSession,
    is_survey_slot_available,
)
from app.modules.reservation.schemas import (
    BoronganReservationSlots,
    HarianReservationSlots,
)


@dataclass(frozen=True, slots=True)
class ReservationPolicy:
    max_worker_count: int = 20
    max_budget_idr: int = 100_000_000_000


DEFAULT_RESERVATION_POLICY = ReservationPolicy()


class ReservationRuleViolation(ValueError):
    """A domain rule failure associated with one user-editable field."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field


def validate_borongan_rules(
    reservation: BoronganReservationSlots,
    *,
    today: date,
    policy: ReservationPolicy = DEFAULT_RESERVATION_POLICY,
) -> BoronganReservationSlots:
    if reservation.survey_date < today:
        raise ReservationRuleViolation(
            "survey_date",
            "Tanggal survei tidak boleh berada di masa lalu.",
        )
    if not is_survey_slot_available(
        reservation.survey_date,
        reservation.survey_time,
        today=today,
    ):
        raise ReservationRuleViolation(
            "survey_time",
            "Waktu survei harus dipilih dari slot yang tersedia.",
        )
    if reservation.budget > policy.max_budget_idr:
        raise ReservationRuleViolation(
            "budget",
            f"Budget maksimal adalah Rp{policy.max_budget_idr:,}.",
        )
    return reservation


def validate_harian_rules(
    reservation: HarianReservationSlots,
    *,
    today: date,
    policy: ReservationPolicy = DEFAULT_RESERVATION_POLICY,
    active_specializations: Collection[str | Specialization] | None = None,
    active_work_sessions: Collection[str | WorkSession] | None = None,
) -> HarianReservationSlots:
    if reservation.start_date < today:
        raise ReservationRuleViolation(
            "start_date",
            "Tanggal mulai tidak boleh berada di masa lalu.",
        )
    if reservation.worker_count > policy.max_worker_count:
        raise ReservationRuleViolation(
            "worker_count",
            f"Jumlah tukang maksimal adalah {policy.max_worker_count} orang.",
        )

    specializations = (
        {option.value for option in SPECIALIZATION_OPTIONS}
        if active_specializations is None
        else active_specializations
    )
    if reservation.specialization not in specializations:
        raise ReservationRuleViolation(
            "specialization",
            "Spesialisasi tersebut sedang tidak tersedia.",
        )

    work_sessions = (
        {option.value for option in WORK_SESSION_OPTIONS}
        if active_work_sessions is None
        else active_work_sessions
    )
    if reservation.work_session not in work_sessions:
        raise ReservationRuleViolation(
            "work_session",
            "Sesi kerja tersebut sedang tidak tersedia.",
        )
    return reservation

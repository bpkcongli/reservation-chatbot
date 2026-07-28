from datetime import date

import pytest
from app.modules.reservation import (
    BoronganReservationSlots,
    HarianReservationSlots,
    ReservationPolicy,
    ReservationRuleViolation,
    validate_borongan_rules,
    validate_harian_rules,
)
from pydantic import ValidationError


def borongan_slots(**overrides: object) -> BoronganReservationSlots:
    values: dict[str, object] = {
        "customer_id": "0123456789",
        "phone_number": "+6281234567890",
        "building_type": "rumah",
        "survey_address": "Jalan Melati No. 10 Jakarta",
        "survey_date": "2026-08-03",
        "survey_time": "09:00",
        "budget": 20_000_000,
    }
    values.update(overrides)
    return BoronganReservationSlots.model_validate(values)


def harian_slots(**overrides: object) -> HarianReservationSlots:
    values: dict[str, object] = {
        "customer_id": "0123456789",
        "phone_number": "+6281234567890",
        "specialization": "listrik",
        "problem_description": "Instalasi listrik sering turun.",
        "worker_count": 2,
        "start_date": "2026-08-03",
        "end_date": "2026-08-04",
        "work_session": "full_day",
        "work_address": "Jalan Melati No. 10 Jakarta",
        "problem_photo": None,
    }
    values.update(overrides)
    return HarianReservationSlots.model_validate(values)


def test_borongan_schema_and_rules_accept_complete_valid_slots() -> None:
    slots = borongan_slots()

    assert validate_borongan_rules(slots, today=date(2026, 7, 29)) is slots
    assert slots.customer_id == "0123456789"


def test_borongan_requires_an_available_survey_time() -> None:
    slots = borongan_slots(survey_time="10:00")

    with pytest.raises(ReservationRuleViolation) as error:
        validate_borongan_rules(slots, today=date(2026, 7, 29))

    assert error.value.field == "survey_time"


def test_borongan_budget_respects_configurable_limit() -> None:
    slots = borongan_slots(budget=20_000_000)

    with pytest.raises(ReservationRuleViolation) as error:
        validate_borongan_rules(
            slots,
            today=date(2026, 7, 29),
            policy=ReservationPolicy(max_budget_idr=10_000_000),
        )

    assert error.value.field == "budget"


def test_harian_schema_rejects_end_before_start() -> None:
    with pytest.raises(ValidationError):
        harian_slots(start_date="2026-08-04", end_date="2026-08-03")


def test_harian_rules_enforce_worker_limit_and_active_catalog() -> None:
    too_many_workers = harian_slots(worker_count=3)
    with pytest.raises(ReservationRuleViolation) as worker_error:
        validate_harian_rules(
            too_many_workers,
            today=date(2026, 7, 29),
            policy=ReservationPolicy(max_worker_count=2),
        )
    assert worker_error.value.field == "worker_count"

    inactive_specialization = harian_slots(specialization="pipa")
    with pytest.raises(ReservationRuleViolation) as specialization_error:
        validate_harian_rules(
            inactive_specialization,
            today=date(2026, 7, 29),
            active_specializations=set(),
        )
    assert specialization_error.value.field == "specialization"


def test_common_slots_reject_invalid_customer_and_phone() -> None:
    with pytest.raises(ValidationError) as error:
        borongan_slots(customer_id="123", phone_number="081234567890")

    fields = {item["loc"][0] for item in error.value.errors()}
    assert fields == {"customer_id", "phone_number"}

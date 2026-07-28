"""Build safe summaries and fixed-price snapshots from complete draft slots."""

from datetime import date

from app.modules.pricing import calculate_borongan_price, calculate_harian_price
from app.modules.reservation.rules import (
    validate_borongan_rules,
    validate_harian_rules,
)
from app.modules.reservation.schemas import (
    BoronganReservationSlots,
    HarianReservationSlots,
)


def mask_phone_number(phone_number: str) -> str:
    """Keep a recognizable prefix/suffix without exposing the full number."""

    if len(phone_number) <= 9:
        return f"{phone_number[:3]}****{phone_number[-2:]}"
    return f"{phone_number[:6]}****{phone_number[-4:]}"


def build_confirmation_snapshot(
    slots: dict[str, object],
    *,
    today: date,
) -> tuple[dict[str, object], dict[str, object]]:
    """Validate a complete draft and return API-safe summary plus pricing."""

    service_type = slots.get("service_type")
    if service_type == "borongan":
        borongan = BoronganReservationSlots.model_validate(slots)
        validate_borongan_rules(borongan, today=today)
        borongan_price = calculate_borongan_price(
            building_type=borongan.building_type,
            budget=borongan.budget,
        )
        summary: dict[str, object] = {
            "service_type": "borongan",
            "customer_id": borongan.customer_id,
            "phone_number_masked": mask_phone_number(borongan.phone_number),
            "building_type": borongan.building_type.value,
            "survey_address": borongan.survey_address,
            "survey_date": borongan.survey_date.isoformat(),
            "survey_time": borongan.survey_time,
            "budget": borongan.budget,
        }
        return summary, borongan_price.model_dump(mode="json")

    if service_type == "harian":
        harian = HarianReservationSlots.model_validate(slots)
        validate_harian_rules(harian, today=today)
        harian_price = calculate_harian_price(
            specialization=harian.specialization,
            work_session=harian.work_session,
            worker_count=harian.worker_count,
            start_date=harian.start_date,
            end_date=harian.end_date,
        )
        summary = {
            "service_type": "harian",
            "customer_id": harian.customer_id,
            "phone_number_masked": mask_phone_number(harian.phone_number),
            "specialization": harian.specialization.value,
            "problem_description": harian.problem_description,
            "worker_count": harian.worker_count,
            "start_date": harian.start_date.isoformat(),
            "end_date": harian.end_date.isoformat(),
            "work_session": harian.work_session.value,
            "work_address": harian.work_address,
            "attachment": None,
        }
        return summary, harian_price.model_dump(mode="json")

    raise ValueError("Draft service_type must be borongan or harian.")

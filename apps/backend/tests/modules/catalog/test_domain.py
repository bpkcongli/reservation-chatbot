from datetime import date

import pytest
from app.modules.catalog.domain import (
    SERVICE_SEEDS,
    SURVEY_TIMES,
    SurveyAvailabilityError,
    list_survey_availability,
)


def test_catalog_seed_contains_two_services_and_required_harian_options() -> None:
    assert [service.value for service in SERVICE_SEEDS] == ["borongan", "harian"]
    harian = SERVICE_SEEDS[1]
    assert [option.value for option in harian.specializations] == [
        "cat",
        "genteng",
        "ac",
        "listrik",
        "keramik",
        "pipa",
    ]
    assert [option.value for option in harian.work_sessions] == [
        "full_day",
        "morning",
        "afternoon",
    ]


def test_survey_availability_is_inclusive_and_deterministic() -> None:
    slots = list_survey_availability(
        date(2026, 8, 3),
        date(2026, 8, 4),
        today=date(2026, 7, 29),
    )

    assert len(slots) == 4
    assert {slot.time for slot in slots} == set(SURVEY_TIMES)
    assert slots[0].date == date(2026, 8, 3)
    assert slots[-1].date == date(2026, 8, 4)
    assert all(slot.available for slot in slots)


@pytest.mark.parametrize(
    ("date_from", "date_to", "field"),
    [
        (date(2026, 7, 28), date(2026, 7, 29), "date_from"),
        (date(2026, 8, 3), date(2026, 8, 2), "date_to"),
        (date(2026, 8, 3), date(2026, 9, 4), "date_to"),
    ],
)
def test_survey_availability_rejects_invalid_ranges(
    date_from: date,
    date_to: date,
    field: str,
) -> None:
    with pytest.raises(SurveyAvailabilityError) as error:
        list_survey_availability(
            date_from,
            date_to,
            today=date(2026, 7, 29),
        )

    assert error.value.field == field

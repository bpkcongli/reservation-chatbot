from datetime import date

import pytest
from app.modules.pricing import (
    PricingInputError,
    calculate_borongan_price,
    calculate_harian_price,
    inclusive_day_count,
)
from app.modules.pricing.config import BORONGAN_BASE_PRICES, DAILY_RATES


def test_pricing_v1_contains_the_complete_fixed_rate_matrix() -> None:
    assert {
        specialization.value: {session.value: rate for session, rate in session_rates.items()}
        for specialization, session_rates in DAILY_RATES.items()
    } == {
        "cat": {"full_day": 250_000, "morning": 150_000, "afternoon": 150_000},
        "genteng": {"full_day": 350_000, "morning": 210_000, "afternoon": 210_000},
        "ac": {"full_day": 300_000, "morning": 180_000, "afternoon": 180_000},
        "listrik": {"full_day": 325_000, "morning": 195_000, "afternoon": 195_000},
        "keramik": {"full_day": 300_000, "morning": 180_000, "afternoon": 180_000},
        "pipa": {"full_day": 325_000, "morning": 195_000, "afternoon": 195_000},
    }
    assert {building.value: price for building, price in BORONGAN_BASE_PRICES.items()} == {
        "rumah": 5_000_000,
        "apartemen": 4_000_000,
        "ruko": 7_500_000,
    }


def test_harian_price_uses_inclusive_days_workers_and_admin_fee() -> None:
    breakdown = calculate_harian_price(
        specialization="listrik",
        work_session="full_day",
        worker_count=2,
        start_date=date(2026, 8, 3),
        end_date=date(2026, 8, 4),
    )

    assert breakdown.day_count == 2
    assert breakdown.unit_rate == 325_000
    assert breakdown.subtotal == 1_300_000
    assert breakdown.admin_fee == 25_000
    assert breakdown.estimated_price == 1_325_000
    assert breakdown.pricing_version == "pricing-v1"
    assert breakdown.currency == "IDR"


def test_borongan_budget_is_reported_but_does_not_change_fixed_total() -> None:
    lower_budget = calculate_borongan_price(building_type="rumah", budget=4_000_000)
    higher_budget = calculate_borongan_price(building_type="rumah", budget=40_000_000)

    assert lower_budget.base_price == 5_000_000
    assert lower_budget.survey_fee == 100_000
    assert lower_budget.admin_fee == 25_000
    assert lower_budget.estimated_price == 5_125_000
    assert higher_budget.estimated_price == lower_budget.estimated_price
    assert higher_budget.budget == 40_000_000


def test_invalid_price_inputs_fail_with_the_related_field() -> None:
    assert inclusive_day_count(date(2026, 8, 3), date(2026, 8, 3)) == 1

    with pytest.raises(PricingInputError) as error:
        inclusive_day_count(date(2026, 8, 4), date(2026, 8, 3))
    assert error.value.field == "end_date"

    with pytest.raises(PricingInputError) as budget_error:
        calculate_borongan_price(building_type="ruko", budget=0)
    assert budget_error.value.field == "budget"

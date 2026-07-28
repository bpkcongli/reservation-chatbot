from datetime import date

from app.modules.reservation.summary import build_confirmation_snapshot, mask_phone_number


def test_borongan_confirmation_snapshot_masks_phone_and_keeps_budget_separate() -> None:
    summary, price = build_confirmation_snapshot(
        {
            "service_type": "borongan",
            "customer_id": "0123456789",
            "phone_number": "+6281234567890",
            "building_type": "rumah",
            "survey_address": "Jalan Melati No. 10 Jakarta",
            "survey_date": "2026-08-03",
            "survey_time": "09:00",
            "budget": 20_000_000,
        },
        today=date(2026, 7, 29),
    )

    assert summary["phone_number_masked"] == "+62812****7890"
    assert "phone_number" not in summary
    assert summary["budget"] == 20_000_000
    assert price["estimated_price"] == 5_125_000
    assert price["budget"] == 20_000_000


def test_harian_confirmation_snapshot_includes_fixed_price_breakdown() -> None:
    summary, price = build_confirmation_snapshot(
        {
            "service_type": "harian",
            "customer_id": "0123456789",
            "phone_number": "+6281234567890",
            "specialization": "listrik",
            "problem_description": "Instalasi listrik sering turun.",
            "worker_count": 2,
            "start_date": "2026-08-03",
            "end_date": "2026-08-04",
            "work_session": "full_day",
            "problem_photo": None,
            "work_address": "Jalan Melati No. 10 Jakarta",
        },
        today=date(2026, 7, 29),
    )

    assert summary["attachment"] is None
    assert summary["specialization"] == "listrik"
    assert price["day_count"] == 2
    assert price["estimated_price"] == 1_325_000
    assert mask_phone_number("+6281234567890") == "+62812****7890"

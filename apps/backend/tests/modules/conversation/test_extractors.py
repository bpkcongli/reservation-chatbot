from datetime import date

import pytest
from app.modules.conversation.extractors import (
    extract_budget,
    extract_building_type,
    extract_customer_id,
    extract_dates,
    extract_phone_number,
    extract_session,
    extract_ticket_number,
    extract_worker_count,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0812 3456 7890", "+6281234567890"),
        ("+62 812-3456-7890", "+6281234567890"),
        ("6281234567890", "+6281234567890"),
        ("nomor saya 0812 3456 7890 ya", "+6281234567890"),
        ("12345", None),
    ],
)
def test_extract_phone_number_normalizes_indonesian_formats(
    raw: str,
    expected: str | None,
) -> None:
    assert extract_phone_number(raw) == expected


def test_customer_id_requires_exactly_ten_ascii_digits() -> None:
    assert extract_customer_id("0123456789") == "0123456789"
    assert extract_customer_id("01234 56789") is None
    assert extract_customer_id("123456789") is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("sekitar 20 juta", 20_000_000),
        ("Rp1.500.000", 1_500_000),
        ("750 ribu", 750_000),
        ("1,5 miliar", 1_500_000_000),
    ],
)
def test_extract_budget_supports_common_rupiah_notation(raw: str, expected: int) -> None:
    assert extract_budget(raw) == expected


def test_extract_worker_count_supports_digits_and_limited_number_words() -> None:
    assert extract_worker_count("butuh 3 orang") == 3
    assert extract_worker_count("dua tukang") == 2


def test_extract_dates_understands_indonesian_shared_month_range() -> None:
    assert extract_dates(
        "dua tukang dari tanggal 2 sampai 3 Agustus 2026",
        reference_date=date(2026, 7, 29),
    ) == (date(2026, 8, 2), date(2026, 8, 3))


def test_extract_session_building_and_ticket_use_canonical_values() -> None:
    assert extract_session("setengah hari pagi") == "morning"
    assert extract_building_type("survei rumah saya") == "rumah"
    assert extract_ticket_number("tkt-20260728-ab12cd") == "TKT-20260728-AB12CD"
    assert extract_ticket_number("TKT-20260728-ABC") is None

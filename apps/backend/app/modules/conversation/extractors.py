"""State-aware, rule-based extractors for structured conversation values."""

import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

CUSTOMER_ID_PATTERN = re.compile(r"^[0-9]{10}$")
TICKET_NUMBER_PATTERN = re.compile(r"^TKT-[0-9]{8}-[A-Z0-9]{6}$")

_MONTHS = {
    "januari": 1,
    "februari": 2,
    "maret": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "agustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "desember": 12,
}
_NUMBER_WORDS = {
    "satu": 1,
    "seorang": 1,
    "dua": 2,
    "tiga": 3,
    "empat": 4,
    "lima": 5,
    "enam": 6,
    "tujuh": 7,
    "delapan": 8,
    "sembilan": 9,
    "sepuluh": 10,
}
_SPECIALIZATIONS = ("cat", "genteng", "ac", "listrik", "keramik", "pipa")


def extract_customer_id(text: str) -> str | None:
    """Extract an ID only when the entire answer is exactly ten ASCII digits."""

    candidate = text.strip()
    return candidate if CUSTOMER_ID_PATTERN.fullmatch(candidate) else None


def extract_phone_number(text: str) -> str | None:
    """Normalize a plausible Indonesian number to its ``+62`` representation."""

    match = re.search(
        r"(?<![0-9])(?:\+?62|0)[0-9\s().-]{6,}[0-9](?![0-9])",
        text,
    )
    if match is None:
        return None

    candidate = match.group(0)
    digits = re.sub(r"\D", "", candidate)
    if digits.startswith("62"):
        subscriber = digits[2:]
    elif digits.startswith("0"):
        subscriber = digits[1:]
    else:
        return None

    if not re.fullmatch(r"[2-9][0-9]{7,11}", subscriber):
        return None
    return f"+62{subscriber}"


def _decimal_number(raw: str) -> Decimal | None:
    compact = raw.strip().replace(" ", "")
    if not compact:
        return None
    try:
        if "," in compact:
            return Decimal(compact.replace(".", "").replace(",", "."))
        if compact.count(".") == 1 and len(compact.rsplit(".", maxsplit=1)[1]) <= 2:
            return Decimal(compact)
        return Decimal(compact.replace(".", ""))
    except InvalidOperation:
        return None


def extract_budget(text: str) -> int | None:
    """Extract Indonesian rupiah notation, including ``ribu`` and ``juta``."""

    normalized = text.casefold()
    unit_match = re.search(
        r"(?<![0-9])([0-9]+(?:[.,][0-9]+)?)\s*(ribu|rb|juta|jt|miliar|milyar)\b",
        normalized,
    )
    if unit_match:
        amount = _decimal_number(unit_match.group(1))
        unit = unit_match.group(2)
        if unit in {"ribu", "rb"}:
            multiplier = 1_000
        elif unit in {"juta", "jt"}:
            multiplier = 1_000_000
        else:
            multiplier = 1_000_000_000
        if amount is None:
            return None
        decimal_value = amount * multiplier
        return (
            int(decimal_value)
            if decimal_value == decimal_value.to_integral_value() and decimal_value > 0
            else None
        )

    rupiah_match = re.search(
        r"(?:\brp\.?\s*)?([0-9]{1,3}(?:[.\s][0-9]{3})+|[0-9]+)\b",
        normalized,
    )
    if rupiah_match is None:
        return None
    digits = re.sub(r"\D", "", rupiah_match.group(1))
    integer_value = int(digits)
    return integer_value if integer_value > 0 else None


def extract_worker_count(text: str) -> int | None:
    """Extract a numeric or limited Indonesian number-word worker count."""

    normalized = text.casefold()
    numeric = re.search(r"\b([0-9]{1,2})\s*(?:orang|tukang|pekerja)\b", normalized)
    if numeric:
        return int(numeric.group(1))

    for word, value in _NUMBER_WORDS.items():
        if re.search(rf"\b{word}\s*(?:orang|tukang|pekerja)\b", normalized):
            return value

    if re.fullmatch(r"\s*[0-9]{1,2}\s*", normalized):
        return int(normalized)
    return _NUMBER_WORDS.get(normalized.strip())


def extract_building_type(text: str) -> str | None:
    """Return the canonical supported building type mentioned in text."""

    normalized = text.casefold()
    aliases = {
        "rumah": "rumah",
        "apartemen": "apartemen",
        "apartment": "apartemen",
        "ruko": "ruko",
    }
    for alias, canonical in aliases.items():
        if re.search(rf"\b{alias}\b", normalized):
            return canonical
    return None


def extract_specialization(text: str) -> str | None:
    """Return one of the six canonical daily-worker specializations."""

    normalized = text.casefold()
    for specialization in _SPECIALIZATIONS:
        if re.search(rf"\b{specialization}\b", normalized):
            return specialization
    return None


def extract_work_session(text: str) -> str | None:
    """Normalize common Indonesian work-session phrases."""

    normalized = " ".join(text.casefold().strip().replace("_", " ").split())
    patterns = (
        (r"\b(?:sehari penuh|satu hari penuh|full day|fulltime|seharian)\b", "full_day"),
        (r"\b(?:setengah hari pagi|sesi pagi|pagi|morning)\b", "morning"),
        (r"\b(?:setengah hari sore|sesi sore|sore|siang|afternoon)\b", "afternoon"),
    )
    for pattern, canonical in patterns:
        if re.search(pattern, normalized):
            return canonical
    return None


def extract_session(text: str) -> str | None:
    """Backward-friendly alias for the work-session extractor."""

    return extract_work_session(text)


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def extract_dates(text: str, *, reference_date: date | None = None) -> tuple[date, ...]:
    """Extract unique dates, including Indonesian shared-month date ranges."""

    normalized = text.casefold()
    found: list[tuple[int, date]] = []
    reference = reference_date or date.today()

    relative_patterns = (("hari ini", reference), ("besok", reference + timedelta(days=1)))
    for phrase, relative_value in relative_patterns:
        match = re.search(rf"\b{phrase}\b", normalized)
        if match:
            found.append((match.start(), relative_value))

    month_names = "|".join(_MONTHS)
    shared_range = re.compile(
        rf"\b([0-9]{{1,2}})\s*(?:sampai|hingga|-)\s*"
        rf"([0-9]{{1,2}})\s+({month_names})\s+([0-9]{{4}})\b"
    )
    consumed: list[tuple[int, int]] = []
    for match in shared_range.finditer(normalized):
        month = _MONTHS[match.group(3)]
        for day_text in (match.group(1), match.group(2)):
            parsed_date = _safe_date(int(match.group(4)), month, int(day_text))
            if parsed_date is not None:
                found.append((match.start(), parsed_date))
        consumed.append(match.span())

    patterns = (
        re.compile(r"\b([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})\b"),
        re.compile(r"\b([0-9]{1,2})[/-]([0-9]{1,2})[/-]([0-9]{4})\b"),
        re.compile(rf"\b([0-9]{{1,2}})\s+({month_names})\s+([0-9]{{4}})\b"),
    )
    for pattern_index, pattern in enumerate(patterns):
        for match in pattern.finditer(normalized):
            if any(start <= match.start() < end for start, end in consumed):
                continue
            if pattern_index == 0:
                parsed_date = _safe_date(
                    int(match.group(1)), int(match.group(2)), int(match.group(3))
                )
            elif pattern_index == 1:
                parsed_date = _safe_date(
                    int(match.group(3)), int(match.group(2)), int(match.group(1))
                )
            else:
                parsed_date = _safe_date(
                    int(match.group(3)),
                    _MONTHS[match.group(2)],
                    int(match.group(1)),
                )
            if parsed_date is not None:
                found.append((match.start(), parsed_date))

    ordered: list[date] = []
    for _, value in sorted(found, key=lambda item: item[0]):
        if value not in ordered:
            ordered.append(value)
    return tuple(ordered)


def extract_date(text: str, *, reference_date: date | None = None) -> date | None:
    """Return the first recognized date."""

    dates = extract_dates(text, reference_date=reference_date)
    return dates[0] if dates else None


def extract_survey_time(text: str) -> str | None:
    """Normalize a survey clock time to ``HH:MM``."""

    normalized = text.casefold()
    clock = re.search(r"\b(?:jam\s*)?([01]?[0-9]|2[0-3])(?:[:.]([0-5][0-9]))?\b", normalized)
    if clock is None:
        return None
    hour = int(clock.group(1))
    minute = int(clock.group(2) or "0")
    if ("sore" in normalized or "siang" in normalized) and hour < 12:
        hour += 12
    return f"{hour:02d}:{minute:02d}"


def extract_ticket_number(text: str) -> str | None:
    """Normalize case and require the complete canonical ticket format."""

    candidate = text.strip().upper()
    return candidate if TICKET_NUMBER_PATTERN.fullmatch(candidate) else None

"""Immutable fixed rates for pricing-v1."""

from types import MappingProxyType
from typing import Final

from app.modules.catalog.domain import BuildingType, Specialization, WorkSession

PRICING_VERSION: Final = "pricing-v1"
CURRENCY: Final = "IDR"
ADMIN_FEE: Final = 25_000
BORONGAN_SURVEY_FEE: Final = 100_000
PRICING_DISCLAIMER: Final = "Harga fixed pricing-v1 hanya untuk demonstrasi chatbot."

_DAILY_RATE_ROWS = {
    Specialization.CAT: {
        WorkSession.FULL_DAY: 250_000,
        WorkSession.MORNING: 150_000,
        WorkSession.AFTERNOON: 150_000,
    },
    Specialization.GENTENG: {
        WorkSession.FULL_DAY: 350_000,
        WorkSession.MORNING: 210_000,
        WorkSession.AFTERNOON: 210_000,
    },
    Specialization.AC: {
        WorkSession.FULL_DAY: 300_000,
        WorkSession.MORNING: 180_000,
        WorkSession.AFTERNOON: 180_000,
    },
    Specialization.LISTRIK: {
        WorkSession.FULL_DAY: 325_000,
        WorkSession.MORNING: 195_000,
        WorkSession.AFTERNOON: 195_000,
    },
    Specialization.KERAMIK: {
        WorkSession.FULL_DAY: 300_000,
        WorkSession.MORNING: 180_000,
        WorkSession.AFTERNOON: 180_000,
    },
    Specialization.PIPA: {
        WorkSession.FULL_DAY: 325_000,
        WorkSession.MORNING: 195_000,
        WorkSession.AFTERNOON: 195_000,
    },
}

DAILY_RATES = MappingProxyType(
    {
        specialization: MappingProxyType(session_rates)
        for specialization, session_rates in _DAILY_RATE_ROWS.items()
    }
)

BORONGAN_BASE_PRICES = MappingProxyType(
    {
        BuildingType.RUMAH: 5_000_000,
        BuildingType.APARTEMEN: 4_000_000,
        BuildingType.RUKO: 7_500_000,
    }
)

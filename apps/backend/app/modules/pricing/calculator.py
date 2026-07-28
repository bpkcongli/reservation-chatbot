"""Pure fixed-rate calculations for pricing-v1."""

from datetime import date

from app.modules.catalog.domain import BuildingType, Specialization, WorkSession
from app.modules.pricing.config import (
    ADMIN_FEE,
    BORONGAN_BASE_PRICES,
    BORONGAN_SURVEY_FEE,
    DAILY_RATES,
    PRICING_DISCLAIMER,
)
from app.modules.pricing.schemas import (
    BoronganPriceBreakdown,
    HarianPriceBreakdown,
)


class PricingInputError(ValueError):
    """Invalid input supplied to a pricing calculation."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field


def inclusive_day_count(start_date: date, end_date: date) -> int:
    """Count calendar days including both endpoints."""

    if end_date < start_date:
        raise PricingInputError(
            "end_date",
            "Tanggal selesai tidak boleh sebelum tanggal mulai.",
        )
    return (end_date - start_date).days + 1


def calculate_harian_price(
    *,
    specialization: Specialization | str,
    work_session: WorkSession | str,
    worker_count: int,
    start_date: date,
    end_date: date,
) -> HarianPriceBreakdown:
    try:
        canonical_specialization = Specialization(specialization)
    except ValueError as error:
        raise PricingInputError(
            "specialization",
            "Spesialisasi tidak tersedia pada pricing-v1.",
        ) from error
    try:
        canonical_session = WorkSession(work_session)
    except ValueError as error:
        raise PricingInputError(
            "work_session",
            "Sesi kerja tidak tersedia pada pricing-v1.",
        ) from error
    if isinstance(worker_count, bool) or not isinstance(worker_count, int) or worker_count < 1:
        raise PricingInputError(
            "worker_count",
            "Jumlah tukang harus berupa bilangan bulat positif.",
        )

    day_count = inclusive_day_count(start_date, end_date)
    unit_rate = DAILY_RATES[canonical_specialization][canonical_session]
    subtotal = unit_rate * worker_count * day_count
    return HarianPriceBreakdown(
        specialization=canonical_specialization,
        work_session=canonical_session,
        unit_rate=unit_rate,
        worker_count=worker_count,
        day_count=day_count,
        subtotal=subtotal,
        estimated_price=subtotal + ADMIN_FEE,
        disclaimer=PRICING_DISCLAIMER,
    )


def calculate_borongan_price(
    *,
    building_type: BuildingType | str,
    budget: int,
) -> BoronganPriceBreakdown:
    try:
        canonical_building = BuildingType(building_type)
    except ValueError as error:
        raise PricingInputError(
            "building_type",
            "Jenis bangunan tidak tersedia pada pricing-v1.",
        ) from error
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 1:
        raise PricingInputError(
            "budget",
            "Budget harus berupa bilangan rupiah positif.",
        )

    base_price = BORONGAN_BASE_PRICES[canonical_building]
    return BoronganPriceBreakdown(
        building_type=canonical_building,
        base_price=base_price,
        subtotal=base_price,
        budget=budget,
        estimated_price=base_price + BORONGAN_SURVEY_FEE + ADMIN_FEE,
        disclaimer=PRICING_DISCLAIMER,
    )


class PricingCalculator:
    """Object-oriented facade for application-service injection."""

    @staticmethod
    def calculate_harian(
        *,
        specialization: Specialization | str,
        work_session: WorkSession | str,
        worker_count: int,
        start_date: date,
        end_date: date,
    ) -> HarianPriceBreakdown:
        return calculate_harian_price(
            specialization=specialization,
            work_session=work_session,
            worker_count=worker_count,
            start_date=start_date,
            end_date=end_date,
        )

    @staticmethod
    def calculate_borongan(
        *,
        building_type: BuildingType | str,
        budget: int,
    ) -> BoronganPriceBreakdown:
        return calculate_borongan_price(building_type=building_type, budget=budget)

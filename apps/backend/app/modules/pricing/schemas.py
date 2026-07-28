"""Typed pricing-v1 breakdowns returned by the backend."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.catalog.domain import BuildingType, Specialization, WorkSession


class PriceBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    pricing_version: Literal["pricing-v1"] = "pricing-v1"
    currency: Literal["IDR"] = "IDR"
    admin_fee: Literal[25000] = 25_000
    estimated_price: int = Field(ge=0)
    disclaimer: str


class HarianPriceBreakdown(PriceBreakdown):
    service_type: Literal["harian"] = "harian"
    specialization: Specialization
    work_session: WorkSession
    unit_rate: int = Field(gt=0)
    worker_count: int = Field(gt=0)
    day_count: int = Field(gt=0)
    subtotal: int = Field(ge=0)


class BoronganPriceBreakdown(PriceBreakdown):
    service_type: Literal["borongan"] = "borongan"
    building_type: BuildingType
    base_price: int = Field(gt=0)
    survey_fee: Literal[100000] = 100_000
    subtotal: int = Field(gt=0)
    budget: int = Field(gt=0)

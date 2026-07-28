"""Validated service-specific reservation slot schemas."""

from datetime import date
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.catalog.domain import BuildingType, Specialization, WorkSession


class ReservationSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CustomerContactSlots(ReservationSchema):
    customer_id: str = Field(pattern=r"^[0-9]{10}$")
    phone_number: str = Field(pattern=r"^\+62[2-9][0-9]{7,11}$")


class BoronganReservationSlots(CustomerContactSlots):
    service_type: Literal["borongan"] = "borongan"
    building_type: BuildingType
    survey_address: str = Field(min_length=10, max_length=300)
    survey_date: date
    survey_time: str = Field(pattern=r"^([01][0-9]|2[0-3]):[0-5][0-9]$")
    budget: int = Field(gt=0, strict=True)


class HarianReservationSlots(CustomerContactSlots):
    service_type: Literal["harian"] = "harian"
    specialization: Specialization
    problem_description: str = Field(min_length=10, max_length=500)
    worker_count: int = Field(gt=0, strict=True)
    start_date: date
    end_date: date
    work_session: WorkSession
    work_address: str = Field(min_length=10, max_length=300)
    problem_photo: str | None = Field(default=None, min_length=26, max_length=26)

    @model_validator(mode="after")
    def validate_date_order(self) -> Self:
        if self.end_date < self.start_date:
            raise ValueError("Tanggal selesai tidak boleh sebelum tanggal mulai.")
        return self

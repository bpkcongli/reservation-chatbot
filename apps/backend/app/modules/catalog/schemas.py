"""Strict response DTOs for catalog endpoints."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.catalog.domain import ServiceType


class CatalogSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SuccessStatus(CatalogSchema):
    code: Literal[120000000] = 120000000
    message: Literal["Success."] = "Success."
    error_details: list[object] = Field(default_factory=list, alias="errorDetails")


class CatalogOptionData(CatalogSchema):
    value: str
    label: str


class ServiceCatalogItemData(CatalogSchema):
    value: ServiceType
    label: str
    description: str
    specializations: list[CatalogOptionData]
    work_sessions: list[CatalogOptionData]


class ServiceCatalogData(CatalogSchema):
    pricing_version: Literal["pricing-v1"] = "pricing-v1"
    services: list[ServiceCatalogItemData]


class ServiceCatalogResponse(CatalogSchema):
    status: SuccessStatus = Field(default_factory=SuccessStatus)
    data: ServiceCatalogData


class SurveySlotData(CatalogSchema):
    date: date
    time: str = Field(pattern=r"^([01][0-9]|2[0-3]):[0-5][0-9]$")
    available: bool


class SurveyAvailabilityData(CatalogSchema):
    timezone: Literal["Asia/Jakarta"] = "Asia/Jakarta"
    slots: list[SurveySlotData]


class SurveySlotResponse(CatalogSchema):
    status: SuccessStatus = Field(default_factory=SuccessStatus)
    data: SurveyAvailabilityData

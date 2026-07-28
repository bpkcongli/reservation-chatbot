"""Strict HTTP response schemas for ticket lookup."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.catalog.domain import ServiceType
from app.modules.ticketing.domain import EmailDelivery, TicketStatus


class TicketSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SuccessStatus(TicketSchema):
    code: Literal[120000000] = 120000000
    message: Literal["Success."] = "Success."
    error_details: list[object] = Field(default_factory=list, alias="errorDetails")


class TicketData(TicketSchema):
    ticket_number: str = Field(pattern=r"^TKT-[0-9]{8}-[A-Z0-9]{6}$")
    service_type: ServiceType
    status: TicketStatus
    pricing_version: Literal["pricing-v1"]
    estimated_price: int = Field(gt=0)
    budget: int | None = Field(default=None, gt=0)
    created_at: datetime
    email_delivery: EmailDelivery


class TicketResponse(TicketSchema):
    status: SuccessStatus = Field(default_factory=SuccessStatus)
    data: TicketData

"""Ticket identifiers and safe lookup representation."""

import re
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Literal

from app.modules.catalog.domain import ServiceType

TICKET_SUFFIX_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
TICKET_NUMBER_PATTERN = re.compile(r"^TKT-[0-9]{8}-[A-Z0-9]{6}$")
SuffixFactory = Callable[[], str]


class TicketStatus(StrEnum):
    MENUNGGU_PEMBAYARAN = "MENUNGGU_PEMBAYARAN"


class EmailDelivery(StrEnum):
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


@dataclass(frozen=True, slots=True)
class Ticket:
    id: str
    reservation_id: str
    ticket_number: str
    status: TicketStatus
    created_at: datetime


@dataclass(frozen=True, slots=True)
class TicketView:
    ticket_number: str
    service_type: ServiceType
    status: TicketStatus
    pricing_version: Literal["pricing-v1"]
    estimated_price: int
    budget: int | None
    created_at: datetime
    email_delivery: EmailDelivery = EmailDelivery.NOT_IMPLEMENTED


def random_ticket_suffix() -> str:
    return "".join(secrets.choice(TICKET_SUFFIX_ALPHABET) for _ in range(6))


def generate_ticket_number(
    created_at: datetime,
    *,
    suffix_factory: SuffixFactory = random_ticket_suffix,
) -> str:
    """Generate TKT-YYYYMMDD-XXXXXX from the caller's business timezone."""

    suffix = suffix_factory().upper()
    if re.fullmatch(r"[A-Z0-9]{6}", suffix) is None:
        raise ValueError("Ticket suffix must contain exactly 6 uppercase letters or digits.")
    return f"TKT-{created_at:%Y%m%d}-{suffix}"


def normalize_ticket_number(value: str) -> str | None:
    candidate = value.strip().upper()
    return candidate if TICKET_NUMBER_PATTERN.fullmatch(candidate) else None

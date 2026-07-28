"""SQLAlchemy model for finalized reservation snapshots."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base


class ReservationRecord(Base):
    """Immutable reservation data created by the later finalization transaction."""

    __tablename__ = "reservation"
    __table_args__ = (
        Index("ix_reservation_service_id", "service_id"),
        Index("ix_reservation_reservation_draft_id", "reservation_draft_id"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    reservation_draft_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("reservation_draft.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    service_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("service.id", ondelete="RESTRICT"),
        nullable=False,
    )
    customer_id: Mapped[str] = mapped_column(String(10), nullable=False)
    phone_number_encrypted: Mapped[str] = mapped_column(String(500), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    estimated_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)

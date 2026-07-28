"""SQLAlchemy ticket persistence model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base


class TicketRecord(Base):
    __tablename__ = "ticket"
    __table_args__ = (
        Index("ix_ticket_reservation_id", "reservation_id"),
        Index("ix_ticket_ticket_number", "ticket_number"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    reservation_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("reservation.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    ticket_number: Mapped[str] = mapped_column(String(26), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)

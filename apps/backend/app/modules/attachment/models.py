"""SQLAlchemy attachment metadata model."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base


class AttachmentRecord(Base):
    __tablename__ = "attachment"
    __table_args__ = (
        Index("ix_attachment_reservation_draft_id", "reservation_draft_id"),
        Index("ix_attachment_reservation_id", "reservation_id"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    reservation_draft_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("reservation_draft.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    reservation_id: Mapped[str | None] = mapped_column(
        String(26),
        ForeignKey("reservation.id", ondelete="RESTRICT"),
        nullable=True,
        unique=True,
    )
    stored_name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String(30), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)

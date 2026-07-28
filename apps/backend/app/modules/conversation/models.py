"""SQLAlchemy persistence models for conversations and reservation drafts."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base


class ConversationRecord(Base):
    """Persisted state and non-transactional conversation metadata."""

    __tablename__ = "conversation"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    locale: Mapped[str] = mapped_column(String(10), nullable=False)
    state: Mapped[str] = mapped_column(String(40), nullable=False)
    context: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)


class ConversationMessageRecord(Base):
    """One ordered user or bot message used to restore chat history."""

    __tablename__ = "conversation_message"
    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "turn_index",
            name="uq_conversation_message_turn",
        ),
        UniqueConstraint(
            "conversation_id",
            "client_message_id",
            name="uq_conversation_message_client_id",
        ),
        Index("ix_conversation_message_conversation_id", "conversation_id"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("conversation.id", ondelete="CASCADE"),
        nullable=False,
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    client_message_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sender: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)


class ReservationDraftRecord(Base):
    """Validated partial reservation data owned by one conversation."""

    __tablename__ = "reservation_draft"
    __table_args__ = (
        UniqueConstraint("conversation_id", name="uq_reservation_draft_conversation_id"),
        Index("ix_reservation_draft_conversation_id", "conversation_id"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey("conversation.id", ondelete="CASCADE"),
        nullable=False,
    )
    service_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    slots: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    price_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)

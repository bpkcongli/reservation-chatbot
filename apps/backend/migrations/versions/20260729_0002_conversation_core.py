"""Persist conversation state, messages, and reservation drafts.

Revision ID: 20260729_0002
Revises: 20260728_0001
Create Date: 2026-07-29 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260729_0002"
down_revision: str | Sequence[str] | None = "20260728_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversation",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("locale", sa.String(length=10), nullable=False),
        sa.Column("state", sa.String(length=40), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "conversation_message",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("conversation_id", sa.String(length=26), nullable=False),
        sa.Column("turn_index", sa.Integer(), nullable=False),
        sa.Column("client_message_id", sa.String(length=100), nullable=True),
        sa.Column("sender", sa.String(length=10), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversation.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "conversation_id",
            "client_message_id",
            name="uq_conversation_message_client_id",
        ),
        sa.UniqueConstraint(
            "conversation_id",
            "turn_index",
            name="uq_conversation_message_turn",
        ),
    )
    op.create_index(
        "ix_conversation_message_conversation_id",
        "conversation_message",
        ["conversation_id"],
    )
    op.create_table(
        "reservation_draft",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("conversation_id", sa.String(length=26), nullable=False),
        sa.Column("service_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("slots", sa.JSON(), nullable=False),
        sa.Column("price_snapshot", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversation.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "conversation_id",
            name="uq_reservation_draft_conversation_id",
        ),
    )
    op.create_index(
        "ix_reservation_draft_conversation_id",
        "reservation_draft",
        ["conversation_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_reservation_draft_conversation_id",
        table_name="reservation_draft",
    )
    op.drop_table("reservation_draft")
    op.drop_index(
        "ix_conversation_message_conversation_id",
        table_name="conversation_message",
    )
    op.drop_table("conversation_message")
    op.drop_table("conversation")

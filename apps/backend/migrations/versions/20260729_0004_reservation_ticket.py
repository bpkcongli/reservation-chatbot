"""Create finalized reservation and ticket tables.

Revision ID: 20260729_0004
Revises: 20260729_0003
Create Date: 2026-07-29 14:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260729_0004"
down_revision: str | Sequence[str] | None = "20260729_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reservation",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("reservation_draft_id", sa.String(length=26), nullable=False),
        sa.Column("service_id", sa.BigInteger(), nullable=False),
        sa.Column("customer_id", sa.String(length=10), nullable=False),
        sa.Column("phone_number_encrypted", sa.String(length=500), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("estimated_price", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["reservation_draft_id"],
            ["reservation_draft.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["service_id"], ["service.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "reservation_draft_id",
            name="uq_reservation_reservation_draft_id",
        ),
    )
    op.create_index(
        "ix_reservation_reservation_draft_id",
        "reservation",
        ["reservation_draft_id"],
    )
    op.create_index("ix_reservation_service_id", "reservation", ["service_id"])

    op.create_table(
        "ticket",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("reservation_id", sa.String(length=26), nullable=False),
        sa.Column("ticket_number", sa.String(length=26), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["reservation_id"], ["reservation.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reservation_id", name="uq_ticket_reservation_id"),
        sa.UniqueConstraint("ticket_number", name="uq_ticket_ticket_number"),
    )
    op.create_index("ix_ticket_reservation_id", "ticket", ["reservation_id"])
    op.create_index("ix_ticket_ticket_number", "ticket", ["ticket_number"])


def downgrade() -> None:
    op.drop_index("ix_ticket_ticket_number", table_name="ticket")
    op.drop_index("ix_ticket_reservation_id", table_name="ticket")
    op.drop_table("ticket")
    op.drop_index("ix_reservation_service_id", table_name="reservation")
    op.drop_index("ix_reservation_reservation_draft_id", table_name="reservation")
    op.drop_table("reservation")

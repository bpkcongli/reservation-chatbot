"""Create optional photo attachment metadata.

Revision ID: 20260729_0005
Revises: 20260729_0004
Create Date: 2026-07-29 16:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260729_0005"
down_revision: str | Sequence[str] | None = "20260729_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "attachment",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("reservation_draft_id", sa.String(length=26), nullable=False),
        sa.Column("reservation_id", sa.String(length=26), nullable=True),
        sa.Column("stored_name", sa.String(length=80), nullable=False),
        sa.Column("content_type", sa.String(length=30), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["reservation_draft_id"],
            ["reservation_draft.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reservation_id"],
            ["reservation.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "reservation_draft_id",
            name="uq_attachment_reservation_draft_id",
        ),
        sa.UniqueConstraint("reservation_id", name="uq_attachment_reservation_id"),
        sa.UniqueConstraint("stored_name", name="uq_attachment_stored_name"),
    )
    op.create_index(
        "ix_attachment_reservation_draft_id",
        "attachment",
        ["reservation_draft_id"],
    )
    op.create_index(
        "ix_attachment_reservation_id",
        "attachment",
        ["reservation_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_attachment_reservation_id", table_name="attachment")
    op.drop_index("ix_attachment_reservation_draft_id", table_name="attachment")
    op.drop_table("attachment")

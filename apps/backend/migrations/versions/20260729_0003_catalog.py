"""Create and seed the service catalog.

Revision ID: 20260729_0003
Revises: 20260729_0002
Create Date: 2026-07-29 12:00:00
"""

from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision: str = "20260729_0003"
down_revision: str | Sequence[str] | None = "20260729_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    service = op.create_table(
        "service",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_service_code"),
    )
    specialization = op.create_table(
        "specialization",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("service_id", sa.BigInteger(), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["service_id"], ["service.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_specialization_code"),
    )
    op.create_index(
        "ix_specialization_service_id",
        "specialization",
        ["service_id"],
    )
    work_session = op.create_table(
        "work_session",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("service_id", sa.BigInteger(), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["service_id"], ["service.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_work_session_code"),
    )
    op.create_index(
        "ix_work_session_service_id",
        "work_session",
        ["service_id"],
    )

    seeded_at = datetime(2026, 7, 29, 12, 0)
    op.bulk_insert(
        service,
        [
            {
                "id": 1,
                "code": "borongan",
                "name": "Jasa Borongan",
                "description": "Permintaan pekerjaan berdasarkan survei dan budget.",
                "is_active": True,
                "created_at": seeded_at,
                "updated_at": seeded_at,
            },
            {
                "id": 2,
                "code": "harian",
                "name": "Tukang Harian",
                "description": "Tukang berdasarkan spesialisasi, durasi, dan sesi.",
                "is_active": True,
                "created_at": seeded_at,
                "updated_at": seeded_at,
            },
        ],
    )
    op.bulk_insert(
        specialization,
        [
            {
                "id": index,
                "service_id": 2,
                "code": code,
                "name": name,
                "is_active": True,
                "created_at": seeded_at,
                "updated_at": seeded_at,
            }
            for index, (code, name) in enumerate(
                (
                    ("cat", "Spesialis Cat"),
                    ("genteng", "Spesialis Genteng"),
                    ("ac", "Spesialis AC"),
                    ("listrik", "Spesialis Listrik"),
                    ("keramik", "Spesialis Keramik"),
                    ("pipa", "Spesialis Pipa"),
                ),
                start=1,
            )
        ],
    )
    op.bulk_insert(
        work_session,
        [
            {
                "id": index,
                "service_id": 2,
                "code": code,
                "name": name,
                "is_active": True,
                "created_at": seeded_at,
                "updated_at": seeded_at,
            }
            for index, (code, name) in enumerate(
                (
                    ("full_day", "Sehari penuh"),
                    ("morning", "Pagi"),
                    ("afternoon", "Siang"),
                ),
                start=1,
            )
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_work_session_service_id", table_name="work_session")
    op.drop_table("work_session")
    op.drop_index("ix_specialization_service_id", table_name="specialization")
    op.drop_table("specialization")
    op.drop_table("service")

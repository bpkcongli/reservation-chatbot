"""Persistence boundary for draft photo metadata."""

from copy import deepcopy
from datetime import UTC
from threading import RLock
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.attachment.domain import Attachment
from app.modules.attachment.models import AttachmentRecord


class AttachmentRepository(Protocol):
    def find_by_draft(self, reservation_draft_id: str) -> Attachment | None:
        """Return the one optional photo associated with a draft."""

    def add(self, attachment: Attachment) -> None:
        """Stage attachment metadata in the current transaction."""


class InMemoryAttachmentRepository:
    def __init__(self) -> None:
        self._attachments: dict[str, Attachment] = {}
        self._lock = RLock()

    def find_by_draft(self, reservation_draft_id: str) -> Attachment | None:
        with self._lock:
            attachment = self._attachments.get(reservation_draft_id)
            return deepcopy(attachment) if attachment is not None else None

    def add(self, attachment: Attachment) -> None:
        with self._lock:
            if attachment.reservation_draft_id in self._attachments:
                raise ValueError("Reservation draft already has an attachment.")
            self._attachments[attachment.reservation_draft_id] = deepcopy(attachment)


def _to_domain(row: AttachmentRecord) -> Attachment:
    created_at = (
        row.created_at.replace(tzinfo=UTC)
        if row.created_at.tzinfo is None
        else row.created_at.astimezone(UTC)
    )
    return Attachment(
        id=row.id,
        reservation_draft_id=row.reservation_draft_id,
        reservation_id=row.reservation_id,
        stored_name=row.stored_name,
        content_type=row.content_type,  # type: ignore[arg-type]
        size_bytes=row.size_bytes,
        checksum_sha256=row.checksum_sha256,
        created_at=created_at,
    )


class SqlAlchemyAttachmentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_draft(self, reservation_draft_id: str) -> Attachment | None:
        row = self._session.scalar(
            select(AttachmentRecord).where(
                AttachmentRecord.reservation_draft_id == reservation_draft_id
            )
        )
        return _to_domain(row) if row is not None else None

    def add(self, attachment: Attachment) -> None:
        self._session.add(
            AttachmentRecord(
                id=attachment.id,
                reservation_draft_id=attachment.reservation_draft_id,
                reservation_id=attachment.reservation_id,
                stored_name=attachment.stored_name,
                content_type=attachment.content_type,
                size_bytes=attachment.size_bytes,
                checksum_sha256=attachment.checksum_sha256,
                created_at=attachment.created_at.astimezone(UTC).replace(tzinfo=None),
            )
        )

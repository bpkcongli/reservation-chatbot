"""Attachment metadata that is safe to expose through the API."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

AttachmentContentType = Literal["image/jpeg", "image/png", "image/webp"]


@dataclass(frozen=True, slots=True)
class Attachment:
    id: str
    reservation_draft_id: str
    stored_name: str
    content_type: AttachmentContentType
    size_bytes: int
    checksum_sha256: str
    created_at: datetime
    reservation_id: str | None = None

    def safe_snapshot(self) -> dict[str, object]:
        return {
            "attachment_id": self.id,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "status": "ready",
        }

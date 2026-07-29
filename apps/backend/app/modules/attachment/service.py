"""Validate, store, and atomically associate an optional draft photo."""

from collections.abc import Callable
from contextlib import suppress
from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import cast

from fastapi import status

from app.modules.attachment.domain import Attachment, AttachmentContentType
from app.modules.attachment.repository import AttachmentRepository
from app.modules.conversation.dialog import prompt_for_state
from app.modules.conversation.domain import ChatMessage, ConversationState, MessageSender
from app.modules.conversation.ids import generate_ulid
from app.modules.conversation.repository import ConversationRepository
from app.modules.conversation.service import ConversationService
from app.shared.errors import ApplicationError

Clock = Callable[[], datetime]
IdFactory = Callable[[datetime], str]

_CONTENT_TYPE_EXTENSIONS: dict[str, frozenset[str]] = {
    "image/jpeg": frozenset({".jpg", ".jpeg"}),
    "image/png": frozenset({".png"}),
    "image/webp": frozenset({".webp"}),
}
_STORED_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _detected_content_type(content: bytes) -> str | None:
    if len(content) >= 3 and content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(content) >= 8 and content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "image/webp"
    return None


class LocalAttachmentStorage:
    """Private local storage that only accepts server-generated basenames."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def write(self, stored_name: str, content: bytes) -> None:
        self._directory.mkdir(parents=True, exist_ok=True)
        target = self._directory / stored_name
        with target.open("xb") as output:
            output.write(content)
        target.chmod(0o600)

    def delete(self, stored_name: str) -> None:
        target = self._directory / stored_name
        with suppress(FileNotFoundError):
            target.unlink()


class AttachmentService:
    def __init__(
        self,
        conversation_repository: ConversationRepository,
        attachment_repository: AttachmentRepository,
        storage: LocalAttachmentStorage,
        *,
        max_size_bytes: int,
        clock: Clock = _utc_now,
        id_factory: IdFactory = generate_ulid,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._attachment_repository = attachment_repository
        self._storage = storage
        self._max_size_bytes = max_size_bytes
        self._clock = clock
        self._id_factory = id_factory

    def upload(
        self,
        conversation_id: str,
        *,
        original_filename: str | None,
        declared_content_type: str | None,
        content: bytes,
    ) -> Attachment:
        context = ConversationService(self._conversation_repository).get_conversation(
            conversation_id
        )
        if (
            context.state is not ConversationState.HARIAN_ASK_PHOTO
            or context.collected_slots.get("service_type") != "harian"
        ):
            raise ApplicationError(
                code="ATTACHMENT_STATE_CONFLICT",
                message=(
                    "Foto hanya dapat diunggah pada langkah lampiran reservasi "
                    "Tukang Harian yang masih aktif."
                ),
                status_code=status.HTTP_409_CONFLICT,
                field="file",
            )
        if self._attachment_repository.find_by_draft(conversation_id) is not None:
            raise ApplicationError(
                code="ATTACHMENT_ALREADY_EXISTS",
                message="Draft reservasi ini sudah memiliki satu foto.",
                status_code=status.HTTP_409_CONFLICT,
                field="file",
            )
        if not content:
            raise ApplicationError(
                code="EMPTY_ATTACHMENT",
                message="Foto yang dipilih masih kosong. Mohon pilih file foto yang berisi.",
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                field="file",
            )
        if len(content) > self._max_size_bytes:
            raise ApplicationError(
                code="ATTACHMENT_TOO_LARGE",
                message="Ukuran foto melebihi batas yang diizinkan.",
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                field="file",
            )

        content_type = declared_content_type or ""
        extension = Path(original_filename or "").suffix.casefold()
        detected_content_type = _detected_content_type(content)
        allowed_extensions = _CONTENT_TYPE_EXTENSIONS.get(content_type)
        if (
            allowed_extensions is None
            or extension not in allowed_extensions
            or detected_content_type != content_type
        ):
            raise ApplicationError(
                code="UNSUPPORTED_ATTACHMENT_TYPE",
                message="Format foto tidak didukung. Gunakan foto JPG, PNG, atau WebP.",
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                field="file",
            )

        now = self._clock()
        attachment_id = self._id_factory(now)
        stored_name = f"{attachment_id}{_STORED_EXTENSIONS[content_type]}"
        attachment = Attachment(
            id=attachment_id,
            reservation_draft_id=conversation_id,
            stored_name=stored_name,
            content_type=cast(AttachmentContentType, content_type),
            size_bytes=len(content),
            checksum_sha256=sha256(content).hexdigest(),
            created_at=now,
        )
        self._storage.write(stored_name, content)
        try:
            self._attachment_repository.add(attachment)
            slots = {
                **context.collected_slots,
                "problem_photo": attachment.id,
                "attachment": attachment.safe_snapshot(),
            }
            next_state = ConversationState.HARIAN_ASK_ADDRESS
            prompt = prompt_for_state(next_state)
            if prompt is None:
                raise RuntimeError("Harian address prompt is not configured.")
            bot_message = ChatMessage(
                id=self._id_factory(now),
                sender=MessageSender.BOT,
                text=prompt,
                created_at=now,
            )
            updated = replace(
                context,
                state=next_state,
                messages=(*context.messages, bot_message),
                quick_replies=(),
                updated_at=now,
                collected_slots=slots,
            )
            self._conversation_repository.save(updated)
        except Exception:
            self._storage.delete(stored_name)
            raise
        return attachment

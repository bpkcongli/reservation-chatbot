from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.modules.attachment.repository import InMemoryAttachmentRepository
from app.modules.attachment.service import AttachmentService, LocalAttachmentStorage
from app.modules.conversation.domain import ConversationContext, ConversationState
from app.modules.conversation.repository import InMemoryConversationRepository
from app.shared.errors import ApplicationError

FIXED_NOW = datetime(2026, 7, 29, 9, 0, tzinfo=UTC)
CONVERSATION_ID = "01K1A2B3C4D5E6F7G8H9J0K1M2"


def _context(state: ConversationState) -> ConversationContext:
    return ConversationContext(
        conversation_id=CONVERSATION_ID,
        locale="id-ID",
        state=state,
        messages=(),
        quick_replies=(),
        created_at=FIXED_NOW,
        updated_at=FIXED_NOW,
        collected_slots={"service_type": "harian"},
    )


def _service(
    tmp_path: Path,
    *,
    state: ConversationState = ConversationState.HARIAN_ASK_PHOTO,
    max_size_bytes: int = 100,
) -> tuple[AttachmentService, InMemoryAttachmentRepository]:
    conversations = InMemoryConversationRepository()
    conversations.create(_context(state))
    attachments = InMemoryAttachmentRepository()
    return (
        AttachmentService(
            conversations,
            attachments,
            LocalAttachmentStorage(tmp_path),
            max_size_bytes=max_size_bytes,
            clock=lambda: FIXED_NOW,
            id_factory=lambda _: "01K1A2B3C4D5E6F7G8H9J0K1M3",
        ),
        attachments,
    )


def test_upload_rejects_content_over_configured_limit_without_writing_file(
    tmp_path: Path,
) -> None:
    service, repository = _service(tmp_path, max_size_bytes=8)

    with pytest.raises(ApplicationError) as error:
        service.upload(
            CONVERSATION_ID,
            original_filename="foto.png",
            declared_content_type="image/png",
            content=b"\x89PNG\r\n\x1a\nextra",
        )

    assert error.value.status_code == 413
    assert repository.find_by_draft(CONVERSATION_ID) is None
    assert list(tmp_path.iterdir()) == []


def test_upload_is_rejected_outside_active_harian_photo_step(tmp_path: Path) -> None:
    service, repository = _service(
        tmp_path,
        state=ConversationState.HARIAN_ASK_ADDRESS,
    )

    with pytest.raises(ApplicationError) as error:
        service.upload(
            CONVERSATION_ID,
            original_filename="foto.png",
            declared_content_type="image/png",
            content=b"\x89PNG\r\n\x1a\ncontent",
        )

    assert error.value.status_code == 409
    assert repository.find_by_draft(CONVERSATION_ID) is None

"""Safe optional photo attachments for Harian reservation drafts."""

from app.modules.attachment.domain import Attachment
from app.modules.attachment.service import AttachmentService

__all__ = ["Attachment", "AttachmentService"]

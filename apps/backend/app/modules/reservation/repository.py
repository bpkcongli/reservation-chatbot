"""Transactional finalization of a validated reservation draft."""

from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.attachment.models import AttachmentRecord
from app.modules.catalog.domain import ServiceType
from app.modules.catalog.models import ServiceRecord
from app.modules.conversation.domain import ConversationContext
from app.modules.conversation.ids import generate_ulid
from app.modules.conversation.models import ConversationRecord, ReservationDraftRecord
from app.modules.reservation.models import ReservationRecord
from app.modules.ticketing.domain import EmailDelivery, TicketView
from app.modules.ticketing.repository import SqlAlchemyTicketRepository
from app.modules.ticketing.service import TicketNumberExhaustedError, TicketService
from app.shared.errors import ApplicationError

IdFactory = Callable[[datetime], str]


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


class SqlAlchemyReservationFinalizer:
    """Stage reservation, attachment link, draft status, and ticket in one session."""

    def __init__(
        self,
        session: Session,
        *,
        id_factory: IdFactory = generate_ulid,
    ) -> None:
        self._session = session
        self._id_factory = id_factory

    def finalize(
        self,
        context: ConversationContext,
        *,
        created_at: datetime,
    ) -> TicketView:
        conversation = self._session.scalar(
            select(ConversationRecord)
            .where(ConversationRecord.id == context.conversation_id)
            .with_for_update()
        )
        if conversation is None:
            raise ApplicationError(
                code="CONVERSATION_NOT_FOUND",
                message="Maaf, sesi percakapan tersebut belum ditemukan.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        draft = self._session.scalar(
            select(ReservationDraftRecord)
            .where(ReservationDraftRecord.conversation_id == context.conversation_id)
            .with_for_update()
        )
        if draft is None:
            raise ApplicationError(
                code="RESERVATION_DRAFT_NOT_FOUND",
                message="Maaf, draft reservasi belum ditemukan. Silakan mulai reservasi kembali.",
                status_code=status.HTTP_409_CONFLICT,
            )

        existing_reservation = self._session.scalar(
            select(ReservationRecord.id).where(ReservationRecord.reservation_draft_id == draft.id)
        )
        if existing_reservation is not None or draft.status != "ACTIVE":
            raise ApplicationError(
                code="RESERVATION_ALREADY_FINALIZED",
                message="Draft reservasi ini sudah pernah dikonfirmasi.",
                status_code=status.HTTP_409_CONFLICT,
            )
        if (
            draft.slots != context.collected_slots
            or draft.price_snapshot != context.price_breakdown
        ):
            raise ApplicationError(
                code="RESERVATION_DRAFT_CHANGED",
                message=(
                    "Data reservasi telah berubah. Mohon periksa kembali ringkasan "
                    "sebelum mengonfirmasi."
                ),
                status_code=status.HTTP_409_CONFLICT,
                retryable=True,
            )
        if context.reservation_summary is None or context.price_breakdown is None:
            raise ApplicationError(
                code="RESERVATION_SNAPSHOT_MISSING",
                message="Ringkasan atau estimasi reservasi belum tersedia.",
                status_code=status.HTTP_409_CONFLICT,
            )

        service_type = str(context.collected_slots.get("service_type", ""))
        service = self._session.scalar(
            select(ServiceRecord).where(ServiceRecord.code == service_type)
        )
        if service is None:
            raise ApplicationError(
                code="RESERVATION_SERVICE_UNAVAILABLE",
                message="Layanan reservasi yang dipilih sedang belum tersedia.",
                status_code=status.HTTP_409_CONFLICT,
                field="service_type",
            )

        customer_id = context.collected_slots.get("customer_id")
        phone_number = context.collected_slots.get("phone_number")
        estimated_price = context.price_breakdown.get("estimated_price")
        pricing_version = context.price_breakdown.get("pricing_version")
        if (
            not isinstance(customer_id, str)
            or not isinstance(phone_number, str)
            or isinstance(estimated_price, bool)
            or not isinstance(estimated_price, int)
            or pricing_version != "pricing-v1"
        ):
            raise ApplicationError(
                code="RESERVATION_SNAPSHOT_INVALID",
                message="Data reservasi belum lengkap untuk dikonfirmasi.",
                status_code=status.HTTP_409_CONFLICT,
            )

        reservation_id = self._id_factory(created_at)
        excluded_details = {
            "attachment",
            "customer_id",
            "phone_number",
            "problem_photo",
            "service_type",
        }
        details = {
            key: value
            for key, value in context.collected_slots.items()
            if key not in excluded_details
        }
        details.update(
            {
                "service_type": service_type,
                "pricing_version": pricing_version,
                "price_breakdown": dict(context.price_breakdown),
            }
        )
        attachment_id = context.collected_slots.get("problem_photo")
        if attachment_id is not None:
            details["attachment_id"] = attachment_id

        reservation = ReservationRecord(
            id=reservation_id,
            reservation_draft_id=draft.id,
            service_id=service.id,
            customer_id=customer_id,
            phone_number_encrypted=phone_number,
            details=details,
            estimated_price=estimated_price,
            created_at=_naive_utc(created_at),
        )
        self._session.add(reservation)
        self._session.flush((reservation,))

        if attachment_id is not None:
            attachment = self._session.scalar(
                select(AttachmentRecord)
                .where(
                    AttachmentRecord.id == str(attachment_id),
                    AttachmentRecord.reservation_draft_id == draft.id,
                )
                .with_for_update()
            )
            if attachment is None or attachment.reservation_id is not None:
                raise ApplicationError(
                    code="ATTACHMENT_FINALIZATION_CONFLICT",
                    message="Foto draft tidak dapat dikaitkan ke reservasi.",
                    status_code=status.HTTP_409_CONFLICT,
                    field="attachment",
                )
            attachment.reservation_id = reservation_id

        try:
            ticket = TicketService(
                SqlAlchemyTicketRepository(self._session),
                id_factory=self._id_factory,
            ).issue(reservation_id, created_at=created_at)
        except TicketNumberExhaustedError as error:
            raise ApplicationError(
                code="TICKET_NUMBER_UNAVAILABLE",
                message="Maaf, nomor tiket belum dapat dibuat. Silakan coba lagi.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                retryable=True,
            ) from error

        draft.status = "CONFIRMED"
        budget = context.collected_slots.get("budget")
        return TicketView(
            ticket_number=ticket.ticket_number,
            service_type=ServiceType(service_type),
            status=ticket.status,
            pricing_version=pricing_version,
            estimated_price=estimated_price,
            budget=budget if isinstance(budget, int) and not isinstance(budget, bool) else None,
            created_at=created_at,
            email_delivery=EmailDelivery.NOT_IMPLEMENTED,
        )

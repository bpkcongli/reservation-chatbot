"""Reservation slot priority, validation, and customer-facing prompts."""

from dataclasses import dataclass
from datetime import date

from app.modules.catalog.domain import SURVEY_TIMES
from app.modules.conversation.domain import (
    ConversationContext,
    ConversationState,
    QuickReply,
)
from app.modules.conversation.extractors import (
    extract_budget,
    extract_building_type,
    extract_customer_id,
    extract_dates,
    extract_phone_number,
    extract_specialization,
    extract_survey_time,
    extract_work_session,
    extract_worker_count,
)

BORONGAN_FLOW = (
    ("customer_id", ConversationState.BORONGAN_ASK_CUSTOMER_ID),
    ("phone_number", ConversationState.BORONGAN_ASK_PHONE),
    ("building_type", ConversationState.BORONGAN_ASK_BUILDING),
    ("survey_address", ConversationState.BORONGAN_ASK_ADDRESS),
    ("survey_date", ConversationState.BORONGAN_ASK_SURVEY_DATE),
    ("survey_time", ConversationState.BORONGAN_ASK_SURVEY_TIME),
    ("budget", ConversationState.BORONGAN_ASK_BUDGET),
)
HARIAN_FLOW = (
    ("customer_id", ConversationState.HARIAN_ASK_CUSTOMER_ID),
    ("phone_number", ConversationState.HARIAN_ASK_PHONE),
    ("specialization", ConversationState.HARIAN_ASK_SPECIALIZATION),
    ("problem_description", ConversationState.HARIAN_ASK_DESCRIPTION),
    ("worker_count", ConversationState.HARIAN_ASK_WORKER_COUNT),
    ("start_date", ConversationState.HARIAN_ASK_START_DATE),
    ("end_date", ConversationState.HARIAN_ASK_END_DATE),
    ("work_session", ConversationState.HARIAN_ASK_SESSION),
    ("problem_photo", ConversationState.HARIAN_ASK_PHOTO),
    ("work_address", ConversationState.HARIAN_ASK_ADDRESS),
)

CONFIRMATION_REPLIES = (
    QuickReply(label="Ya, konfirmasi", value="ya"),
    QuickReply(label="Ubah data", value="ubah"),
    QuickReply(label="Batalkan", value="batal"),
)

_EDIT_LABELS = {
    "customer_id": "ID pelanggan",
    "phone_number": "nomor telepon",
    "building_type": "jenis bangunan",
    "survey_address": "alamat survei",
    "survey_date": "tanggal survei",
    "survey_time": "waktu survei",
    "budget": "budget",
    "specialization": "spesialisasi",
    "problem_description": "deskripsi pekerjaan",
    "worker_count": "jumlah tukang",
    "start_date": "tanggal mulai",
    "end_date": "tanggal selesai",
    "work_session": "sesi kerja",
    "problem_photo": "foto kendala",
    "work_address": "alamat pekerjaan",
}

_EDIT_ALIASES = {
    "id": "customer_id",
    "id pelanggan": "customer_id",
    "customer id": "customer_id",
    "nomor telepon": "phone_number",
    "telepon": "phone_number",
    "kontak": "phone_number",
    "jenis bangunan": "building_type",
    "bangunan": "building_type",
    "alamat survei": "survey_address",
    "tanggal survei": "survey_date",
    "waktu survei": "survey_time",
    "jam survei": "survey_time",
    "budget": "budget",
    "anggaran": "budget",
    "spesialisasi": "specialization",
    "deskripsi": "problem_description",
    "deskripsi pekerjaan": "problem_description",
    "kendala": "problem_description",
    "jumlah tukang": "worker_count",
    "jumlah pekerja": "worker_count",
    "tanggal mulai": "start_date",
    "tanggal selesai": "end_date",
    "sesi": "work_session",
    "sesi kerja": "work_session",
    "foto": "problem_photo",
    "foto kendala": "problem_photo",
    "alamat": "work_address",
    "alamat pekerjaan": "work_address",
}

_PROMPTS: dict[ConversationState, str] = {
    ConversationState.BORONGAN_ASK_CUSTOMER_ID: (
        "Untuk memulai Jasa Borongan, mohon masukkan ID pelanggan yang terdiri dari "
        "tepat 10 digit angka, misalnya 0123456789."
    ),
    ConversationState.BORONGAN_ASK_PHONE: (
        "ID pelanggan sudah kami catat. Mohon masukkan nomor telepon Indonesia yang "
        "dapat dihubungi, misalnya 081234567890."
    ),
    ConversationState.BORONGAN_ASK_BUILDING: (
        "Baik, nomor kontak sudah tersimpan. Silakan pilih jenis bangunan: rumah, "
        "apartemen, atau ruko."
    ),
    ConversationState.BORONGAN_ASK_ADDRESS: (
        "Jenis bangunan sudah dicatat. Mohon tuliskan alamat survei secara lengkap "
        "dalam 10-300 karakter."
    ),
    ConversationState.BORONGAN_ASK_SURVEY_DATE: (
        "Alamat survei sudah kami catat. Silakan masukkan tanggal survei hari ini "
        "atau setelahnya, misalnya 2 Agustus 2026."
    ),
    ConversationState.BORONGAN_ASK_SURVEY_TIME: (
        "Tanggal survei sudah dicatat. Mohon pilih waktu survei dalam format HH:MM, misalnya 09:00."
    ),
    ConversationState.BORONGAN_ASK_BUDGET: (
        "Jadwal survei sudah kami catat. Mohon masukkan perkiraan budget dalam rupiah, "
        "misalnya Rp20.000.000 atau 20 juta."
    ),
    ConversationState.HARIAN_ASK_CUSTOMER_ID: (
        "Untuk memulai reservasi Tukang Harian, mohon masukkan ID pelanggan yang "
        "terdiri dari tepat 10 digit angka, misalnya 0123456789."
    ),
    ConversationState.HARIAN_ASK_PHONE: (
        "ID pelanggan sudah kami catat. Mohon masukkan nomor telepon Indonesia yang "
        "dapat dihubungi, misalnya 081234567890."
    ),
    ConversationState.HARIAN_ASK_SPECIALIZATION: (
        "Nomor kontak sudah tersimpan. Silakan pilih spesialisasi: cat, genteng, AC, "
        "listrik, keramik, atau pipa."
    ),
    ConversationState.HARIAN_ASK_DESCRIPTION: (
        "Spesialisasi sudah dicatat. Mohon jelaskan kebutuhan atau kendalanya dalam "
        "10-500 karakter."
    ),
    ConversationState.HARIAN_ASK_WORKER_COUNT: (
        "Deskripsi pekerjaan sudah kami catat. Berapa tukang yang dibutuhkan? "
        "Masukkan 1-20 orang, misalnya 2 orang."
    ),
    ConversationState.HARIAN_ASK_START_DATE: (
        "Jumlah tukang sudah dicatat. Silakan masukkan tanggal mulai hari ini atau "
        "setelahnya, misalnya 2 Agustus 2026."
    ),
    ConversationState.HARIAN_ASK_END_DATE: (
        "Tanggal mulai sudah dicatat. Silakan masukkan tanggal selesai yang sama "
        "dengan atau setelah tanggal mulai, misalnya 3 Agustus 2026."
    ),
    ConversationState.HARIAN_ASK_SESSION: (
        "Rentang tanggal sudah kami catat. Silakan pilih sesi kerja: sehari penuh, pagi, atau sore."
    ),
    ConversationState.HARIAN_ASK_PHOTO: (
        "Sesi kerja sudah dicatat. Foto kendala bersifat opsional. Silakan unggah "
        "melalui tombol lampiran atau ketik “lewati” untuk melanjutkan."
    ),
    ConversationState.HARIAN_ASK_ADDRESS: (
        "Baik, sekarang mohon tuliskan alamat pekerjaan secara lengkap dalam 10-300 karakter."
    ),
}

_STATE_SLOT = {
    state: slot
    for slot, state in (
        *BORONGAN_FLOW,
        *HARIAN_FLOW,
    )
}

_SLOT_REPLIES: dict[ConversationState, tuple[QuickReply, ...]] = {
    ConversationState.BORONGAN_ASK_BUILDING: (
        QuickReply(label="Rumah", value="rumah"),
        QuickReply(label="Apartemen", value="apartemen"),
        QuickReply(label="Ruko", value="ruko"),
    ),
    ConversationState.HARIAN_ASK_SPECIALIZATION: tuple(
        QuickReply(label=label, value=value)
        for label, value in (
            ("Spesialis Cat", "cat"),
            ("Spesialis Genteng", "genteng"),
            ("Spesialis AC", "ac"),
            ("Spesialis Listrik", "listrik"),
            ("Spesialis Keramik", "keramik"),
            ("Spesialis Pipa", "pipa"),
        )
    ),
    ConversationState.HARIAN_ASK_SESSION: (
        QuickReply(label="Sehari penuh", value="sehari penuh"),
        QuickReply(label="Pagi", value="pagi"),
        QuickReply(label="Sore", value="sore"),
    ),
    ConversationState.HARIAN_ASK_PHOTO: (QuickReply(label="Lewati foto", value="lewati"),),
}


@dataclass(frozen=True, slots=True)
class DialogDecision:
    """Pure result of one reservation dialog turn."""

    state: ConversationState
    text: str
    quick_replies: tuple[QuickReply, ...]
    collected_slots: dict[str, object]
    validation_field: str | None = None


def prompt_for_state(state: ConversationState) -> str | None:
    """Return the current slot prompt when the state collects a value."""

    return _PROMPTS.get(state)


def replies_for_state(state: ConversationState) -> tuple[QuickReply, ...]:
    """Return catalog-like shortcuts for a slot state."""

    return _SLOT_REPLIES.get(state, ())


def is_reservation_state(state: ConversationState) -> bool:
    """Whether a state belongs to active slot collection."""

    return state in _STATE_SLOT


def confirmation_prompt(service_type: str) -> str:
    service_label = "Jasa Borongan" if service_type == "borongan" else "Tukang Harian"
    return (
        f"Terima kasih, seluruh data {service_label} sudah lengkap. "
        "Silakan periksa ringkasan dan estimasi harga, lalu pilih konfirmasi, "
        "ubah data, atau batalkan."
    )


def edit_replies(service_type: str) -> tuple[QuickReply, ...]:
    flow = BORONGAN_FLOW if service_type == "borongan" else HARIAN_FLOW
    return tuple(QuickReply(label=_EDIT_LABELS[field], value=f"ubah:{field}") for field, _ in flow)


def edit_prompt(service_type: str) -> str:
    options = ", ".join(reply.label for reply in edit_replies(service_type))
    return f"Baik, data mana yang ingin diubah? Pilih salah satu: {options}."


def parse_edit_field(text: str, service_type: str) -> str | None:
    normalized = " ".join(text.casefold().strip().replace("_", " ").split())
    if normalized.startswith("ubah:"):
        candidate = normalized.removeprefix("ubah:").replace(" ", "_")
    else:
        candidate = normalized
        for prefix in ("ubah ", "edit "):
            if candidate.startswith(prefix):
                candidate = candidate.removeprefix(prefix)
                break
        candidate = _EDIT_ALIASES.get(candidate, candidate.replace(" ", "_"))

    flow = BORONGAN_FLOW if service_type == "borongan" else HARIAN_FLOW
    editable_fields = {field for field, _ in flow}
    return candidate if candidate in editable_fields else None


def begin_slot_edit(context: ConversationContext, field: str) -> DialogDecision:
    service_type = str(context.collected_slots.get("service_type", ""))
    flow = BORONGAN_FLOW if service_type == "borongan" else HARIAN_FLOW
    state_by_field = dict(flow)
    if field not in state_by_field:
        raise ValueError(f"Field {field!r} is not editable for {service_type!r}.")

    slots = dict(context.collected_slots)
    slots.pop(field, None)
    if field == "start_date":
        slots.pop("end_date", None)
    state = state_by_field[field]
    return DialogDecision(
        state=state,
        text=f"Baik, mari perbarui {_EDIT_LABELS[field]}. {_PROMPTS[state]}",
        quick_replies=replies_for_state(state),
        collected_slots=slots,
    )


def start_reservation(service_type: str) -> DialogDecision:
    """Start one service flow with a clean draft."""

    if service_type == "borongan":
        state = ConversationState.BORONGAN_ASK_CUSTOMER_ID
    else:
        state = ConversationState.HARIAN_ASK_CUSTOMER_ID
    return DialogDecision(
        state=state,
        text=_PROMPTS[state],
        quick_replies=replies_for_state(state),
        collected_slots={"service_type": service_type},
    )


def _feedback(field: str, reason: str, correct_format: str) -> str:
    return (
        f"Maaf, {reason}. Format yang dapat digunakan: {correct_format}. "
        "Mohon masukkan kembali agar kami dapat melanjutkan."
    )


def _invalid(
    context: ConversationContext,
    *,
    field: str,
    reason: str,
    correct_format: str,
) -> DialogDecision:
    return DialogDecision(
        state=context.state,
        text=_feedback(field, reason, correct_format),
        quick_replies=replies_for_state(context.state),
        collected_slots=dict(context.collected_slots),
        validation_field=field,
    )


def _next_missing(
    flow: tuple[tuple[str, ConversationState], ...],
    slots: dict[str, object],
) -> ConversationState | None:
    for slot, state in flow:
        if slot not in slots:
            return state
    return None


def _collect_structured_candidates(
    context: ConversationContext,
    text: str,
    *,
    today: date,
) -> dict[str, object]:
    state = context.state
    slots: dict[str, object] = {}
    is_borongan = state.name.startswith("BORONGAN_")

    if state in {
        ConversationState.BORONGAN_ASK_CUSTOMER_ID,
        ConversationState.HARIAN_ASK_CUSTOMER_ID,
    }:
        customer_id = extract_customer_id(text)
        if customer_id is not None:
            slots["customer_id"] = customer_id

    if state in {
        ConversationState.BORONGAN_ASK_PHONE,
        ConversationState.HARIAN_ASK_PHONE,
    }:
        phone = extract_phone_number(text)
        if phone is not None:
            slots["phone_number"] = phone

    if is_borongan:
        building = extract_building_type(text)
        if building is not None:
            slots["building_type"] = building

        dates = extract_dates(text, reference_date=today)
        if dates:
            slots["survey_date"] = dates[0].isoformat()

        if state is ConversationState.BORONGAN_ASK_SURVEY_TIME or any(
            marker in text.casefold() for marker in ("jam", ":")
        ):
            survey_time = extract_survey_time(text)
            if survey_time is not None:
                slots["survey_time"] = survey_time

        if state is ConversationState.BORONGAN_ASK_BUDGET or any(
            marker in text.casefold() for marker in ("rp", "ribu", "juta", "budget", "anggaran")
        ):
            budget = extract_budget(text)
            if budget is not None:
                slots["budget"] = budget
    else:
        specialization = extract_specialization(text)
        if specialization is not None:
            slots["specialization"] = specialization

        worker_count = extract_worker_count(text)
        if worker_count is not None:
            slots["worker_count"] = worker_count

        dates = extract_dates(text, reference_date=today)
        if len(dates) >= 2:
            slots["start_date"] = dates[0].isoformat()
            slots["end_date"] = dates[1].isoformat()
        elif dates:
            target = "end_date" if state is ConversationState.HARIAN_ASK_END_DATE else "start_date"
            slots[target] = dates[0].isoformat()

        session = extract_work_session(text)
        if session is not None:
            slots["work_session"] = session

    return slots


def _validate_current_slot(
    context: ConversationContext,
    text: str,
    candidates: dict[str, object],
    *,
    today: date,
) -> tuple[str, str, str] | None:
    field = _STATE_SLOT[context.state]
    value = candidates.get(field)

    if field == "customer_id" and value is None:
        return field, "ID pelanggan belum terdiri dari tepat 10 digit angka", "0123456789"
    if field == "phone_number" and value is None:
        return (
            field,
            "nomor teleponnya belum sesuai sebagai nomor Indonesia",
            "081234567890",
        )
    if field == "building_type" and value is None:
        return field, "jenis bangunannya belum dikenali", "rumah, apartemen, atau ruko"
    if field == "specialization" and value is None:
        return (
            field,
            "spesialisasinya belum tersedia dalam pilihan layanan",
            "cat, genteng, AC, listrik, keramik, atau pipa",
        )
    if field == "worker_count" and (not isinstance(value, int) or not 1 <= value <= 20):
        return field, "jumlah tukangnya perlu berada pada rentang 1-20 orang", "2 orang"
    if field in {"survey_date", "start_date", "end_date"}:
        if value is None:
            return field, "tanggalnya belum dapat dikenali", "2 Agustus 2026"
        parsed = date.fromisoformat(str(value))
        if parsed < today:
            return (
                field,
                "tanggal tersebut sudah berlalu dan belum dapat digunakan",
                "tanggal hari ini atau setelahnya, misalnya 2 Agustus 2026",
            )
    if field == "survey_time":
        if value is None:
            return field, "waktu surveinya belum dapat dikenali", "09:00"
        if value not in SURVEY_TIMES:
            return field, "waktu surveinya belum termasuk slot yang tersedia", "09:00 atau 13:00"
    if field == "budget" and (not isinstance(value, int) or value < 1):
        return (
            field,
            "nominal budgetnya perlu berupa bilangan rupiah positif",
            "Rp20.000.000 atau 20 juta",
        )
    if field == "work_session" and value is None:
        return field, "sesi kerjanya belum dikenali", "sehari penuh, pagi, atau sore"
    if field == "problem_photo":
        normalized = " ".join(text.casefold().strip().split())
        if normalized not in {"lewati", "tanpa foto", "skip"}:
            return (
                field,
                "foto perlu diunggah melalui tombol lampiran atau dapat dilewati",
                "ketik “lewati”",
            )
    return None


def process_reservation_turn(
    context: ConversationContext,
    text: str,
    *,
    today: date,
) -> DialogDecision:
    """Extract valid values, preserve priority, and select the next missing slot."""

    candidates = _collect_structured_candidates(context, text, today=today)
    field = _STATE_SLOT[context.state]
    stripped = text.strip()

    if field == "survey_address":
        if not 10 <= len(stripped) <= 300:
            return _invalid(
                context,
                field=field,
                reason="alamat surveinya perlu berisi 10-300 karakter",
                correct_format="contoh Jalan Melati No. 10, Jakarta",
            )
        candidates[field] = stripped
    elif field == "problem_description":
        if not 10 <= len(stripped) <= 500:
            return _invalid(
                context,
                field=field,
                reason="deskripsi kebutuhannya perlu berisi 10-500 karakter",
                correct_format="contoh Pipa dapur bocor sejak kemarin",
            )
        candidates[field] = stripped
    elif field == "work_address":
        if not 10 <= len(stripped) <= 300:
            return _invalid(
                context,
                field=field,
                reason="alamat pekerjaannya perlu berisi 10-300 karakter",
                correct_format="contoh Jalan Melati No. 10, Jakarta",
            )
        candidates[field] = stripped
    elif field == "problem_photo":
        normalized = " ".join(text.casefold().strip().split())
        if normalized in {"lewati", "tanpa foto", "skip"}:
            candidates[field] = None

    validation = _validate_current_slot(context, text, candidates, today=today)
    if validation is not None:
        invalid_field, reason, correct_format = validation
        return _invalid(
            context,
            field=invalid_field,
            reason=reason,
            correct_format=correct_format,
        )

    merged = {**context.collected_slots, **candidates}
    start_date = merged.get("start_date")
    end_date = merged.get("end_date")
    if (
        start_date is not None
        and end_date is not None
        and date.fromisoformat(str(end_date)) < date.fromisoformat(str(start_date))
    ):
        return _invalid(
            context,
            field="end_date",
            reason="tanggal selesai belum boleh lebih awal dari tanggal mulai",
            correct_format="tanggal yang sama dengan atau setelah tanggal mulai",
        )

    for date_field in ("survey_date", "start_date", "end_date"):
        candidate_date = candidates.get(date_field)
        if candidate_date is not None and date.fromisoformat(str(candidate_date)) < today:
            return _invalid(
                context,
                field=date_field,
                reason="tanggal tersebut sudah berlalu dan belum dapat digunakan",
                correct_format="tanggal hari ini atau setelahnya, misalnya 2 Agustus 2026",
            )

    service_type = str(context.collected_slots.get("service_type", ""))
    flow = BORONGAN_FLOW if service_type == "borongan" else HARIAN_FLOW
    next_state = _next_missing(flow, merged)
    if next_state is not None:
        return DialogDecision(
            state=next_state,
            text=_PROMPTS[next_state],
            quick_replies=replies_for_state(next_state),
            collected_slots=merged,
        )

    final_state = (
        ConversationState.CONFIRM_RESERVATION
        if service_type == "borongan"
        else ConversationState.CALCULATE_PRICE
    )
    final_text = (
        "Terima kasih, seluruh data Jasa Borongan sudah lengkap dan siap ditampilkan "
        "pada ringkasan konfirmasi."
        if service_type == "borongan"
        else (
            "Terima kasih, seluruh data Tukang Harian sudah lengkap dan siap digunakan "
            "untuk menghitung estimasi harga."
        )
    )
    return DialogDecision(
        state=final_state,
        text=final_text,
        quick_replies=(),
        collected_slots=merged,
    )

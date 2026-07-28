"""Canonical intent taxonomy for the FAQ intent classifier."""

from dataclasses import dataclass
from enum import StrEnum


class Intent(StrEnum):
    """Supported user intents outside an active slot-filling state."""

    GREETING = "greeting"
    SERVICE_OVERVIEW = "service_overview"
    BORONGAN_INFO = "borongan_info"
    HARIAN_INFO = "harian_info"
    PRICING_INFO = "pricing_info"
    START_RESERVATION = "start_reservation"
    RESERVATION_STATUS = "reservation_status"
    GOODBYE = "goodbye"


@dataclass(frozen=True, slots=True)
class IntentDefinition:
    """Labeling contract and target distribution for an intent."""

    intent: Intent
    target_count: int
    purpose: str
    include_when: str
    exclude_when: str


INTENT_TAXONOMY: tuple[IntentDefinition, ...] = (
    IntentDefinition(
        intent=Intent.GREETING,
        target_count=25,
        purpose="Membuka atau memulai percakapan.",
        include_when="Tujuan utamanya menyapa bot, termasuk sapaan berbasis waktu.",
        exclude_when="Sapaan hanya menjadi pembuka sebelum permintaan layanan yang jelas.",
    ),
    IntentDefinition(
        intent=Intent.SERVICE_OVERVIEW,
        target_count=30,
        purpose="Memahami layanan tukang yang tersedia secara umum.",
        include_when="Pengguna meminta daftar, gambaran, atau perbedaan layanan.",
        exclude_when="Pertanyaan sudah khusus tentang Borongan, Harian, atau harga.",
    ),
    IntentDefinition(
        intent=Intent.BORONGAN_INFO,
        target_count=35,
        purpose="Memahami cakupan, survei, dan proses Jasa Borongan.",
        include_when="Fokus pada cara kerja, cakupan, bangunan, atau survei Borongan.",
        exclude_when="Fokus utama pada nominal biaya atau meminta langsung dipesankan.",
    ),
    IntentDefinition(
        intent=Intent.HARIAN_INFO,
        target_count=35,
        purpose="Memahami cakupan dan spesialisasi Tukang Harian.",
        include_when="Fokus pada spesialisasi, sesi, jumlah, atau cara kerja Harian.",
        exclude_when="Fokus utama pada tarif per hari atau meminta langsung dipesankan.",
    ),
    IntentDefinition(
        intent=Intent.PRICING_INFO,
        target_count=30,
        purpose="Memahami tarif, estimasi, komponen harga, atau hubungan budget.",
        include_when="Jawaban yang dicari terutama berupa harga atau cara perhitungannya.",
        exclude_when="Nominal diberikan sebagai slot ketika reservasi sedang berlangsung.",
    ),
    IntentDefinition(
        intent=Intent.START_RESERVATION,
        target_count=35,
        purpose="Memulai pemesanan Jasa Borongan atau Tukang Harian.",
        include_when="Pengguna meminta booking, pesan, reservasi, atau penjadwalan.",
        exclude_when="Pengguna hanya bertanya cara reservasi tanpa meminta memulai.",
    ),
    IntentDefinition(
        intent=Intent.RESERVATION_STATUS,
        target_count=25,
        purpose="Memeriksa tiket atau progres reservasi yang sudah dibuat.",
        include_when="Pengguna ingin cek status, tiket, atau kelanjutan pesanan.",
        exclude_when="Pengguna ingin membuat reservasi baru atau menanyakan layanan.",
    ),
    IntentDefinition(
        intent=Intent.GOODBYE,
        target_count=25,
        purpose="Menutup atau mengakhiri percakapan.",
        include_when="Tujuan utamanya pamit, mengakhiri chat, atau menyatakan cukup.",
        exclude_when="Ucapan terima kasih masih diikuti pertanyaan atau permintaan.",
    ),
)

INTENT_BY_LABEL = {definition.intent.value: definition for definition in INTENT_TAXONOMY}
EXPECTED_DISTRIBUTION = {
    definition.intent.value: definition.target_count for definition in INTENT_TAXONOMY
}
TOTAL_UTTERANCES = sum(EXPECTED_DISTRIBUTION.values())

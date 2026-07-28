"""Customer-service copy and quick replies for recognized FAQ intents."""

from dataclasses import dataclass

from app.modules.conversation.domain import ConversationState, QuickReply
from app.modules.nlp.taxonomy import Intent

WELCOME_TEXT = (
    "Halo! Selamat datang di layanan reservasi tukang. Saya dapat membantu Anda "
    "mencari informasi layanan atau memulai reservasi. Silakan pilih kebutuhan Anda."
)
WELCOME_REPLIES = (
    QuickReply(label="Tanya-tanya dulu layanan tukang", value="info"),
    QuickReply(label="Langsung reservasi", value="reservation"),
)

INFO_MENU_TEXT = (
    "Baik, silakan tanyakan informasi tentang Jasa Borongan, Tukang Harian, harga "
    "demo, reservasi, atau status tiket."
)
INFO_MENU_REPLIES = (
    QuickReply(label="Jasa Borongan", value="borongan"),
    QuickReply(label="Tukang Harian", value="harian"),
    QuickReply(label="Harga", value="harga"),
    QuickReply(label="Mulai reservasi", value="reservation"),
)

FALLBACK_TEXT = (
    "Maaf, saya belum yakin memahami pertanyaan Anda. Anda ingin mengetahui Jasa "
    "Borongan, Tukang Harian, harga, atau mulai reservasi?"
)
FALLBACK_REPLIES = INFO_MENU_REPLIES

SELECT_SERVICE_TEXT = (
    "Baik, mari mulai reservasi. Silakan pilih layanan Jasa Borongan atau Tukang "
    "Harian agar saya dapat memandu langkah berikutnya."
)
SELECT_SERVICE_REPLIES = (
    QuickReply(label="Jasa Borongan", value="borongan"),
    QuickReply(label="Tukang Harian", value="harian"),
)

TICKET_LOOKUP_TEXT = (
    "Baik, saya dapat membantu memeriksa status reservasi. Mohon masukkan nomor "
    "tiket dengan format seperti TKT-20260728-AB12CD."
)


@dataclass(frozen=True, slots=True)
class FaqAnswer:
    """Response selected for one confidently recognized intent."""

    text: str
    state: ConversationState
    quick_replies: tuple[QuickReply, ...]


FAQ_ANSWERS: dict[Intent, FaqAnswer] = {
    Intent.GREETING: FaqAnswer(
        text=(
            "Halo! Senang dapat membantu Anda. Anda dapat bertanya tentang layanan "
            "tukang atau langsung memulai reservasi."
        ),
        state=ConversationState.INFO_MODE,
        quick_replies=WELCOME_REPLIES,
    ),
    Intent.SERVICE_OVERVIEW: FaqAnswer(
        text=(
            "Kami menyediakan dua layanan utama: Jasa Borongan untuk pekerjaan "
            "berbasis proyek yang diawali permintaan survei, serta Tukang Harian "
            "untuk pekerjaan berdasarkan spesialisasi, tanggal, jumlah pekerja, "
            "dan sesi kerja."
        ),
        state=ConversationState.INFO_MODE,
        quick_replies=INFO_MENU_REPLIES,
    ),
    Intent.BORONGAN_INFO: FaqAnswer(
        text=(
            "Jasa Borongan cocok untuk pekerjaan berbasis proyek pada rumah, "
            "apartemen, atau ruko. Anda mengajukan lokasi, jadwal survei, dan "
            "budget; pengajuan tersebut belum menjamin jadwal atau pekerjaan "
            "langsung dimulai."
        ),
        state=ConversationState.INFO_MODE,
        quick_replies=INFO_MENU_REPLIES,
    ),
    Intent.HARIAN_INFO: FaqAnswer(
        text=(
            "Tukang Harian tersedia untuk spesialisasi cat, genteng, AC, listrik, "
            "keramik, dan pipa. Anda dapat memilih jumlah pekerja, rentang tanggal, "
            "serta sesi sehari penuh, pagi, atau sore."
        ),
        state=ConversationState.INFO_MODE,
        quick_replies=INFO_MENU_REPLIES,
    ),
    Intent.PRICING_INFO: FaqAnswer(
        text=(
            "Estimasi menggunakan harga tetap demonstrasi pricing-v1 dari backend. "
            "Tukang Harian dihitung dari spesialisasi, sesi, jumlah pekerja, dan "
            "jumlah hari; Borongan memakai harga dasar jenis bangunan ditambah "
            "biaya survei dan administrasi. Nilai ini bukan harga pasar."
        ),
        state=ConversationState.INFO_MODE,
        quick_replies=INFO_MENU_REPLIES,
    ),
    Intent.START_RESERVATION: FaqAnswer(
        text=SELECT_SERVICE_TEXT,
        state=ConversationState.SELECT_SERVICE,
        quick_replies=SELECT_SERVICE_REPLIES,
    ),
    Intent.RESERVATION_STATUS: FaqAnswer(
        text=TICKET_LOOKUP_TEXT,
        state=ConversationState.TICKET_LOOKUP,
        quick_replies=(),
    ),
    Intent.GOODBYE: FaqAnswer(
        text=(
            "Baik, terima kasih sudah menghubungi kami. Jika masih ada yang ingin "
            "ditanyakan, saya siap membantu Anda kembali."
        ),
        state=ConversationState.INFO_MODE,
        quick_replies=WELCOME_REPLIES,
    ),
}

DIRECT_INTENTS: dict[str, Intent] = {
    "borongan": Intent.BORONGAN_INFO,
    "harian": Intent.HARIAN_INFO,
    "harga": Intent.PRICING_INFO,
    "layanan": Intent.SERVICE_OVERVIEW,
    "reservation": Intent.START_RESERVATION,
    "reservasi": Intent.START_RESERVATION,
    "status": Intent.RESERVATION_STATUS,
}

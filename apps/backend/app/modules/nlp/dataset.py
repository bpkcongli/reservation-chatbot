"""Deterministic source and CSV generator for the intent dataset."""

import csv
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from app.modules.nlp.taxonomy import INTENT_TAXONOMY, Intent

DATASET_SOURCE = "synthetic_manual"
CSV_FIELDS = ("id", "text", "intent", "source")


@dataclass(frozen=True, slots=True)
class UtteranceRecord:
    """One traceable utterance in the raw dataset."""

    id: str
    text: str
    intent: str
    source: str = DATASET_SOURCE


# These are deliberately explicit, manually authored utterances. The generator only
# assigns stable IDs and serializes them; it does not inflate the dataset by randomly
# combining interchangeable templates.
UTTERANCES: dict[Intent, tuple[str, ...]] = {
    Intent.GREETING: (
        "Halo",
        "Hai kak",
        "Selamat pagi",
        "Selamat siang, admin",
        "Selamat sore semuanya",
        "Malam min",
        "Permisi",
        "Halo, ada yang bisa bantu?",
        "Hai bot tukang",
        "Pagi kak, semoga sehat",
        "Assalamualaikum",
        "Apa kabar admin?",
        "Halo halo",
        "Tes, apakah chat ini aktif?",
        "Hai, saya baru datang",
        "Min, boleh tanya?",
        "Selamat malam",
        "Hello, ada orang?",
        "Permisi kak admin",
        "Halo, saya mau ngobrol",
        "Pagi semuanya",
        "Hai chatbot",
        "Adminnya online?",
        "Salam kenal ya",
        "Woi halo min",
    ),
    Intent.SERVICE_OVERVIEW: (
        "Layanan apa saja yang tersedia?",
        "Bisa bantu pekerjaan tukang apa aja?",
        "Tolong jelaskan jasa yang kalian punya",
        "Di sini melayani apa ya?",
        "Ada pilihan layanan apa saja, kak?",
        "Saya ingin tahu gambaran layanan kalian",
        "Jenis tukangnya ada apa aja?",
        "Apa bedanya jasa borongan dan tukang harian?",
        "Bingung pilih borongan atau harian",
        "Jelaskan pilihan jasa tukang dong",
        "Untuk perbaikan rumah bisa pakai layanan yang mana?",
        "Apakah melayani renovasi dan perbaikan kecil?",
        "Kasih daftar layanan yang dapat dipesan",
        "Pekerjaan bangunan apa yang bisa dibantu?",
        "Ada jasa untuk rumah dan ruko tidak?",
        "Mau lihat menu layanan",
        "Tampilkan katalog jasa secara umum",
        "Kalian punya layanan tukang apa?",
        "Saya butuh bantuan hunian, opsinya apa saja?",
        "Bagaimana cara memilih jenis layanan?",
        "Layanan di aplikasi ini untuk kebutuhan apa?",
        "Boleh minta penjelasan singkat soal layanan?",
        "Apakah ada tukang untuk proyek besar maupun kecil?",
        "Menu jasa tukangnya apa aja sih",
        "Sebutkan dua jenis layanan utama",
        "Aku belum tahu harus pilih jasa yang mana",
        "Cakupan layanan platform ini apa?",
        "Bisa jelaskan layanan dari awal?",
        "Pilihan servis bangunannya apa saja?",
        "Saya mau membandingkan opsi tukang yang ada",
    ),
    Intent.BORONGAN_INFO: (
        "Apa yang dimaksud Jasa Borongan?",
        "Jelaskan cara kerja proyek borongan",
        "Pekerjaan apa saja yang masuk layanan borongan?",
        "Borongan cocok untuk kebutuhan seperti apa?",
        "Apakah renovasi rumah bisa dikerjakan borongan?",
        "Kalau perbaikan ruko besar pilih borongan ya?",
        "Jasa borongan menerima proyek apartemen?",
        "Bangunan apa saja yang dilayani secara borongan?",
        "Apakah sebelum borongan ada survei lokasi?",
        "Bagaimana proses survei untuk proyek borongan?",
        "Data apa yang dibutuhkan untuk survei borongan?",
        "Alamat survei diberikan saat tahap mana?",
        "Bisakah saya memilih tanggal survei borongan?",
        "Jam survei proyek tersedia kapan saja?",
        "Berapa lama proses pengajuan jasa borongan?",
        "Apakah borongan mencakup bahan bangunan?",
        "Siapa yang menentukan detail pekerjaan borongan?",
        "Setelah survei, proses borongan lanjut ke mana?",
        "Untuk renovasi total sebaiknya pakai borongan?",
        "Saya mau tahu cakupan pengerjaan borongan",
        "Borongan itu berdasarkan proyek atau jumlah hari?",
        "Apakah jasa borongan hanya untuk rumah?",
        "Bisa pakai borongan untuk memperbaiki banyak ruangan?",
        "Kalau proyeknya besar bagaimana alur borongannya?",
        "Survei borongan dilakukan di lokasi bangunan kan?",
        "Apa saja yang perlu disiapkan sebelum survei?",
        "Jenis bangunan ruko termasuk cakupan borongan tidak?",
        "Minta info lengkap mengenai layanan borongan",
        "Apakah jadwal survei bisa dipilih sendiri?",
        "Aku ingin paham tahap-tahap jasa borongan",
        "Pengerjaan borongan perlu menentukan spesialisasi tukang?",
        "Apakah budget proyek dicatat saat mengajukan borongan?",
        "Untuk bongkar dan renovasi beberapa bagian, bisa borongan?",
        "Bedanya survei borongan dengan mulai pengerjaan apa?",
        "Jasa borongan menangani satu paket pekerjaan, ya?",
    ),
    Intent.HARIAN_INFO: (
        "Apa itu layanan Tukang Harian?",
        "Bagaimana cara kerja tukang harian?",
        "Spesialisasi tukang apa saja yang tersedia?",
        "Apakah ada tukang khusus cat?",
        "Saya mencari spesialis genteng, tersedia?",
        "Ada teknisi AC dalam layanan harian tidak?",
        "Apakah bisa memesan tukang listrik?",
        "Kalian menyediakan spesialis keramik?",
        "Tukang pipa termasuk pilihan harian?",
        "Pekerjaan kecil cocok memakai tukang harian ya?",
        "Satu tukang bisa dipesan untuk beberapa hari?",
        "Berapa orang tukang yang boleh dipilih?",
        "Apa saja sesi kerja Tukang Harian?",
        "Ada pilihan kerja setengah hari pagi?",
        "Apakah tersedia sesi sore untuk tukang harian?",
        "Full day itu berapa lama dalam layanan ini?",
        "Bisa tentukan tanggal mulai dan selesai pekerjaan?",
        "Foto masalah wajib untuk pesan tukang harian?",
        "Data apa yang diperlukan untuk layanan harian?",
        "Apakah deskripsi kerusakan harus ditulis?",
        "Tukang harian datang ke alamat yang saya berikan?",
        "Kalau cuma memperbaiki satu titik pilih harian?",
        "Saya ingin tahu cakupan kerja spesialis pipa",
        "Bisakah pesan dua spesialis dalam satu reservasi?",
        "Tukang harian tersedia untuk apartemen juga?",
        "Apakah saya dapat memilih jumlah pekerja?",
        "Jelaskan alur layanan harian dari awal",
        "Untuk cat satu kamar cocoknya tukang harian?",
        "Boleh melewati upload foto kerusakan?",
        "Apa perbedaan sesi pagi dan sehari penuh?",
        "Mau tahu daftar keahlian tukang harian",
        "Apakah tukang harian dihitung per tanggal kerja?",
        "Pemasangan keramik kecil bisa ditangani layanan harian?",
        "Kalau AC bermasalah, spesialis mana yang dipilih?",
        "Apakah jadwal kerja harian bisa lebih dari sehari?",
    ),
    Intent.PRICING_INFO: (
        "Berapa harga layanan tukang?",
        "Minta daftar tarif dong",
        "Biaya jasa borongan berapa?",
        "Berapa tarif tukang harian per hari?",
        "Cara menghitung estimasi harga harian bagaimana?",
        "Apakah jumlah pekerja memengaruhi total biaya?",
        "Kalau pesan beberapa hari hitungannya bagaimana?",
        "Sesi pagi tarifnya sama dengan full day?",
        "Berapa biaya admin setiap reservasi?",
        "Apakah borongan dikenakan biaya survei?",
        "Harga dasar borongan rumah berapa?",
        "Minta estimasi borongan untuk apartemen",
        "Berapa biaya dasar proyek ruko?",
        "Tarif spesialis cat sehari berapa?",
        "Berapa ongkos tukang genteng full day?",
        "Harga teknisi AC untuk sesi pagi?",
        "Spesialis listrik tarif sorenya berapa?",
        "Saya ingin tahu biaya tukang keramik",
        "Ongkos spesialis pipa dihitung bagaimana?",
        "Apakah harga yang tampil sudah termasuk admin?",
        "Ada pajak atau biaya tersembunyi tidak?",
        "Budget saya memengaruhi harga borongan?",
        "Ini harga tetap atau hanya perkiraan?",
        "Versi harga demo maksudnya apa?",
        "Tolong buatkan gambaran komponen biayanya",
        "Dua tukang selama tiga hari kira-kira berapa?",
        "Kalau pilih setengah hari apakah lebih murah?",
        "Total pembayaran dihitung oleh sistem, kan?",
        "Brp trf tukng harian?",
        "Ada diskon untuk pemesanan lebih lama?",
    ),
    Intent.START_RESERVATION: (
        "Saya mau mulai reservasi",
        "Tolong buatkan pesanan tukang",
        "Bisa bantu saya booking sekarang?",
        "Saya ingin memesan Jasa Borongan",
        "Mulai pengajuan borongan untuk rumah saya",
        "Tolong jadwalkan survei borongan",
        "Saya jadi ambil layanan borongan",
        "Mau booking proyek renovasi ruko",
        "Pesankan borongan untuk apartemen saya",
        "Saya siap isi data reservasi borongan",
        "Bantu pesan Tukang Harian dong",
        "Saya mau booking tukang cat",
        "Jadwalkan spesialis genteng untuk saya",
        "Tolong pesan teknisi AC",
        "Saya butuh tukang listrik, mulai reservasinya",
        "Mau sewa tukang keramik harian",
        "Pesankan spesialis pipa secepatnya",
        "Saya pilih tukang harian, lanjutkan",
        "Ayo mulai proses pemesanan",
        "Saya sudah siap melakukan reservasi",
        "Langsung booking aja ya",
        "Boking tukang buat besok dong",
        "Mulai form pesanan saya",
        "Saya ingin menjadwalkan tukang ke rumah",
        "Tolong arahkan ke proses booking",
        "Bisa mulai catat data pemesanan saya?",
        "Oke, saya mau pesan layanan ini",
        "Lanjut ke reservasi sekarang",
        "Buat reservasi baru untuk saya",
        "Saya perlu tukang dan ingin memesannya",
        "Pengen booking layanan harian",
        "Saya hendak mengajukan pekerjaan borongan",
        "Siapkan pesanan tukang baru",
        "Mari jadwalkan kunjungan tukang",
        "Reservsi sekarang bisa?",
    ),
    Intent.RESERVATION_STATUS: (
        "Saya mau cek status reservasi",
        "Pesanan saya sudah sampai mana?",
        "Tolong lacak tiket saya",
        "Bagaimana progres booking saya?",
        "Saya ingin melihat status tiket",
        "Reservasi kemarin sudah diproses belum?",
        "Cek pesanan tukang saya dong",
        "Di mana saya bisa mengecek tiket?",
        "Apakah reservasi saya masih menunggu pembayaran?",
        "Tiket saya statusnya apa sekarang?",
        "Bantu periksa nomor tiket ini",
        "Mau lihat detail reservasi yang sudah dibuat",
        "Bagaimana cara melacak pesanan borongan?",
        "Cek progres tukang harian saya",
        "Apakah booking saya sudah tercatat?",
        "Saya punya tiket dan ingin memeriksa statusnya",
        "Tolong tampilkan kembali pesanan saya",
        "Reservasi saya aktif atau tidak?",
        "Sudah ada perkembangan untuk permintaan saya?",
        "Saya ingin konfirmasi keadaan tiket",
        "Lacak reservasi berdasarkan nomor tiket",
        "Status pembayaran pesanan saya bagaimana?",
        "Bisa cari tiket reservasi saya?",
        "Mau cek kelanjutan order tukang",
        "Pesanan yang tadi bisa dilihat lagi?",
    ),
    Intent.GOODBYE: (
        "Sampai jumpa",
        "Dadah",
        "Selamat tinggal",
        "Terima kasih, cukup",
        "Oke makasih, saya pergi dulu",
        "Percakapannya selesai ya",
        "Saya tidak punya pertanyaan lagi",
        "Sudah dulu chatnya",
        "Bye admin",
        "Sampai ketemu lagi",
        "Makasih banyak, dadah",
        "Cukup sekian",
        "Saya pamit",
        "Tutup percakapan ini",
        "Oke, selesai",
        "Terima kasih atas bantuannya",
        "Nanti saya kembali lagi",
        "Udahan ya kak",
        "Sip, itu saja",
        "Tidak perlu dibantu lagi, makasih",
        "Saya akhiri chatnya",
        "Sampai nanti min",
        "Baik, terima kasih dan selamat tinggal",
        "Informasinya sudah cukup",
        "Oke deh, bye",
    ),
}


def iter_records() -> Iterator[UtteranceRecord]:
    """Yield records in taxonomy order with stable, contiguous IDs."""

    sequence = 1
    for definition in INTENT_TAXONOMY:
        for text in UTTERANCES[definition.intent]:
            yield UtteranceRecord(
                id=f"utt-{sequence:04d}",
                text=text,
                intent=definition.intent.value,
            )
            sequence += 1


def write_dataset(destination: Path) -> int:
    """Write the deterministic raw CSV and return its row count."""

    records = tuple(iter_records())
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            {
                "id": record.id,
                "text": record.text,
                "intent": record.intent,
                "source": record.source,
            }
            for record in records
        )
    return len(records)

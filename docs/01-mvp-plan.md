# MVP Plan

## 1. Ringkasan masalah

Calon pelanggan jasa tukang perlu memahami perbedaan Jasa Borongan dan Tukang
Harian, lalu mengisi data reservasi yang cukup panjang. Website biasa membuat
pengguna harus berpindah antara halaman informasi dan form. Chatbot ini
menyatukan proses tanya jawab dan reservasi dalam percakapan bertahap.

Target pengguna adalah individu yang membutuhkan:

- perbaikan bangunan secara borongan untuk rumah, apartemen, atau ruko; atau
- tukang harian berdasarkan spesialisasi untuk masalah hunian tertentu.

## 2. Tujuan MVP

MVP dinyatakan berhasil jika pengguna dapat:

1. Membuka landing page dan memulai chatbot.
2. Memilih jalur awal:
   `1. Tanya-tanya dulu layanan tukang` atau `2. Langsung reservasi`.
3. Mengajukan pertanyaan umum mengenai Jasa Borongan/Tukang Harian.
4. Beralih dari tanya jawab ke reservasi.
5. Menyelesaikan reservasi multi-turn pada salah satu jenis layanan.
6. Memeriksa ringkasan dan memberikan konfirmasi sebelum reservasi dibuat.
7. Menerima nomor tiket, status `MENUNGGU_PEMBAYARAN`, dan estimasi harga.
8. Melihat respons fallback saat intent tidak dikenali.
9. Menghasilkan log percakapan dalam format JSONL.

MVP juga harus menghasilkan artefak akademik untuk P1–P5: dataset minimal 200
utterance, pipeline preprocessing dan TF-IDF, model intent classification,
slot filling, evaluasi model, confusion matrix, serta analisis keterbatasan.

## 3. Scope fungsional

### 3.1 Jalur informasi

- Menjelaskan gambaran layanan.
- Menjelaskan cakupan dan data yang diperlukan untuk Jasa Borongan.
- Menjelaskan spesialisasi, sesi kerja, dan data Tukang Harian.
- Menjelaskan harga demo tetap sesuai pricing version backend.
- Menawarkan transisi ke reservasi.
- Menjawab sapaan, penutup, dan input yang tidak dipahami.

### 3.2 Reservasi Jasa Borongan

Slot wajib:

| Slot | Aturan MVP |
|---|---|
| `customer_id` | Tepat 10 digit angka; diperlakukan sebagai string agar leading zero tidak hilang |
| `phone_number` | Nomor Indonesia yang dapat dinormalisasi ke `+62` |
| `building_type` | `rumah`, `apartemen`, atau `ruko` |
| `survey_address` | Teks 10–300 karakter |
| `survey_date` | Tanggal yang tersedia dan tidak di masa lalu |
| `survey_time` | Salah satu slot waktu dari backend |
| `budget` | Rupiah, bilangan positif dalam batas konfigurasi |

Setelah seluruh slot valid, bot menampilkan ringkasan dan meminta konfirmasi
`ya/tidak`. Jawaban `ya` membuat reservasi dan tiket. Jawaban `tidak` memberi
pilihan slot yang ingin diubah atau membatalkan proses.

### 3.3 Reservasi Tukang Harian

Slot wajib:

| Slot | Aturan MVP |
|---|---|
| `customer_id` | Tepat 10 digit angka; diperlakukan sebagai string agar leading zero tidak hilang |
| `phone_number` | Nomor Indonesia yang dapat dinormalisasi ke `+62` |
| `specialization` | Nilai dari katalog backend |
| `problem_description` | Teks 10–500 karakter |
| `worker_count` | Bilangan bulat sesuai batas konfigurasi |
| `start_date` | Tidak di masa lalu |
| `end_date` | Sama dengan/lebih besar dari tanggal mulai |
| `work_session` | `full_day`, `morning`, atau `afternoon` |
| `work_address` | Teks 10–300 karakter |
| `problem_photo` | Opsional; JPG/PNG/WebP sesuai batas ukuran |

Katalog Tukang Harian menyediakan enam spesialisasi:

| Nama tampilan | Nilai canonical backend |
|---|---|
| Spesialis Cat | `cat` |
| Spesialis Genteng | `genteng` |
| Spesialis AC | `ac` |
| Spesialis Listrik | `listrik` |
| Spesialis Keramik | `keramik` |
| Spesialis Pipa | `pipa` |

Nilai `specialization` pada reservasi harus berasal dari katalog tersebut.

Backend menghitung jumlah hari kerja dan estimasi harga berdasarkan
spesialisasi, jumlah tukang, jumlah hari, dan sesi. Setelah konfirmasi, backend
membuat tiket berstatus `MENUNGGU_PEMBAYARAN`.

### 3.4 Harga demo tetap

Harga memakai konfigurasi `pricing-v1`. Nilainya fixed dan hanya dapat berubah
melalui perubahan konfigurasi backend yang menghasilkan pricing version baru.
Frontend tidak menghitung atau mengubah harga.

Tarif Tukang Harian berikut adalah harga per tukang per hari kalender:

| Spesialisasi | `full_day` | `morning` | `afternoon` |
|---|---:|---:|---:|
| Spesialis Cat | Rp250.000 | Rp150.000 | Rp150.000 |
| Spesialis Genteng | Rp350.000 | Rp210.000 | Rp210.000 |
| Spesialis AC | Rp300.000 | Rp180.000 | Rp180.000 |
| Spesialis Listrik | Rp325.000 | Rp195.000 | Rp195.000 |
| Spesialis Keramik | Rp300.000 | Rp180.000 | Rp180.000 |
| Spesialis Pipa | Rp325.000 | Rp195.000 | Rp195.000 |

Jasa Borongan tidak memiliki slot spesialisasi, sehingga harga dasarnya fixed
berdasarkan jenis bangunan:

| Jenis bangunan | Harga dasar |
|---|---:|
| Rumah | Rp5.000.000 |
| Apartemen | Rp4.000.000 |
| Ruko | Rp7.500.000 |

Biaya tambahan:

- Biaya admin: Rp25.000 per reservasi, berlaku untuk kedua layanan.
- Biaya survei Borongan: Rp100.000 per reservasi.
- Tidak ada pajak, diskon, biaya upload, atau biaya tersembunyi pada MVP.

Total Harian adalah tarif fixed specialization/session dikali jumlah tukang
dan jumlah hari, lalu ditambah biaya admin. Total Borongan adalah harga dasar
jenis bangunan ditambah biaya survei dan biaya admin. `budget` Borongan tetap
dicatat sebagai preferensi pengguna dan tidak mengubah kalkulasi.

Seluruh angka adalah harga demo fixed untuk pengembangan chatbot, bukan
kebijakan harga komersial penyedia jasa nyata.

### 3.5 Tiket

- Format nomor tiket adalah `TKT-YYYYMMDD-XXXXXX`: prefix literal `TKT`,
  tanggal pembuatan 8 digit, dan 6 karakter huruf kapital atau angka.
- Contoh nomor tiket valid: `TKT-20260728-AB12CD`.
- Menyimpan referensi reservasi, jenis layanan, estimasi harga, status, dan
  waktu pembuatan.
- Dapat diperiksa kembali dengan nomor tiket.
- Pengiriman email hanya disimulasikan sebagai pesan/flag
  `email_delivery: NOT_IMPLEMENTED`.

## 4. Di luar scope MVP

- Login, registrasi, dan verifikasi bahwa `customer_id` benar-benar dimiliki
  pengguna.
- Pembayaran dan integrasi payment gateway.
- Pengiriman email/WhatsApp nyata.
- Penjadwalan real-time dengan sistem tenaga kerja eksternal.
- Validasi harga komersial riil, negosiasi, dan perubahan harga setelah survei.
- Computer vision untuk menganalisis foto.
- Dashboard admin, penugasan tukang, reschedule, refund, dan pembatalan setelah
  tiket dibuat.
- Generative AI/LLM dan speech-to-text.
- Dukungan bahasa selain Bahasa Indonesia.

## 5. Asumsi dan keputusan konfigurasi

| ID | Asumsi MVP | Penanganan |
|---|---|---|
| A-01 | Katalog spesialisasi Tukang Harian | Tetapkan enam seed: cat, genteng, AC, listrik, keramik, dan pipa |
| A-02 | Tarif digunakan untuk demonstrasi chatbot | Gunakan matriks fixed `pricing-v1`; perubahan nilai wajib menghasilkan version baru |
| A-03 | Slot survei belum diberikan | Generate slot demo dari hari/jam kerja yang dikonfigurasi |
| A-04 | Budget Borongan tidak menentukan harga demo | Disimpan sebagai preferensi dan ditampilkan terpisah dari total fixed |
| A-05 | ID pelanggan tidak terhubung ke master customer | Validasi tepat 10 digit angka tanpa lookup customer |
| A-06 | Ketersediaan tukang tidak real-time | Reservasi berarti permintaan jadwal, bukan jaminan penugasan |
| A-07 | Lampiran foto opsional | Reservasi tetap bisa dilanjutkan tanpa foto |
| A-08 | Tarif Harian mencakup hari kalender pada rentang tanggal | Gunakan inclusive calendar-day count secara fixed pada `pricing-v1` |

## 6. User journey utama

```mermaid
flowchart TD
    A[Buka landing page] --> B[Buka chatbot]
    B --> C{Ada yang ingin saya bantu?}
    C -->|1 Tanya-tanya| D[FAQ berbasis intent]
    D --> E{Mulai reservasi?}
    E -->|Belum| D
    E -->|Ya| F[Pilih jenis layanan]
    C -->|2 Langsung reservasi| F
    F -->|Jasa Borongan| G[Kumpulkan slot borongan]
    F -->|Tukang Harian| H[Kumpulkan slot harian]
    G --> J[Hitung fixed pricing-v1]
    H --> J
    J --> I
    I --> K{Konfirmasi pengguna}
    K -->|Ubah| L[Pilih slot yang diubah]
    L --> I
    K -->|Batalkan| M[Reservasi dibatalkan]
    K -->|Ya| N[Buat reservasi dan tiket]
    N --> O[Nomor tiket + status menunggu pembayaran]
```

## 7. Non-functional requirements

- API memberikan response terstruktur dan error yang konsisten.
- Target respons lokal p95 di bawah 1 detik, di luar upload file.
- Data sensitif seperti nomor telepon tidak ditulis ke log aplikasi biasa;
  conversation log boleh menyimpan versi masked.
- Upload dibatasi tipe, ukuran, dan nama file yang dihasilkan server.
- Seluruh fixed rate, fee, pricing version, dan katalog berada di
  backend/configuration.
- Model dan vectorizer disimpan dengan versi yang sama.
- Training dapat direproduksi menggunakan seed tetap.
- Backend dan frontend memiliki unit test pada aturan bisnis kritis.
- Chat interface responsif dan dapat digunakan dengan keyboard.
- Seluruh copy chatbot mengikuti standar bahasa customer service di
  `03-nlp-and-dialog-design.md`: ramah, sopan, jelas, solutif, dan tidak
  menyalahkan pengguna.

## 8. Acceptance criteria end-to-end

- [ ] Prompt awal menampilkan dua pilihan yang diwajibkan.
- [ ] Minimal tiga pertanyaan FAQ yang berbeda mendapat jawaban sesuai intent.
- [ ] Reservasi Borongan dapat selesai sampai tiket dan estimasi harga fixed.
- [ ] Reservasi Harian dapat selesai sampai tiket dan estimasi harga.
- [ ] ID pelanggan selain tepat 10 digit ditolak tanpa menghapus slot valid.
- [ ] Nomor tiket mengikuti `TKT-YYYYMMDD-XXXXXX`.
- [ ] Breakdown kedua layanan identik dengan fixed rate `pricing-v1`.
- [ ] Pengguna dapat memperbaiki minimal satu slot pada tahap konfirmasi.
- [ ] Input tidak valid tidak menghapus slot lain yang sudah terkumpul.
- [ ] Respons normal, validasi, fallback, pembatalan, dan error menggunakan
  Bahasa Indonesia yang ramah serta memberi langkah berikutnya yang jelas.
- [ ] Refresh/reconnect dapat melanjutkan conversation selama session ID valid.
- [ ] Setiap turn tersimpan sebagai satu event JSONL yang valid.
- [ ] Dataset berisi sekurangnya 200 utterance dan 4 intent; target MVP 240/8.
- [ ] Script evaluasi menghasilkan accuracy, macro/weighted
  precision-recall-F1, classification report, dan confusion matrix.
- [ ] Landing page dan chat dapat dijalankan melalui petunjuk README.

## 9. Definisi keberhasilan akademik

Tidak digunakan target accuracy arbitrer sebagai jaminan. Baseline yang
diinginkan adalah accuracy dan macro F1 minimal 0,80 pada stratified test set,
namun hasil aktual harus dilaporkan apa adanya. Jika hasil di bawah baseline,
analisis error dan rencana perbaikan tetap menjadi bagian wajib laporan.

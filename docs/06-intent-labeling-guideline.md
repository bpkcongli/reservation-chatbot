# Intent Taxonomy and Labeling Guideline

## Tujuan

Dokumen ini menjadi kontrak pelabelan untuk dataset intent FAQ. Label ditentukan
dari tujuan utama pengguna, bukan dari satu keyword. Intent classifier hanya
dipakai di menu umum/FAQ; jawaban pada state pengisian slot ditangani oleh
dialog manager.

## Taxonomy

| Intent | Target | Beri label ketika | Jangan beri label ketika |
|---|---:|---|---|
| `greeting` | 25 | Pengguna membuka percakapan dengan sapaan. | Sapaan diikuti permintaan yang lebih spesifik. |
| `service_overview` | 30 | Meminta daftar, gambaran, perbandingan, atau saran memilih layanan. | Sudah khusus menanyakan Borongan, Harian, atau harga. |
| `borongan_info` | 35 | Menanyakan cakupan, bangunan, survei, data, atau alur Borongan. | Tujuan utamanya mengetahui nominal atau mulai memesan. |
| `harian_info` | 35 | Menanyakan spesialisasi, sesi, data, atau cara kerja Tukang Harian. | Tujuan utamanya mengetahui tarif atau mulai memesan. |
| `pricing_info` | 30 | Menanyakan tarif, estimasi, komponen biaya, atau pengaruh budget. | Nominal merupakan jawaban slot budget dalam transaksi aktif. |
| `start_reservation` | 35 | Meminta booking, reservasi, pemesanan, atau penjadwalan dimulai. | Hanya bertanya bagaimana cara reservasi. |
| `reservation_status` | 25 | Meminta status tiket, progres, atau detail reservasi yang sudah dibuat. | Meminta membuat reservasi baru. |
| `goodbye` | 25 | Pamit, menyatakan cukup, atau meminta percakapan diakhiri. | Terima kasih masih diikuti pertanyaan atau permintaan. |

Total target adalah 240 utterance. Nilai canonical dan target yang dibaca kode
berada di `app/modules/nlp/taxonomy.py`.

## Aturan keputusan

1. Baca seluruh utterance dan tentukan hasil yang diharapkan pengguna.
2. Jika ada lebih dari satu maksud, pilih permintaan yang paling spesifik dan
   dapat ditindaklanjuti. Contoh: “Halo, saya mau pesan tukang cat” adalah
   `start_reservation`, bukan `greeting`.
3. Kata “borongan” atau “harian” tidak otomatis menentukan label. “Berapa harga
   borongan rumah?” tetap `pricing_info`, sedangkan “Bagaimana survei
   borongan?” adalah `borongan_info`.
4. Bedakan informasi dengan aksi. “Bagaimana cara booking?” adalah
   `service_overview`; “Tolong mulai booking” adalah `start_reservation`.
5. Bedakan reservasi baru dengan reservasi yang sudah ada. Permintaan melacak
   tiket selalu `reservation_status`.
6. Bila dua label tetap sama kuat, tandai untuk adjudikasi; jangan menebak dari
   keyword terbanyak.

## Pedoman penulisan data

- Gunakan variasi formal, percakapan, pertanyaan, dan pernyataan.
- Sertakan sinonim yang alami seperti `pesan`, `booking`, `reservasi`, `biaya`,
  `tarif`, dan `harga`.
- Typo ringan boleh ada dalam porsi kecil, tetapi teks harus tetap dapat
  dipahami tanpa menebak konteks.
- Hindari data pribadi, alamat nyata, nomor telepon, dan nomor tiket milik
  pengguna.
- Jangan membuat data hanya dengan mengganti satu kata pada template yang sama.
- Exact duplicate tidak diperbolehkan. Near-duplicate harus diperiksa dan
  diputuskan sebelum train/test split.

## Contoh batas antar-intent

| Utterance | Label | Alasan |
|---|---|---|
| “Halo, ada layanan apa saja?” | `service_overview` | Permintaan layanan lebih spesifik daripada sapaan. |
| “Apa saja yang masuk borongan?” | `borongan_info` | Fokus pada cakupan. |
| “Biaya borongan rumah berapa?” | `pricing_info` | Hasil yang dicari adalah nominal. |
| “Apakah ada tukang listrik?” | `harian_info` | Memeriksa ketersediaan spesialisasi. |
| “Tolong pesan tukang listrik” | `start_reservation` | Meminta aksi pemesanan. |
| “Bagaimana cara melihat tiket?” | `reservation_status` | Fokus pada reservasi yang sudah dibuat. |
| “Makasih, bagaimana tarifnya?” | `pricing_info` | Pertanyaan harga mengalahkan penutup semu. |

## Prosedur review

1. Jalankan generator dan audit dataset.
2. Periksa kegagalan schema, jumlah per label, exact duplicate, dan semua
   pasangan near-duplicate yang dilaporkan.
3. Spot-check setiap label terhadap aturan inklusi/eksklusi, termasuk contoh
   batas antar-intent.
4. Catat keputusan pasangan near-duplicate dan temuan variasi dalam
   `data/reviews/intents-manual-review.md`.
5. Jika hanya satu reviewer tersedia, tulis keterbatasan tersebut; jangan
   mengklaim inter-annotator agreement.

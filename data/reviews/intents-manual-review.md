# Manual Review — Intent Dataset

Tanggal review: 2026-07-29  
Dataset: `data/raw/intents.csv`  
SHA-256: `93641153746f7c85c17510ed00d224ae626aeafb1649bd0c29716df25feedb60`

## Cakupan dan keterbatasan

Seluruh 240 utterance diperiksa oleh satu reviewer implementer terhadap
`docs/06-intent-labeling-guideline.md`. Belum ada reviewer kedua, sehingga
review ini tidak mengklaim inter-annotator agreement. Review kedua tetap
direkomendasikan sebelum metrik final dipakai dalam laporan akademik.

## Hasil integrity dan duplicate review

- Total: 240/240 baris.
- Distribusi: sesuai delapan target taxonomy.
- ID kosong/duplikat/tidak berurutan: 0.
- Teks kosong dan label di luar taxonomy: 0.
- Exact duplicate setelah normalisasi case dan tanda baca: 0.
- Near-duplicate pada ambang utama (`SequenceMatcher >= 0.88` atau token
  Jaccard `>= 0.80` untuk teks dengan minimal empat token): 0.
- Pemeriksaan kedua dengan ambang lebih longgar (`>= 0.78` atau `>= 0.65`):
  0 kandidat.

Hasil audit yang dapat direproduksi tersimpan di `intents-audit.json`; CSV
kandidat tetap dibuat dengan header walaupun tidak ada pasangan yang perlu
diadjudikasi.

## Review variasi dan konsistensi label

| Intent | ID | Fokus review | Hasil |
|---|---|---|---|
| `greeting` | `utt-0001`–`utt-0025` | Sapaan waktu, informal/formal, pembuka singkat | 25 sesuai; tidak ada permintaan spesifik yang mengalahkan sapaan. |
| `service_overview` | `utt-0026`–`utt-0055` | Daftar, perbandingan, dan pemilihan layanan | 30 sesuai; tidak ada permintaan harga atau aksi booking. |
| `borongan_info` | `utt-0056`–`utt-0090` | Cakupan bangunan, survei, data, dan alur proyek | 35 sesuai; pertanyaan budget `utt-0087` meminta data proses, bukan nominal harga. |
| `harian_info` | `utt-0091`–`utt-0125` | Enam spesialisasi, sesi, jadwal, foto, dan aturan pemesanan | 35 sesuai; `utt-0097` dan `utt-0114` berbentuk pertanyaan kemampuan, bukan instruksi memulai booking. |
| `pricing_info` | `utt-0126`–`utt-0155` | Harga umum, kedua layanan, komponen, dan rumus | 30 sesuai; mencakup satu typo ringan tanpa mengubah makna. |
| `start_reservation` | `utt-0156`–`utt-0190` | Permintaan aksi umum, Borongan, Harian, dan tiap spesialisasi | 35 sesuai; seluruhnya meminta proses dimulai, termasuk dua typo ringan. |
| `reservation_status` | `utt-0191`–`utt-0215` | Status tiket, progres reservasi, dan pembayaran | 25 sesuai; semuanya merujuk pesanan yang sudah ada. |
| `goodbye` | `utt-0216`–`utt-0240` | Pamit, cukup, dan perintah mengakhiri chat | 25 sesuai; ucapan terima kasih tidak diikuti maksud lain. |

Indikator variasi otomatis menunjukkan rentang satu sampai delapan token,
campuran pertanyaan/pernyataan, serta ragam formal dan percakapan. Typo sengaja
dibatasi pada tiga contoh agar model tidak didominasi noise sintetis.

## Keputusan

Dataset diterima untuk tahap analisis dan preprocessing. Setiap perubahan pada
sumber utterance wajib:

1. menghasilkan ulang CSV dan artifact audit;
2. memastikan hash pada dokumen ini diperbarui; dan
3. mengulang review label serta near-duplicate sebelum train/test split.

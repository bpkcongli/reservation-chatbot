# NLP and Dialog Design

## 1. Pendekatan sistem

Sistem bersifat hybrid:

1. Intent classifier memahami tujuan utterance saat pengguna berada di menu
   umum/FAQ.
2. Rule-based slot filling membaca nilai terstruktur saat dialog sedang
   mengumpulkan data reservasi.
3. Dialog manager berbasis finite state machine menentukan pertanyaan
   berikutnya, validasi, koreksi, konfirmasi, dan pembuatan tiket.

Intent classifier tidak boleh bebas melompati state transaksi. Contohnya,
saat state meminta nomor telepon, prioritas sistem adalah phone extractor,
bukan menafsirkan nomor tersebut sebagai intent FAQ.

## 2. Dataset intent

Target dataset awal adalah 240 utterance buatan sendiri dalam Bahasa Indonesia.
Semua utterance akan direview agar tidak hanya berupa perubahan satu kata dari
template yang sama.

| Intent | Jumlah | Persentase | Contoh tujuan |
|---|---:|---:|---|
| `greeting` | 25 | 10,42% | Sapaan/memulai percakapan |
| `service_overview` | 30 | 12,50% | Menanyakan layanan yang tersedia |
| `borongan_info` | 35 | 14,58% | Cakupan/survei Jasa Borongan |
| `harian_info` | 35 | 14,58% | Cakupan/spesialisasi Tukang Harian |
| `pricing_info` | 30 | 12,50% | Menanyakan tarif/estimasi/budget |
| `start_reservation` | 35 | 14,58% | Meminta mulai booking/reservasi |
| `reservation_status` | 25 | 10,42% | Mengecek tiket/status reservasi |
| `goodbye` | 25 | 10,42% | Mengakhiri percakapan |
| **Total** | **240** | **100%** | |

Distribusi dibuat cukup seimbang untuk proyek akademik. Intent informasi dan
reservasi diberi sedikit lebih banyak variasi karena bahasa pengguna di area
tersebut lebih beragam dan batas antarkelasnya lebih mudah tumpang tindih.

### Format raw dataset

`data/raw/intents.csv`:

```csv
id,text,intent,source
utt-0001,Halo kak,greeting,synthetic_manual
utt-0042,Apa saja yang termasuk jasa borongan?,borongan_info,synthetic_manual
utt-0111,Berapa tarif tukang sehari?,pricing_info,synthetic_manual
utt-0178,Saya mau pesan tukang untuk besok,start_reservation,synthetic_manual
```

Dataset generator harus deterministic, namun hasilnya tetap direview manual.
Kolom `source` membuat asal data transparan. ID unik dipakai untuk traceability.

### Pedoman variasi utterance

- Formal dan percakapan: “Saya ingin…” / “mau… dong”.
- Sinonim relevan: pesan, booking, reservasi; biaya, tarif, harga.
- Bentuk pertanyaan dan pernyataan.
- Typo ringan yang realistis dalam porsi kecil.
- Konteks eksplisit Borongan/Harian maupun konteks singkat.
- Tidak memasukkan nomor telepon/alamat nyata.
- Hindari duplikat exact maupun near-duplicate lintas train dan test.
- Label berdasarkan tujuan utama, bukan semata keyword.

### Quality checks

- Total dan jumlah per intent sesuai tabel.
- Tidak ada `text` kosong, ID duplikat, atau label di luar taxonomy.
- Exact duplicate dihapus sebelum split.
- Near-duplicate diperiksa sebelum split untuk mengurangi data leakage.
- Panjang karakter/token dan contoh per label dilaporkan.
- Minimal dua orang melakukan spot-check bila memungkinkan; jika hanya satu,
  keterbatasan tersebut ditulis dalam laporan.

## 3. Text preprocessing

Urutan pipeline:

1. Unicode normalization (`NFKC`).
2. Lowercase.
3. Ganti URL, email, dan nomor telepon dengan token khusus bila muncul.
4. Hapus HTML dan karakter kontrol.
5. Normalisasi whitespace.
6. Pertahankan kata/angka yang informatif; ubah tanda baca lain menjadi spasi.
7. Tokenisasi dengan regex.

Stemming dan stopword removal tidak digunakan pada baseline. Untuk utterance
pendek, stopword seperti “mau”, “apa”, dan “berapa” dapat membantu membedakan
intent. Stemming Bahasa Indonesia dapat diuji sebagai eksperimen terpisah,
tetapi hasilnya harus dibandingkan dengan baseline.

Contoh yang nantinya wajib dihasilkan oleh script, bukan diketik manual di
laporan:

| Sebelum | Setelah cleaning/lowercase | Token |
|---|---|---|
| `Halo Kak!! Ada jasa tukang listrik?` | `halo kak ada jasa tukang listrik` | `["halo","kak","ada","jasa","tukang","listrik"]` |
| `Saya mau BOOKING tukang utk 02/08/2026.` | `saya mau booking tukang utk 02 08 2026` | `["saya","mau","booking","tukang","utk","02","08","2026"]` |
| `Cek tiket TKT-20260728-AB12CD dong` | `cek tiket tkt 20260728 ab12cd dong` | `["cek","tiket","tkt","20260728","ab12cd","dong"]` |

Preprocessor yang sama harus dipakai saat training dan inference. Cara paling
aman adalah membungkusnya di sklearn `Pipeline`.

## 4. Representasi dan intent classification

Baseline utama:

```text
cleaner/tokenizer
  -> TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
  -> LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
```

Hyperparameter dipilih melalui cross-validation hanya pada training data.
Candidate grid kecil:

- `ngram_range`: `(1, 1)` atau `(1, 2)`.
- `min_df`: `1` atau `2`.
- Logistic Regression `C`: `0.5`, `1.0`, `2.0`.

Multinomial Naive Bayes dapat dilaporkan sebagai baseline pembanding. Model
final dipilih berdasarkan macro F1 validation/cross-validation, bukan test set.

### Split dan reproducibility

- Stratified split: 80% train (192), 20% test (48).
- `random_state=42`.
- Bila melakukan tuning: stratified 5-fold CV hanya pada 192 train samples.
- Test set disentuh satu kali untuk evaluasi final.
- Simpan pipeline, label list, dataset checksum, waktu training, library
  versions, dan model version.

### Confidence dan fallback

`predict_proba` dipakai untuk confidence. Threshold tidak ditentukan dengan
menebak test result; threshold awal dipilih dari validation behavior. Jika
confidence di bawah threshold, bot memberi respons:

> Maaf, saya belum yakin memahami pertanyaan Anda. Anda ingin mengetahui Jasa
> Borongan, Tukang Harian, harga, atau mulai reservasi?

Quick reply menjaga pengguna tetap dapat melanjutkan meskipun classifier gagal.

## 5. Rule-based slot filling

Extractor membaca raw text dan state aktif. Contoh:

| Slot | Teknik | Contoh |
|---|---|---|
| `phone_number` | Regex + normalisasi `0`, `62`, `+62` | `0812 3456 7890` → `+6281234567890` |
| `customer_id` | Pattern allow-list | `CUST-1024` |
| `building_type` | Dictionary/synonym matching | `rumah saya` → `rumah` |
| `budget` | Regex nominal + unit | `sekitar 20 juta` → `20000000` |
| `worker_count` | Regex angka/kata bilangan terbatas | `dua orang` → `2` |
| `work_session` | Pattern/synonym | `setengah hari pagi` → `morning` |
| dates | Parser format Indonesia + validation | `2 Agustus 2026` → ISO date |
| ticket number | Regex case-insensitive | `TKT-20260728-AB12CD` |

Alamat dan deskripsi bukan NER; keduanya diambil sebagai jawaban penuh pada
state yang sesuai lalu divalidasi panjangnya. Foto masuk melalui endpoint
attachment dan menghasilkan `attachment_id`.

Jika satu utterance mengandung beberapa slot—misalnya “dua tukang dari tanggal
2 sampai 3 Agustus”—semua slot valid boleh disimpan sekaligus. Dialog manager
lalu menanyakan slot wajib berikutnya yang masih kosong.

## 6. Dialog state machine

### State umum

```mermaid
stateDiagram-v2
    [*] --> WELCOME
    WELCOME --> INFO_MODE: pilih 1
    WELCOME --> SELECT_SERVICE: pilih 2
    INFO_MODE --> INFO_MODE: FAQ dikenali
    INFO_MODE --> FALLBACK: confidence rendah
    FALLBACK --> INFO_MODE: pilih topik
    INFO_MODE --> SELECT_SERVICE: mulai reservasi
    SELECT_SERVICE --> BORONGAN_ASK_CUSTOMER_ID: borongan
    SELECT_SERVICE --> HARIAN_ASK_CUSTOMER_ID: harian
    TICKET_LOOKUP --> INFO_MODE: status ditampilkan
    INFO_MODE --> TICKET_LOOKUP: cek tiket
```

### Jasa Borongan

```mermaid
stateDiagram-v2
    BORONGAN_ASK_CUSTOMER_ID --> BORONGAN_ASK_PHONE: valid
    BORONGAN_ASK_PHONE --> BORONGAN_ASK_BUILDING: valid
    BORONGAN_ASK_BUILDING --> BORONGAN_ASK_ADDRESS: valid
    BORONGAN_ASK_ADDRESS --> BORONGAN_ASK_SURVEY_DATE: valid
    BORONGAN_ASK_SURVEY_DATE --> BORONGAN_ASK_SURVEY_TIME: valid
    BORONGAN_ASK_SURVEY_TIME --> BORONGAN_ASK_BUDGET: valid
    BORONGAN_ASK_BUDGET --> CONFIRM_RESERVATION: valid
    CONFIRM_RESERVATION --> TICKET_CREATED: ya
    CONFIRM_RESERVATION --> EDIT_SLOT: ubah
    EDIT_SLOT --> CONFIRM_RESERVATION: slot valid
    CONFIRM_RESERVATION --> CANCELLED: batal
    TICKET_CREATED --> [*]
    CANCELLED --> [*]
```

### Tukang Harian

```mermaid
stateDiagram-v2
    HARIAN_ASK_CUSTOMER_ID --> HARIAN_ASK_PHONE: valid
    HARIAN_ASK_PHONE --> HARIAN_ASK_SPECIALIZATION: valid
    HARIAN_ASK_SPECIALIZATION --> HARIAN_ASK_DESCRIPTION: valid
    HARIAN_ASK_DESCRIPTION --> HARIAN_ASK_WORKER_COUNT: valid
    HARIAN_ASK_WORKER_COUNT --> HARIAN_ASK_START_DATE: valid
    HARIAN_ASK_START_DATE --> HARIAN_ASK_END_DATE: valid
    HARIAN_ASK_END_DATE --> HARIAN_ASK_SESSION: valid
    HARIAN_ASK_SESSION --> HARIAN_ASK_PHOTO: valid
    HARIAN_ASK_PHOTO --> HARIAN_ASK_ADDRESS: upload atau lewati
    HARIAN_ASK_ADDRESS --> CALCULATE_PRICE: valid
    CALCULATE_PRICE --> CONFIRM_RESERVATION
    CONFIRM_RESERVATION --> TICKET_CREATED: ya
    CONFIRM_RESERVATION --> EDIT_SLOT: ubah
    EDIT_SLOT --> CALCULATE_PRICE: slot harga berubah
    EDIT_SLOT --> CONFIRM_RESERVATION: slot non-harga berubah
    CONFIRM_RESERVATION --> CANCELLED: batal
    TICKET_CREATED --> [*]
    CANCELLED --> [*]
```

Pada setiap `ASK_*`, jawaban invalid mempertahankan state, menjelaskan format
yang diharapkan, dan memberi contoh. Perintah global `batal`, `mulai ulang`,
`menu`, dan `bantuan` ditangani sebelum extractor state.

## 7. Pricing design

Nilai tarif belum diberikan dan harus berada pada config/katalog seed.

Rumus estimasi Tukang Harian:

```text
jumlah_hari = inclusive_day_count(start_date, end_date)
subtotal = tariff[specialization][session] * worker_count * jumlah_hari
estimated_price = subtotal + configurable_service_fee
```

Rumus dan breakdown ditampilkan kepada pengguna. Untuk Borongan, `budget`
adalah perkiraan budget pelanggan; harga final menunggu survei sehingga tiket
menampilkan `estimated_price: null` dan budget secara terpisah.

## 8. Evaluation plan

Script evaluasi wajib menghasilkan:

- Accuracy.
- Precision, recall, dan F1 per class.
- Macro average dan weighted average.
- Confusion matrix dalam CSV dan PNG.
- Daftar contoh misclassification berisi text, actual, predicted, confidence.
- Distribusi train/test per intent.

Output direncanakan:

```text
artifacts/evaluation/
├── metrics.json
├── classification-report.csv
├── confusion-matrix.csv
├── confusion-matrix.png
├── misclassified.csv
├── dataset-distribution.csv
└── preprocessing-examples.csv
```

### Analisis error yang wajib ditulis setelah eksperimen

Jangan menyatakan intent paling sering salah sebelum hasil model tersedia.
Analisis final mengambil pasangan off-diagonal terbesar pada confusion matrix,
lalu memeriksa contoh utterance-nya.

Hipotesis awal yang perlu diuji:

- `borongan_info` vs `pricing_info`, karena pertanyaan budget borongan memuat
  kata biaya/harga.
- `harian_info` vs `pricing_info`, karena “tarif tukang harian” menyebut nama
  layanan sekaligus harga.
- `service_overview` vs kedua intent layanan, terutama pada pertanyaan pendek.
- `start_reservation` vs `harian_info`, misalnya “butuh tukang listrik”.

Penyebab yang mungkin:

- Dataset sintetis kecil tidak mencerminkan variasi pengguna nyata.
- Keyword yang sama muncul di beberapa intent.
- Utterance pendek tidak memiliki konteks.
- Typo/slang belum terwakili.
- Label tujuan utama bersifat ambigu.
- Split mengandung distribusi variasi bahasa yang tidak merata.

### Keterbatasan sistem

- Hanya Bahasa Indonesia dan domain jasa tukang terbatas.
- Intent taxonomy kecil; pertanyaan di luar scope menghasilkan fallback.
- TF-IDF tidak memahami makna/konteks sedalam embedding atau LLM.
- Rule-based slot filling sensitif terhadap format baru.
- State disimpan per conversation, sehingga penggunaan ID yang salah dapat
  mengganggu konteks.
- Data sintetis berpotensi membuat metrik lebih optimistis dari pemakaian nyata.
- Tidak ada availability, payment, customer, email, atau WhatsApp real-time.
- Estimasi harga bergantung pada asumsi konfigurasi.
- Foto hanya disimpan, tidak dianalisis.

## 9. Conversation test scenarios

Minimal automated scenarios:

1. Welcome → info → tanya Borongan → mulai reservasi.
2. Direct reservation → Borongan → semua slot valid → confirm → ticket.
3. Direct reservation → Harian → skip photo → price → confirm → ticket.
4. Phone invalid lalu valid, state tidak meloncat.
5. End date sebelum start date, bot meminta ulang.
6. Konfirmasi `ubah` → ubah jumlah tukang → harga dihitung ulang.
7. Konfirmasi `batal` tidak membuat reservation/ticket.
8. Low-confidence message menghasilkan fallback dan quick replies.
9. Ticket lookup valid dan nomor tiket tidak ditemukan.
10. Refresh session mengembalikan state dan slots yang sama.

# Sequence Diagram

Dokumen ini menjelaskan interaksi runtime utama Reservation Chatbot. Kontrak
request/response normatif berada di
[OpenAPI contract](../api-contract/openapi.yml), sedangkan state dan aturan
slot dijelaskan di [NLP and dialog design](../03-nlp-and-dialog-design.md).

## Komponen

| Nama | Tanggung jawab |
|---|---|
| Pengguna | Memilih jalur, memberikan slot, dan mengonfirmasi reservasi |
| Frontend | Menampilkan chat dan menyimpan `conversation_id`; tidak menentukan state atau harga |
| API | Validasi HTTP, rate limit, envelope `status`/`data`, dan routing |
| Conversation | State machine, slot priority, prompt, serta global command |
| NLP | Preprocessing dan prediksi intent pada info mode |
| Catalog | Layanan, spesialisasi, sesi kerja, tarif, dan slot survei |
| Reservation | Draft, validasi lintas field, finalisasi reservasi |
| Pricing | Kalkulasi fixed `pricing-v1` untuk Harian dan Borongan |
| Ticketing | Pembuatan nomor tiket unik dan lookup |
| MySQL | State, message, draft, reservasi, attachment metadata, dan tiket |
| JSONL Logger | Satu event ter-mask untuk setiap turn |
| File Storage | Binary foto dengan generated filename |

Path tanpa prefix pada diagram panjang adalah singkatan dari `/api/v1`.

## 1. Membuka chat dan membuat conversation

```mermaid
sequenceDiagram
    autonumber
    actor U as Pengguna
    participant W as Next.js Frontend
    participant A as FastAPI
    participant C as Conversation
    participant DB as MySQL
    participant L as JSONL Logger

    U->>W: Buka chat
    W->>A: POST /api/v1/conversations
    A->>C: create_conversation(locale=id-ID)
    C->>DB: INSERT conversation(state=WELCOME)
    C->>DB: INSERT bot message
    C->>L: Append event session_created
    C-->>A: Snapshot + prompt + 2 quick replies
    A-->>W: 201 ConversationResponse
    W->>W: Simpan conversation_id
    W-->>U: Tampilkan pilihan info / reservasi
```

Frontend membuat conversation baru hanya bila belum memiliki
`conversation_id` yang valid. Refresh halaman menggunakan alur restore pada
bagian 5.

## 2. Jalur tanya layanan dan fallback NLP

```mermaid
sequenceDiagram
    autonumber
    actor U as Pengguna
    participant W as Next.js Frontend
    participant A as FastAPI
    participant C as Conversation
    participant N as NLP
    participant DB as MySQL
    participant L as JSONL Logger

    U->>W: "Apa saja jasa tukang harian?"
    W->>A: POST /conversations/{conversation_id}/messages
    Note over W,A: client_message_id mencegah turn duplikat
    A->>C: process_message(text, client_message_id)
    C->>DB: Cek idempotency + load state/context
    C->>N: predict_intent(normalized_text)
    N-->>C: harian_info, confidence

    alt confidence >= threshold
        C->>C: Pilih FAQ response
        C->>DB: Simpan user/bot message + state INFO_MODE
        C->>L: Append turn dengan intent dan confidence
        C-->>A: Jawaban FAQ + quick reply reservasi
        A-->>W: 200 ConversationResponse
        W-->>U: Tampilkan jawaban
    else confidence < threshold
        C->>C: Gunakan fallback terarah
        C->>DB: Simpan message + state FALLBACK
        C->>L: Append turn fallback
        C-->>A: Prompt klarifikasi + pilihan topik
        A-->>W: 200 ConversationResponse
        W-->>U: Tampilkan fallback
    end
```

Perintah global `batal`, `menu`, `bantuan`, dan `mulai ulang` diperiksa oleh
Conversation sebelum memanggil model NLP.

## 3. Reservasi Tukang Harian

```mermaid
sequenceDiagram
    autonumber
    actor U as Pengguna
    participant W as Next.js Frontend
    participant A as FastAPI
    participant C as Conversation
    participant K as Catalog
    participant R as Reservation
    participant P as Pricing
    participant T as Ticketing
    participant DB as MySQL
    participant L as JSONL Logger
    participant FS as File Storage

    U->>W: Pilih "Langsung reservasi"
    W->>A: POST message(value=reservation)
    A->>C: process_message
    C->>DB: Load conversation
    C-->>A: State SELECT_SERVICE
    A-->>W: 200 ConversationResponse

    U->>W: Pilih Tukang Harian
    W->>A: POST message(value=harian)
    A->>C: process_message
    C->>R: create_or_load_draft(harian)
    R->>DB: UPSERT reservation_draft
    C-->>A: State HARIAN_ASK_CUSTOMER_ID
    A-->>W: 200 ConversationResponse

    loop Setiap slot wajib yang belum terisi
        U->>W: Jawab slot berikutnya
        W->>A: POST /conversations/{conversation_id}/messages
        A->>C: process_message
        C->>DB: Load state + draft
        C->>R: extract_and_validate(raw_text, state)
        opt Slot specialization atau work_session
            R->>K: Validasi terhadap katalog aktif
            K-->>R: Nilai canonical / invalid
        end
        alt Nilai valid
            R->>DB: Update slot draft tanpa menghapus slot lain
            C->>DB: Simpan user/bot message + state berikutnya
            C->>L: Append event ter-mask
            C-->>A: Prompt slot berikutnya
            A-->>W: 200 ConversationResponse
        else Nilai invalid
            C->>DB: Pertahankan state dan draft sebelumnya
            C->>L: Append invalid turn ter-mask
            C-->>A: Feedback field + contoh format
            A-->>W: 422 ErrorResponse(status.errorDetails)
            W-->>U: Tampilkan feedback dan pertahankan input
        end
    end

    Note over U,R: customer_id wajib tepat 10 digit angka

    opt Pengguna mengunggah foto
        U->>W: Pilih foto JPG/PNG/WebP
        W->>A: POST /conversations/{conversation_id}/attachments
        A->>A: Cek limit, MIME, extension, magic bytes
        A->>FS: Simpan dengan generated filename
        A->>R: Kaitkan attachment ke draft
        R->>DB: INSERT attachment metadata
        A-->>W: 201 AttachmentUploadResponse
    end

    C->>P: calculate(specialization, session, workers, dates)
    P->>K: Ambil fixed rate pricing-v1
    K-->>P: Unit rate + admin fee Rp25.000
    P-->>C: PriceBreakdown
    C->>DB: Simpan snapshot kalkulasi
    C-->>A: CONFIRM_RESERVATION + summary + estimasi
    A-->>W: 200 ConversationResponse
    W-->>U: Tampilkan ringkasan

    alt Pengguna memilih ubah
        U->>W: Pilih slot yang ingin diubah
        W->>A: POST message(value=edit...)
        A->>C: Pindah ke EDIT_SLOT
        C-->>A: Prompt nilai pengganti
        A-->>W: 200 ConversationResponse
        Note over C,P: Hitung ulang jika slot harga berubah
    else Pengguna memilih batal
        U->>W: Pilih batal
        W->>A: POST message(value=batal)
        A->>C: cancel_draft
        C->>DB: Tandai draft batal tanpa membuat reservasi/tiket
        C->>L: Append cancellation event
        C-->>A: State CANCELLED
        A-->>W: 200 ConversationResponse
    else Pengguna mengonfirmasi
        U->>W: Pilih ya
        W->>A: POST message(value=ya)
        A->>C: confirm_reservation
        C->>R: finalize(draft, price_breakdown)
        R->>DB: BEGIN transaction
        R->>DB: INSERT reservation
        R->>DB: Hubungkan attachment bila ada
        R->>T: create_ticket(reservation)
        T->>DB: INSERT unique TKT-YYYYMMDD-XXXXXX
        R->>DB: COMMIT
        C->>DB: State TICKET_CREATED + bot message
        C->>L: Append confirmation event
        C-->>A: Ticket MENUNGGU_PEMBAYARAN
        A-->>W: 200 ConversationResponse
        W-->>U: Tampilkan ticket card
    end
```

Enam nilai specialization canonical adalah `cat`, `genteng`, `ac`, `listrik`,
`keramik`, dan `pipa`. Hanya cabang konfirmasi yang boleh membuat reservation
dan ticket.

## 4. Reservasi Jasa Borongan

```mermaid
sequenceDiagram
    autonumber
    actor U as Pengguna
    participant W as Next.js Frontend
    participant A as FastAPI
    participant C as Conversation
    participant K as Catalog
    participant R as Reservation
    participant P as Pricing
    participant T as Ticketing
    participant DB as MySQL
    participant L as JSONL Logger

    U->>W: Pilih Jasa Borongan
    W->>A: POST message(value=borongan)
    A->>C: process_message
    C->>R: create_or_load_draft(borongan)
    R->>DB: UPSERT reservation_draft
    C-->>A: State BORONGAN_ASK_CUSTOMER_ID
    A-->>W: 200 ConversationResponse

    Note over U,R: customer_id wajib tepat 10 digit angka

    loop customer_id, phone, building, address
        U->>W: Jawab slot
        W->>A: POST message
        A->>C: Validasi sesuai state
        C->>R: Simpan slot valid
        R->>DB: UPDATE draft
        C->>L: Append event ter-mask
        C-->>A: Prompt berikutnya
        A-->>W: 200 ConversationResponse
    end

    C-->>A: State BORONGAN_ASK_SURVEY_DATE
    A-->>W: 200 ConversationResponse
    W->>A: GET /catalog/survey-slots?date_from&date_to
    A->>K: list_available_survey_slots
    K-->>A: Slot demo yang tersedia
    A-->>W: 200 SurveySlotResponse
    U->>W: Pilih tanggal dan waktu
    W->>A: POST message
    A->>C: Validasi terhadap Catalog
    C->>R: Simpan survey_date dan survey_time
    R->>DB: UPDATE draft

    U->>W: Masukkan budget
    W->>A: POST message
    A->>C: Normalisasi nominal
    C->>R: Simpan budget sebagai preferensi
    R->>DB: UPDATE draft
    C->>P: calculate_borongan(building_type)
    P->>K: Ambil fixed rate pricing-v1
    K-->>P: Base price + survey Rp100.000 + admin Rp25.000
    P-->>C: BoronganPriceBreakdown
    C->>DB: Simpan price snapshot
    C-->>A: CONFIRM_RESERVATION + summary
    A-->>W: 200 ConversationResponse
    Note over W,U: Budget tidak mengubah total fixed

    alt Konfirmasi ya
        U->>W: Pilih ya
        W->>A: POST message(value=ya)
        A->>C: confirm_reservation
        C->>R: finalize(draft, price_breakdown)
        R->>DB: BEGIN transaction
        R->>DB: INSERT reservation
        R->>T: create_ticket
        T->>DB: INSERT TKT-YYYYMMDD-XXXXXX
        R->>DB: COMMIT
        C->>L: Append confirmation event
        C-->>A: Ticket + fixed total + budget
        A-->>W: 200 ConversationResponse
    else Ubah atau batal
        U->>W: Pilih ubah / batal
        W->>A: POST message
        A->>C: Edit slot atau cancel draft
        C->>DB: Update tanpa membuat ticket
        C->>L: Append event
        C-->>A: Prompt edit atau state CANCELLED
        A-->>W: 200 ConversationResponse
    end
```

## 5. Refresh dan pemulihan conversation

```mermaid
sequenceDiagram
    autonumber
    actor U as Pengguna
    participant W as Next.js Frontend
    participant A as FastAPI
    participant C as Conversation
    participant DB as MySQL

    U->>W: Refresh halaman
    W->>W: Baca conversation_id dari storage
    W->>A: GET /conversations/{conversation_id}
    A->>C: restore_conversation(id)
    C->>DB: SELECT conversation + messages + draft + ticket

    alt Session ditemukan dan belum expired
        DB-->>C: Snapshot terkini
        C-->>A: ConversationData dengan full history
        A-->>W: 200 ConversationResponse(status + data)
        W-->>U: Render history dan lanjutkan state aktif
    else Session expired
        C-->>A: CONVERSATION_EXPIRED
        A-->>W: 410 ErrorResponse(status)
        W->>W: Hapus conversation_id lama
        W-->>U: Tawarkan mulai percakapan baru
    else ID tidak ditemukan
        C-->>A: CONVERSATION_NOT_FOUND
        A-->>W: 404 ErrorResponse(status)
        W->>W: Hapus conversation_id invalid
        W-->>U: Tawarkan mulai percakapan baru
    end
```

## 6. Lookup tiket

```mermaid
sequenceDiagram
    autonumber
    actor U as Pengguna
    participant W as Next.js Frontend
    participant A as FastAPI
    participant T as Ticketing
    participant DB as MySQL

    U->>W: Masukkan nomor tiket
    W->>A: GET /api/v1/tickets/{ticket_number}
    A->>A: Validasi format TKT-YYYYMMDD-XXXXXX
    A->>T: find_by_ticket_number
    T->>DB: SELECT ticket + safe reservation summary

    alt Tiket ditemukan
        DB-->>T: Ticket + reservation
        T-->>A: DTO tanpa PII sensitif
        A-->>W: 200 Ticket
        W-->>U: Tampilkan status dan estimasi/budget
    else Tiket tidak ditemukan
        DB-->>T: Empty
        T-->>A: TICKET_NOT_FOUND
        A-->>W: 404 ErrorResponse(status)
        W-->>U: Tampilkan error dan izinkan koreksi
    end
```

## 7. Aturan kegagalan dan retry

- HTTP `422` berarti bentuk request atau nilai slot tidak valid. Feedback field
  berada pada `status.errorDetails`; frontend mempertahankan input dan meminta
  pengguna memperbaikinya.
- Invalid slot tetap dicatat sebagai turn dan tidak menghapus state/slot valid
  sebelumnya, walaupun response menggunakan error envelope HTTP `422`.
- HTTP `409` berarti operasi tidak sesuai state aktif, misalnya upload foto
  pada draft Borongan.
- HTTP `410` membuat frontend membuang session lokal yang kedaluwarsa.
- HTTP `429` mengikuti header `Retry-After`; HTTP `503` boleh di-retry dengan
  backoff. Retry message memakai `client_message_id` yang sama.
- Kegagalan sebelum database `COMMIT` me-rollback reservasi dan tiket bersama.
  Sistem tidak boleh menghasilkan tiket tanpa reservation atau menghasilkan
  dua tiket akibat retry.

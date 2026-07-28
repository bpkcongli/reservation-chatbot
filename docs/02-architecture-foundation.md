# Architecture Foundation

## 1. Gaya arsitektur

Repository menggunakan monorepo dengan dua deployable application:

- `backend`: modular monolith Python yang menyediakan HTTP API.
- `frontend`: Next.js web app yang mengonsumsi API backend.

Istilah modular monolith berlaku pada backend: satu process dan satu database,
namun domain dipisahkan menjadi module dengan public interface yang jelas.
Module tidak membaca table milik module lain secara sembarang; koordinasi
dilakukan melalui application service.

```mermaid
flowchart LR
    U[Pengguna] --> W[Next.js Web]
    W -->|REST / JSON| A[FastAPI]
    W -->|multipart upload| A

    subgraph Backend Modular Monolith
        A --> C[Conversation]
        C --> N[NLP]
        C --> K[Catalog]
        C --> R[Reservation]
        R --> P[Pricing]
        R --> T[Ticketing]
    end

    N --> M[(Model artifacts)]
    K --> DB[(MySQL)]
    R --> DB
    T --> DB
    C --> JL[(JSONL conversation logs)]
    R --> FS[(Local photo storage)]
```

## 2. Tech stack

### Backend

| Area | Pilihan | Alasan |
|---|---|---|
| Runtime | Python 3.12 | Stabil dan memiliki ekosistem NLP kuat |
| API | FastAPI + Uvicorn | Typed API, validation, dan OpenAPI otomatis |
| Schema | Pydantic v2 | Validasi request/response dan configuration |
| NLP/data | scikit-learn, pandas, NumPy | TF-IDF, Logistic Regression, metrik, manipulasi dataset |
| Tokenization | Regex tokenizer sendiri | Transparan untuk laporan dan tanpa download corpus |
| Persistence | SQLAlchemy 2 + Alembic | ORM dan database migration |
| Database | MySQL 8 | Sesuai pengalaman developer dan cocok untuk data transaksi |
| Model artifact | joblib | Menyimpan pipeline sklearn yang telah dilatih |
| Conversation log | JSON Lines | Append-friendly dan memenuhi P5 |
| Testing | pytest, pytest-asyncio, HTTPX | Unit dan integration/API testing |
| Quality | Ruff + mypy | Lint/format dan static type checking |
| Dependency manager | `uv` | Lockfile cepat dan reproducible |

Model utama adalah `TfidfVectorizer` + `LogisticRegression`. Multinomial Naive
Bayes boleh ditambahkan sebagai baseline pembanding, tetapi bukan dependency
runtime utama.

### Frontend

| Area | Pilihan |
|---|---|
| Framework | Next.js 16, App Router, React |
| Language | TypeScript strict |
| Package manager | Bun |
| Styling | Tailwind CSS |
| Components | shadcn/ui + Radix primitives |
| Forms | React Hook Form + Zod bila form non-chat diperlukan |
| Server state | Native `fetch`; TanStack Query hanya jika kebutuhan cache meningkat |
| Quality | ESLint, Prettier, Husky, lint-staged |
| Testing | Vitest + Testing Library; Playwright untuk happy path |

Chat state utama tetap berasal dari backend. Frontend hanya menyimpan
`conversation_id`, menampilkan message, mengirim input/quick reply, dan
menangani upload.

## 3. Proposed repository structure

```text
reservation-chatbot/
├── apps/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── shared/
│   │   │   │   ├── config.py
│   │   │   │   ├── database.py
│   │   │   │   ├── errors.py
│   │   │   │   └── observability.py
│   │   │   └── modules/
│   │   │       ├── catalog/
│   │   │       ├── conversation/
│   │   │       ├── nlp/
│   │   │       ├── reservation/
│   │   │       ├── pricing/
│   │   │       └── ticketing/
│   │   ├── migrations/
│   │   ├── scripts/
│   │   │   ├── generate_dataset.py
│   │   │   ├── train_model.py
│   │   │   └── evaluate_model.py
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── uv.lock
│   └── frontend/
│       ├── src/
│       │   ├── app/
│       │   ├── components/
│       │   │   ├── landing/
│       │   │   ├── chat/
│       │   │   └── ui/
│       │   ├── features/chat/
│       │   ├── lib/
│       │   └── types/
│       ├── public/
│       ├── package.json
│       └── bun.lock
├── data/
│   ├── raw/intents.csv
│   ├── processed/
│   ├── logs/.gitkeep
│   └── README.md
├── artifacts/
│   ├── models/.gitkeep
│   └── evaluation/.gitkeep
├── storage/uploads/.gitkeep
├── docs/
├── compose.yaml
├── .env.example
└── README.md
```

Generated dataset boleh di-commit untuk kebutuhan penilaian. Conversation log,
upload pengguna, database volume, dan model binary sebaiknya di-`.gitignore`.
Hasil evaluasi seperti CSV metrik dan PNG confusion matrix boleh di-commit
sebagai bukti UAS setelah model dilatih.

## 4. Backend modules

| Module | Tanggung jawab | Tidak bertanggung jawab |
|---|---|---|
| `nlp` | Preprocessing, load pipeline, predict intent/confidence | Menentukan langkah reservasi |
| `conversation` | State machine, next prompt, fallback, context/session, log turn | Menyimpan transaksi final langsung |
| `catalog` | Jenis layanan, spesialisasi, sesi, available survey slots | Kalkulasi total |
| `reservation` | Validasi slot lintas field, draft dan final reservation | Klasifikasi intent |
| `pricing` | Aturan estimasi harga harian | Membuat tiket |
| `ticketing` | Nomor tiket, status lifecycle, lookup | Mengirim email nyata |
| `shared` | Config, DB session, error model, clock/ID abstraction | Business rule spesifik |

Dependency direction:

```text
api -> application service -> domain rules -> repository interface
                                      infrastructure implements repository
conversation -> nlp/catalog/reservation application interfaces
reservation -> pricing and ticketing application interfaces
```

Tidak perlu message broker, service discovery, atau network call antar-module
untuk MVP.

## 5. API contract awal

Base path: `/api/v1`.

### Endpoints

| Method | Path | Fungsi |
|---|---|---|
| `GET` | `/health` | Liveness sederhana |
| `GET` | `/ready` | Cek DB dan model sudah dimuat |
| `POST` | `/conversations` | Membuat session dan memperoleh prompt awal |
| `POST` | `/conversations/{id}/messages` | Mengirim teks/quick reply dan mendapat respons berikutnya |
| `GET` | `/conversations/{id}` | Memulihkan message dan state session |
| `POST` | `/conversations/{id}/attachments` | Upload foto masalah untuk draft aktif |
| `GET` | `/catalog/services` | Katalog layanan dan spesialisasi |
| `GET` | `/catalog/survey-slots` | Pilihan tanggal/jam survei |
| `GET` | `/tickets/{ticket_number}` | Melihat ringkasan dan status tiket |
| `GET` | `/nlp/model-info` | Metadata model/dataset untuk demo UAS |

Contoh response message:

```json
{
  "conversation_id": "01J...",
  "state": "HARIAN_ASK_SPECIALIZATION",
  "messages": [
    {
      "id": "01J...",
      "sender": "bot",
      "text": "Spesialisasi tukang apa yang Anda butuhkan?"
    }
  ],
  "quick_replies": [
    {"label": "Listrik", "value": "listrik"},
    {"label": "Plumbing", "value": "plumbing"}
  ],
  "collected_slots": {
    "service_type": "harian"
  },
  "ticket": null,
  "error": null
}
```

Frontend tidak menentukan `state` berikutnya dan tidak mengirim total harga.

### Error envelope

```json
{
  "error": {
    "code": "INVALID_SLOT_VALUE",
    "message": "Tanggal selesai tidak boleh sebelum tanggal mulai.",
    "field": "end_date",
    "retryable": true
  }
}
```

## 6. Data model

### Relational entities

```mermaid
erDiagram
    CONVERSATION ||--o| RESERVATION_DRAFT : owns
    RESERVATION_DRAFT ||--o| RESERVATION : becomes
    RESERVATION ||--|| TICKET : creates
    RESERVATION ||--o| ATTACHMENT : contains
    SERVICE ||--o{ SPECIALIZATION : offers

    CONVERSATION {
        string id PK
        string state
        json context
        datetime created_at
        datetime updated_at
        datetime expires_at
    }
    RESERVATION_DRAFT {
        string id PK
        string conversation_id FK
        string service_type
        json slots
        datetime updated_at
    }
    RESERVATION {
        string id PK
        string service_type
        string customer_id
        string phone_number_encrypted
        json details
        decimal estimated_price
        datetime created_at
    }
    TICKET {
        string id PK
        string reservation_id FK
        string ticket_number UK
        string status
        datetime created_at
    }
    ATTACHMENT {
        string id PK
        string reservation_id FK
        string stored_name
        string content_type
        int size_bytes
    }
```

Untuk menjaga scope, detail unik Borongan/Harian disimpan pada JSON tervalidasi
Pydantic. Jika sistem berkembang, detail dapat dinormalisasi menjadi table
terpisah.

### Ticket status MVP

```text
MENUNGGU_KONFIRMASI --(pengguna setuju)--> MENUNGGU_PEMBAYARAN
```

Status pembayaran selanjutnya hanya placeholder dan tidak berubah otomatis
karena payment gateway berada di luar scope.

## 7. Conversation persistence dan logging

State/session disimpan di MySQL agar dapat dipulihkan. Selain itu, setiap turn
di-append ke `data/logs/conversations-YYYY-MM-DD.jsonl`.

Contoh satu event log:

```json
{
  "event_id": "01J...",
  "timestamp": "2026-07-28T10:15:00+07:00",
  "conversation_id": "01J...",
  "turn": 4,
  "sender": "user",
  "raw_text": "nomor WA saya 0812****7890",
  "normalized_text": "nomor wa saya 0812 masked 7890",
  "predicted_intent": null,
  "confidence": null,
  "state_before": "BORONGAN_ASK_PHONE",
  "state_after": "BORONGAN_ASK_BUILDING",
  "extracted_slots": {"phone_number": "+62812****7890"},
  "response_text": "Jenis bangunannya rumah, apartemen, atau ruko?",
  "model_version": "intent-v1"
}
```

Log dataset/training dan log percakapan runtime adalah dua hal berbeda.
Runtime log tidak otomatis dimasukkan kembali ke training set karena mungkin
mengandung data pribadi dan label yang belum diverifikasi.

## 8. Security dan privacy baseline

- Masking nomor telepon pada JSONL dan application log.
- Nomor lengkap hanya disimpan pada database; encryption at rest menjadi
  target foundation, minimal jangan pernah masuk source control.
- Validasi MIME, extension, magic bytes, ukuran, serta generated filename untuk
  upload. File tidak dieksekusi dan tidak disajikan dari path mentah.
- CORS hanya mengizinkan origin frontend yang dikonfigurasi.
- Rate limit ringan per IP/session untuk endpoint message dan upload.
- Tidak me-render text bot/user sebagai raw HTML.
- Secret dan DSN hanya melalui environment variable.
- Retention log/upload didokumentasikan; untuk demo lokal dapat dibersihkan
  manual setelah penilaian.

## 9. Deployment dan local development

`compose.yaml` menjalankan MySQL dan, bila diinginkan, backend/frontend.
Development normal dapat tetap menjalankan:

```text
bun --cwd apps/frontend dev
uv run --project apps/backend uvicorn app.main:app --reload
docker compose up mysql
```

Environment minimal:

```text
DATABASE_URL
FRONTEND_ORIGIN
MODEL_PATH
CONVERSATION_LOG_DIR
UPLOAD_DIR
MAX_UPLOAD_MB
APP_TIMEZONE=Asia/Jakarta
```

CI foundation menjalankan backend lint/typecheck/test, frontend
lint/typecheck/test, dan build frontend. Training model tidak dijalankan pada
setiap commit; artifact dibuat melalui task eksplisit dan diverifikasi metadata
versinya.

## 10. Architecture decision records yang disarankan

- ADR-001: Modular monolith dalam monorepo.
- ADR-002: TF-IDF + Logistic Regression untuk intent classifier.
- ADR-003: Deterministic state machine untuk transaksi reservasi.
- ADR-004: MySQL untuk transaksi dan JSONL untuk evidence log.
- ADR-005: Harga dan availability sebagai configuration MVP.

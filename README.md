# Reservation Chatbot

Monorepo web chatbot untuk bertanya tentang layanan tukang dan melakukan
reservasi Jasa Borongan atau Tukang Harian. Project ini disiapkan sebagai UAS
mata kuliah Natural Language Processing.

## Stack

- Frontend: Next.js 16 App Router, React 19, TypeScript strict, Tailwind CSS,
  shadcn/ui, dan Bun.
- Backend: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, dan `uv`.
- Database: MySQL 8.4 melalui Docker Compose.
- Quality: Ruff, mypy, pytest, ESLint, Prettier, Vitest, Husky, lint-staged,
  dan GitHub Actions.

## Prasyarat

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Bun 1.3
- Docker dengan Compose plugin

## Setup

```bash
cp .env.example .env
make install
make db-up
make migrate
```

Tunggu container MySQL berstatus sehat sebelum menjalankan migration. Nilai
default dalam `.env.example` hanya untuk development lokal dan harus diganti
pada environment lain.

## Menjalankan aplikasi

Jalankan backend dan frontend pada terminal terpisah:

```bash
make dev-backend
make dev-frontend
```

- Frontend: <http://localhost:3000>
- OpenAPI: <http://localhost:8000/docs>
- Liveness: <http://localhost:8000/api/v1/health>
- Readiness: <http://localhost:8000/api/v1/ready>

`/health` hanya menandakan process API hidup. `/ready` melakukan query ringan
ke database dan memberikan HTTP 503 dengan error envelope terstruktur bila
database belum siap.

## Developer commands

```bash
make lint          # Ruff dan ESLint
make format        # Ruff formatter dan Prettier
make format-check  # verifikasi formatting tanpa mengubah file
make typecheck     # mypy strict dan TypeScript strict
make test          # pytest dan Vitest
make build         # Next.js production build
make check         # semua quality gate di atas
make db-logs       # ikuti log MySQL
make db-down       # hentikan service Docker Compose
make dataset-generate # hasilkan ulang dataset intent 240 baris
make dataset-review   # audit distribusi, duplicate, dan variasi
make dataset-analyze  # analisis distribusi intent dan panjang teks
make preprocessing-examples # export contoh preprocessing
make nlp-data-artifacts # jalankan seluruh tahap data NLP-01–NLP-06
make nlp-train       # train TF-IDF + Logistic Regression dan export evaluasi/model
make nlp-artifacts   # generate seluruh data, model, dan evaluasi NLP baseline
```

`make nlp-train` memakai stratified split 80/20 dan seed 42, melakukan
5-fold cross-validation hanya pada training split, lalu menulis:

- pipeline model dan metadata versioned ke `artifacts/models/`;
- accuracy, classification report, confusion matrix CSV/PNG,
  misclassification, dan distribusi split ke `artifacts/evaluation/`.

Loader runtime tersedia melalui
`app.modules.nlp.model.load_intent_model`. File `joblib` hanya boleh dimuat dari
sumber lokal yang dipercaya; loader memverifikasi checksum artifact terhadap
metadata sebelum inference.

Conversation core menyediakan endpoint berikut:

```text
POST /api/v1/conversations
GET  /api/v1/conversations/{conversation_id}
POST /api/v1/conversations/{conversation_id}/messages
```

Session conversation masih disimpan dalam memory process. Persistensi dan
restore lintas restart akan ditambahkan pada task `CONV-08`. FAQ free-text
memakai model intent beserta confidence threshold; input ber-confidence rendah
dikembalikan sebagai state `FALLBACK` dengan pilihan topik terarah.

Untuk migration baru:

```bash
make migration message="describe_change"
make migrate
```

Husky menjalankan lint-staged sebelum commit. CI menjalankan lint, format
check, typecheck, test, dan frontend production build pada setiap push dan
pull request.

## Struktur repository

```text
apps/backend/   FastAPI, shared infrastructure, modules, migrations, tests
apps/frontend/  Next.js App Router, shadcn/ui baseline, tests
data/           raw/processed dataset dan runtime conversation logs
artifacts/      model serta evaluation output
storage/        runtime upload
docs/           perencanaan, arsitektur, dan traceability UAS
```

Dokumentasi perencanaan:

- [Documentation index](docs/README.md)
- [MVP plan](docs/01-mvp-plan.md)
- [Architecture foundation](docs/02-architecture-foundation.md)
- [NLP and dialog design](docs/03-nlp-and-dialog-design.md)
- [Intent taxonomy and labeling guideline](docs/06-intent-labeling-guideline.md)
- [Task breakdown](docs/04-task-breakdown.md)
- [UAS traceability matrix](docs/05-uas-traceability.md)
- [API contract convention](docs/api-contract/README.md)
- [OpenAPI contract](docs/api-contract/openapi.yml)
- [Sequence diagram](docs/diagram/sequence-diagram.md)
- [Entity Relationship Diagram](docs/diagram/erd.md)

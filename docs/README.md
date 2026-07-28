# Planning Documentation

Dokumentasi ini adalah source of truth untuk fase MVP `reservation-chatbot`.

## Urutan baca

1. [MVP plan](01-mvp-plan.md) — tujuan, scope, asumsi, dan acceptance criteria.
2. [Architecture foundation](02-architecture-foundation.md) — struktur
   modular monolith, komponen, data, API, dan keputusan teknologi.
3. [NLP and dialog design](03-nlp-and-dialog-design.md) — intent, dataset,
   preprocessing, slot filling, state dialog, dan evaluasi model.
4. [Task breakdown](04-task-breakdown.md) — urutan implementasi dan Definition
   of Done.
5. [UAS traceability](05-uas-traceability.md) — pemetaan artefak ke P1–P5.

## Kontrak dan diagram

- [API contract convention](api-contract/README.md) — success/error envelope
  dan application code yang digunakan project.
- [OpenAPI contract](api-contract/openapi.yml) — kontrak normatif endpoint dan
  schema.
- [Sequence diagram](diagram/sequence-diagram.md) — interaksi session, FAQ,
  reservasi Harian/Borongan, upload, restore, dan lookup tiket.
- [Entity Relationship Diagram](diagram/erd.md) — model relational, data
  dictionary, constraint, dan index.

## Prinsip perencanaan

- MVP harus dapat didemokan end-to-end tanpa layanan eksternal berbayar.
- Machine learning dipakai untuk klasifikasi intent, sedangkan alur transaksi
  reservasi dikendalikan oleh state machine agar dapat diprediksi.
- Semua metrik evaluasi berasal dari test set yang tidak dipakai saat training.
- Tiket dan kalkulasi harga dihasilkan oleh backend, bukan dipercaya dari
  input frontend.
- Hal yang belum didefinisikan oleh soal dibuat configurable dan diberi label
  sebagai asumsi.

## Status

| Area | Status |
|---|---|
| Product scope | Planned |
| Architecture | Planned |
| Dataset generation | Not started |
| Backend implementation | Not started |
| Frontend implementation | Not started |
| Model evaluation | Not started |
| UAS report/evidence | Not started |

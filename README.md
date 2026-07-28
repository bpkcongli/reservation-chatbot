# Reservation Chatbot

Web chatbot untuk bertanya tentang layanan tukang dan melakukan reservasi
Jasa Borongan atau Tukang Harian. Project ini disiapkan sebagai UAS mata
kuliah Natural Language Processing.

Saat ini repository berada pada fase perencanaan. Dokumentasi berikut menjadi
acuan sebelum development dimulai:

- [Documentation index](docs/README.md)
- [MVP plan](docs/01-mvp-plan.md)
- [Architecture foundation](docs/02-architecture-foundation.md)
- [NLP and dialog design](docs/03-nlp-and-dialog-design.md)
- [Task breakdown](docs/04-task-breakdown.md)
- [UAS traceability matrix](docs/05-uas-traceability.md)

Keputusan stack utama:

- Frontend: Next.js 16 App Router, TypeScript, Tailwind CSS, shadcn/ui, Bun.
- Backend: Python 3.12, FastAPI, scikit-learn, pandas, Pydantic, SQLAlchemy.
- NLP: TF-IDF + Logistic Regression dan rule-based slot filling.
- Storage: MySQL untuk data aplikasi serta JSONL untuk log percakapan.

> Belum ada kode aplikasi pada fase ini. Nilai harga, slot jadwal, dan aturan
> bisnis yang belum diberikan akan diperlakukan sebagai konfigurasi/asumsi MVP,
> bukan sebagai kebijakan bisnis final.

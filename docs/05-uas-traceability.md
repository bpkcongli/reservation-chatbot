# UAS Traceability Matrix

Dokumen ini memastikan implementasi dan laporan nantinya menjawab seluruh
requirement, bukan hanya menghasilkan aplikasi yang berjalan.

| Pertanyaan | Requirement | Rencana artefak/evidence | Task |
|---|---|---|---|
| P1 | Masalah nyata | Problem statement dan target user di MVP plan | `DOC-08` |
| P1 | Kebutuhan fungsional | Scope informasi, dua reservasi, tiket | `RES-*`, `WEB-*` |
| P1 | Flow dialog/state diagram | Mermaid general, Borongan, Harian | `CONV-01` |
| P1 | Struktur dataset intent | CSV schema dan taxonomy 8 intent | `NLP-01..03` |
| P1 | Struktur log percakapan | JSONL event schema | `CONV-07` |
| P2 | Minimal 200 data | Target 240 utterance | `NLP-02` |
| P2 | Minimal 4 intent | Target 8 intent | `NLP-01` |
| P2 | Distribusi per intent | Tabel dan generated distribution CSV | `NLP-04` |
| P2 | Lowercase, cleaning, tokenization | Shared preprocessing pipeline | `NLP-05` |
| P2 | Representasi teks | TF-IDF unigram/bigram | `NLP-07` |
| P2 | Contoh sebelum/sesudah | `preprocessing-examples.csv` | `NLP-06` |
| P3 | Intent classification | Logistic Regression pipeline | `NLP-07`, `CONV-03` |
| P3 | Rule-based slot filling | Regex/pattern dan state-aware extractor | `CONV-05..06` |
| P3 | Multi-turn | Persisted finite state machine | `CONV-01..09` |
| P3 | Minimal satu konfirmasi | Summary → ya/ubah/batal | `RES-03..04` |
| P4 | Accuracy | `metrics.json` | `NLP-09` |
| P4 | Precision/recall/F1 | Classification report per class + averages | `NLP-09` |
| P4 | Confusion matrix | CSV dan PNG | `NLP-09` |
| P4 | Intent paling sering salah | Pasangan off-diagonal terbesar + examples | `DOC-04` |
| P4 | Penyebab kesalahan | Evidence-based error analysis | `DOC-04..05` |
| P4 | Keterbatasan sistem | NLP/dialog/business limitations | `DOC-05` |
| P5 | Input pengguna | Chat composer + quick reply | `WEB-02..05` |
| P5 | Respons chatbot | Message renderer | `WEB-03` |
| P5 | Log CSV/JSON | Masked JSONL per turn | `CONV-07`, `DOC-06` |
| Tambahan | Landing page | Hero, layanan, cara kerja, CTA | `WEB-01` |
| Tambahan | Bukti reservasi | Ticket card number/status | `TKT-*`, `WEB-07` |

## Checklist evidence akhir

- [ ] `data/raw/intents.csv` memiliki jumlah yang dilaporkan.
- [ ] Distribution chart/table dihasilkan dari dataset yang sama.
- [ ] Screenshot contoh preprocessing berasal dari output script.
- [ ] `metrics.json` dan classification report konsisten.
- [ ] Confusion matrix memiliki label intent yang terbaca.
- [ ] Analisis misclassification menyebut contoh aktual, bukan dugaan saja.
- [ ] Log percakapan demo sudah dimasking.
- [ ] Screenshot flow menunjukkan prompt awal dua pilihan.
- [ ] Screenshot flow menunjukkan konfirmasi sebelum tiket.
- [ ] Screenshot akhir menunjukkan nomor dan status tiket.
- [ ] README berisi perintah setup, train, evaluate, run, dan test.

## Catatan laporan

Bagian P4 baru dapat difinalisasi setelah implementasi dan eksperimen. Dokumen
planning hanya mencatat metode analisis dan hipotesis; nilai metrik serta intent
yang paling sering salah tidak boleh direkayasa sebelum model dijalankan.

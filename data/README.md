# Data

- `raw/` berisi dataset sumber yang boleh di-version-control.
- `processed/` berisi hasil transformasi yang reproducible.
- `reviews/` berisi hasil audit otomatis dan catatan review manual dataset.
- `logs/` berisi conversation log runtime dan diabaikan oleh Git.

Dataset intent dibuat deterministik dari utterance yang ditulis manual:

```bash
make dataset-generate
make dataset-review
make dataset-analyze
make preprocessing-examples
```

`data/raw/intents.csv` adalah output generator dengan tepat 240 baris.
`data/reviews/intents-audit.json` dan daftar kandidat near-duplicate selalu
dihasilkan ulang sebelum keputusan review manual dicatat.

Hasil analisis dan contoh preprocessing disimpan di `artifacts/evaluation/`:

- `dataset-analysis.json`: ringkasan distribusi dan panjang teks.
- `dataset-distribution.csv`: jumlah serta persentase per intent.
- `text-lengths.csv`: panjang karakter/token setiap utterance.
- `text-length-summary.csv`: statistik keseluruhan dan per intent.
- `preprocessing-examples.csv`: contoh raw, cleaned, dan token hasil pipeline.

Jalankan `make nlp-data-artifacts` untuk menghasilkan ulang seluruh dataset,
review, analisis, dan contoh preprocessing dengan satu command.

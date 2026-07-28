# Data

- `raw/` berisi dataset sumber yang boleh di-version-control.
- `processed/` berisi hasil transformasi yang reproducible.
- `reviews/` berisi hasil audit otomatis dan catatan review manual dataset.
- `logs/` berisi conversation log runtime dan diabaikan oleh Git.

Dataset intent dibuat deterministik dari utterance yang ditulis manual:

```bash
make dataset-generate
make dataset-review
```

`data/raw/intents.csv` adalah output generator dengan tepat 240 baris.
`data/reviews/intents-audit.json` dan daftar kandidat near-duplicate selalu
dihasilkan ulang sebelum keputusan review manual dicatat.

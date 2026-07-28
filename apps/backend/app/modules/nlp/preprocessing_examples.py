"""Reproducible before/after examples for preprocessing evidence."""

import csv
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from app.modules.nlp.preprocessing import preprocess_text

DEFAULT_EXAMPLES: tuple[str, ...] = (
    "Halo Kak!! Ada jasa tukang listrik?",
    "Saya mau BOOKING tukang utk 02/08/2026.",
    "Cek tiket TKT-20260728-AB12CD dong",
    "Hubungi 0812 3456 7890 atau CS@example.com",
    "<b>Lihat info</b> di https://contoh.id/layanan",
)


@dataclass(frozen=True, slots=True)
class PreprocessingExample:
    """One exported preprocessing example."""

    example_id: str
    original_text: str
    cleaned_text: str
    tokens: str


def build_preprocessing_examples(
    examples: Sequence[str] = DEFAULT_EXAMPLES,
) -> tuple[PreprocessingExample, ...]:
    """Preprocess examples and serialize tokens as valid JSON."""

    rows: list[PreprocessingExample] = []
    for index, text in enumerate(examples, start=1):
        result = preprocess_text(text)
        rows.append(
            PreprocessingExample(
                example_id=f"example-{index:02d}",
                original_text=result.original,
                cleaned_text=result.cleaned,
                tokens=json.dumps(result.tokens, ensure_ascii=False, separators=(",", ":")),
            )
        )
    return tuple(rows)


def write_preprocessing_examples(
    destination: Path,
    examples: Sequence[str] = DEFAULT_EXAMPLES,
) -> int:
    """Write generated preprocessing examples and return their count."""

    rows = build_preprocessing_examples(examples)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fields = ("example_id", "original_text", "cleaned_text", "tokens")
    with destination.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            {
                "example_id": row.example_id,
                "original_text": row.original_text,
                "cleaned_text": row.cleaned_text,
                "tokens": row.tokens,
            }
            for row in rows
        )
    return len(rows)

"""Intent distribution and text-length analysis for the raw dataset."""

import csv
import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import median

from app.modules.nlp.dataset import UtteranceRecord
from app.modules.nlp.preprocessing import preprocess_text
from app.modules.nlp.review import load_records, validate_records
from app.modules.nlp.taxonomy import EXPECTED_DISTRIBUTION


@dataclass(frozen=True, slots=True)
class DistributionRow:
    """Intent count and percentage."""

    intent: str
    count: int
    percentage: float


@dataclass(frozen=True, slots=True)
class TextLengthRow:
    """Character and token lengths for one utterance."""

    id: str
    intent: str
    character_count: int
    token_count: int


@dataclass(frozen=True, slots=True)
class TextLengthSummary:
    """Aggregate character and token lengths for a dataset scope."""

    scope: str
    count: int
    min_characters: int
    max_characters: int
    mean_characters: float
    median_characters: float
    min_tokens: int
    max_tokens: int
    mean_tokens: float
    median_tokens: float


@dataclass(frozen=True, slots=True)
class DatasetAnalysis:
    """Complete deterministic dataset analysis."""

    total: int
    sha256: str
    distribution: tuple[DistributionRow, ...]
    text_lengths: tuple[TextLengthRow, ...]
    length_summary: tuple[TextLengthSummary, ...]


def _rounded_mean(values: list[int]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def _rounded_median(values: list[int]) -> float:
    if not values:
        return 0.0
    return round(float(median(values)), 2)


def _summarize_lengths(scope: str, rows: list[TextLengthRow]) -> TextLengthSummary:
    character_counts = [row.character_count for row in rows]
    token_counts = [row.token_count for row in rows]
    return TextLengthSummary(
        scope=scope,
        count=len(rows),
        min_characters=min(character_counts, default=0),
        max_characters=max(character_counts, default=0),
        mean_characters=_rounded_mean(character_counts),
        median_characters=_rounded_median(character_counts),
        min_tokens=min(token_counts, default=0),
        max_tokens=max(token_counts, default=0),
        mean_tokens=_rounded_mean(token_counts),
        median_tokens=_rounded_median(token_counts),
    )


def analyze_records(records: list[UtteranceRecord], *, sha256: str = "") -> DatasetAnalysis:
    """Analyze validated records in canonical taxonomy order."""

    issues = validate_records(records)
    if issues:
        issue_codes = ", ".join(issue.code for issue in issues)
        raise ValueError(f"Dataset validation failed: {issue_codes}")

    total = len(records)
    counts = Counter(record.intent for record in records)
    distribution = tuple(
        DistributionRow(
            intent=intent,
            count=counts[intent],
            percentage=round((counts[intent] / total) * 100, 2),
        )
        for intent in EXPECTED_DISTRIBUTION
    )
    text_lengths = tuple(
        TextLengthRow(
            id=record.id,
            intent=record.intent,
            character_count=len(record.text),
            token_count=len(preprocess_text(record.text).tokens),
        )
        for record in records
    )
    all_rows = list(text_lengths)
    summaries = [_summarize_lengths("all", all_rows)]
    summaries.extend(
        _summarize_lengths(
            intent,
            [row for row in all_rows if row.intent == intent],
        )
        for intent in EXPECTED_DISTRIBUTION
    )
    return DatasetAnalysis(
        total=total,
        sha256=sha256,
        distribution=distribution,
        text_lengths=text_lengths,
        length_summary=tuple(summaries),
    )


def analyze_dataset(source: Path) -> DatasetAnalysis:
    """Load, validate, and analyze a raw dataset CSV."""

    records, load_issues = load_records(source)
    if load_issues:
        issue_codes = ", ".join(issue.code for issue in load_issues)
        raise ValueError(f"Dataset loading failed: {issue_codes}")
    content_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    return analyze_records(records, sha256=content_hash)


def _write_csv(
    destination: Path,
    fieldnames: tuple[str, ...],
    rows: Iterable[Mapping[str, object]],
) -> None:
    with destination.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_analysis_artifacts(analysis: DatasetAnalysis, destination: Path) -> None:
    """Write distribution and text-length artifacts."""

    destination.mkdir(parents=True, exist_ok=True)
    _write_csv(
        destination / "dataset-distribution.csv",
        ("intent", "count", "percentage"),
        (asdict(row) for row in analysis.distribution),
    )
    _write_csv(
        destination / "text-lengths.csv",
        ("id", "intent", "character_count", "token_count"),
        (asdict(row) for row in analysis.text_lengths),
    )
    _write_csv(
        destination / "text-length-summary.csv",
        (
            "scope",
            "count",
            "min_characters",
            "max_characters",
            "mean_characters",
            "median_characters",
            "min_tokens",
            "max_tokens",
            "mean_tokens",
            "median_tokens",
        ),
        (asdict(row) for row in analysis.length_summary),
    )

    summary = {
        "total": analysis.total,
        "sha256": analysis.sha256,
        "distribution": [asdict(row) for row in analysis.distribution],
        "text_length_summary": [asdict(row) for row in analysis.length_summary],
    }
    (destination / "dataset-analysis.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

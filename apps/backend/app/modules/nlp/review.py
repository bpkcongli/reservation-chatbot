"""Dataset integrity and near-duplicate review utilities."""

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path

from app.modules.nlp.dataset import CSV_FIELDS, DATASET_SOURCE, UtteranceRecord
from app.modules.nlp.taxonomy import EXPECTED_DISTRIBUTION, TOTAL_UTTERANCES

ID_PATTERN = re.compile(r"^utt-\d{4}$")
TOKEN_PATTERN = re.compile(r"\w+", flags=re.UNICODE)
QUESTION_STARTERS = {
    "apa",
    "apakah",
    "bagaimana",
    "berapa",
    "bisakah",
    "boleh",
    "di",
    "kapan",
    "siapa",
}
CONVERSATIONAL_MARKERS = {
    "aja",
    "dong",
    "gimana",
    "kak",
    "mau",
    "min",
    "nih",
    "pengen",
    "sih",
    "ya",
}
FORMAL_MARKERS = {"apakah", "dapat", "hendak", "ingin", "mohon", "saya", "tolong"}
TYPO_MARKERS = {"boking", "brp", "reservsi", "trf", "tukng"}


@dataclass(frozen=True, slots=True)
class ReviewIssue:
    """A blocking dataset integrity problem."""

    code: str
    message: str
    record_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class NearDuplicate:
    """A candidate pair requiring human adjudication."""

    id_a: str
    intent_a: str
    text_a: str
    id_b: str
    intent_b: str
    text_b: str
    sequence_similarity: float
    token_jaccard: float


@dataclass(frozen=True, slots=True)
class VariationSummary:
    """Small, interpretable indicators used during manual variation review."""

    intent: str
    count: int
    min_tokens: int
    max_tokens: int
    mean_tokens: float
    question_like: int
    conversational: int
    formal: int
    typo_examples: int


@dataclass(frozen=True, slots=True)
class DatasetReview:
    """Complete reproducible review result."""

    row_count: int
    sha256: str
    distribution: dict[str, int]
    issues: tuple[ReviewIssue, ...]
    near_duplicates: tuple[NearDuplicate, ...]
    variation: tuple[VariationSummary, ...]


def normalize_for_comparison(text: str) -> str:
    """Normalize text only for duplicate comparison, not model preprocessing."""

    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(TOKEN_PATTERN.findall(normalized))


def _token_set(text: str) -> set[str]:
    return set(normalize_for_comparison(text).split())


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    if not union:
        return 1.0
    return len(left & right) / len(union)


def load_records(source: Path) -> tuple[list[UtteranceRecord], list[ReviewIssue]]:
    """Load a raw CSV while retaining schema errors for the audit report."""

    issues: list[ReviewIssue] = []
    records: list[UtteranceRecord] = []
    with source.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        found_columns = tuple(reader.fieldnames or ())
        if found_columns != CSV_FIELDS:
            issues.append(
                ReviewIssue(
                    code="invalid_columns",
                    message=f"Expected columns {CSV_FIELDS}, found {found_columns}.",
                )
            )
            return records, issues

        for row_number, row in enumerate(reader, start=2):
            if any(row[field] is None for field in CSV_FIELDS):
                issues.append(
                    ReviewIssue(
                        code="malformed_row",
                        message=f"CSV row {row_number} has a missing field.",
                    )
                )
                continue
            records.append(
                UtteranceRecord(
                    id=row["id"] or "",
                    text=row["text"] or "",
                    intent=row["intent"] or "",
                    source=row["source"] or "",
                )
            )
    return records, issues


def validate_records(records: list[UtteranceRecord]) -> list[ReviewIssue]:
    """Check schema-level invariants and exact duplicates."""

    issues: list[ReviewIssue] = []
    if len(records) != TOTAL_UTTERANCES:
        issues.append(
            ReviewIssue(
                code="invalid_total",
                message=f"Expected {TOTAL_UTTERANCES} rows, found {len(records)}.",
            )
        )

    ids = [record.id for record in records]
    duplicate_ids = tuple(
        sorted(record_id for record_id, count in Counter(ids).items() if count > 1)
    )
    if duplicate_ids:
        issues.append(
            ReviewIssue(
                code="duplicate_id",
                message="Record IDs must be unique.",
                record_ids=duplicate_ids,
            )
        )

    invalid_ids = tuple(record_id for record_id in ids if ID_PATTERN.fullmatch(record_id) is None)
    if invalid_ids:
        issues.append(
            ReviewIssue(
                code="invalid_id",
                message="Record IDs must use the utt-NNNN format.",
                record_ids=invalid_ids,
            )
        )

    expected_ids = [f"utt-{index:04d}" for index in range(1, len(records) + 1)]
    if ids != expected_ids:
        issues.append(
            ReviewIssue(
                code="non_contiguous_ids",
                message="Record IDs must be ordered and contiguous from utt-0001.",
            )
        )

    blank_text_ids = tuple(record.id for record in records if not record.text.strip())
    if blank_text_ids:
        issues.append(
            ReviewIssue(
                code="blank_text",
                message="Utterance text cannot be blank.",
                record_ids=blank_text_ids,
            )
        )

    unknown_label_ids = tuple(
        record.id for record in records if record.intent not in EXPECTED_DISTRIBUTION
    )
    if unknown_label_ids:
        issues.append(
            ReviewIssue(
                code="unknown_label",
                message="Every label must be part of the canonical taxonomy.",
                record_ids=unknown_label_ids,
            )
        )

    distribution = Counter(record.intent for record in records)
    if {label: distribution[label] for label in EXPECTED_DISTRIBUTION} != EXPECTED_DISTRIBUTION:
        issues.append(
            ReviewIssue(
                code="invalid_distribution",
                message=(
                    f"Expected distribution {EXPECTED_DISTRIBUTION}, "
                    f"found {dict(sorted(distribution.items()))}."
                ),
            )
        )

    invalid_source_ids = tuple(record.id for record in records if record.source != DATASET_SOURCE)
    if invalid_source_ids:
        issues.append(
            ReviewIssue(
                code="invalid_source",
                message=f"Every generated row must use source={DATASET_SOURCE}.",
                record_ids=invalid_source_ids,
            )
        )

    normalized_to_ids: dict[str, list[str]] = {}
    for record in records:
        normalized_to_ids.setdefault(normalize_for_comparison(record.text), []).append(record.id)
    for normalized, matching_ids in sorted(normalized_to_ids.items()):
        if normalized and len(matching_ids) > 1:
            issues.append(
                ReviewIssue(
                    code="exact_duplicate",
                    message=f"Duplicate normalized text: {normalized!r}.",
                    record_ids=tuple(matching_ids),
                )
            )
    return issues


def find_near_duplicates(
    records: list[UtteranceRecord],
    *,
    sequence_threshold: float = 0.88,
    token_jaccard_threshold: float = 0.80,
) -> list[NearDuplicate]:
    """Return similar non-identical pairs for human review."""

    candidates: list[NearDuplicate] = []
    normalized = [normalize_for_comparison(record.text) for record in records]
    token_sets = [_token_set(record.text) for record in records]

    for left_index, left in enumerate(records):
        for right_index in range(left_index + 1, len(records)):
            right = records[right_index]
            if normalized[left_index] == normalized[right_index]:
                continue

            sequence_similarity = SequenceMatcher(
                None,
                normalized[left_index],
                normalized[right_index],
                autojunk=False,
            ).ratio()
            token_jaccard = _jaccard(token_sets[left_index], token_sets[right_index])
            enough_tokens = min(len(token_sets[left_index]), len(token_sets[right_index])) >= 4
            if sequence_similarity < sequence_threshold and (
                not enough_tokens or token_jaccard < token_jaccard_threshold
            ):
                continue

            candidates.append(
                NearDuplicate(
                    id_a=left.id,
                    intent_a=left.intent,
                    text_a=left.text,
                    id_b=right.id,
                    intent_b=right.intent,
                    text_b=right.text,
                    sequence_similarity=round(sequence_similarity, 4),
                    token_jaccard=round(token_jaccard, 4),
                )
            )

    return sorted(
        candidates,
        key=lambda candidate: (
            -max(candidate.sequence_similarity, candidate.token_jaccard),
            candidate.id_a,
            candidate.id_b,
        ),
    )


def summarize_variation(records: list[UtteranceRecord]) -> list[VariationSummary]:
    """Build per-label indicators to support, not replace, manual review."""

    summaries: list[VariationSummary] = []
    for intent in EXPECTED_DISTRIBUTION:
        texts = [record.text for record in records if record.intent == intent]
        token_lists = [normalize_for_comparison(text).split() for text in texts]
        token_counts = [len(tokens) for tokens in token_lists]
        question_like = sum(
            text.rstrip().endswith("?") or bool(tokens and tokens[0] in QUESTION_STARTERS)
            for text, tokens in zip(texts, token_lists, strict=True)
        )
        conversational = sum(bool(set(tokens) & CONVERSATIONAL_MARKERS) for tokens in token_lists)
        formal = sum(bool(set(tokens) & FORMAL_MARKERS) for tokens in token_lists)
        typo_examples = sum(bool(set(tokens) & TYPO_MARKERS) for tokens in token_lists)
        summaries.append(
            VariationSummary(
                intent=intent,
                count=len(texts),
                min_tokens=min(token_counts, default=0),
                max_tokens=max(token_counts, default=0),
                mean_tokens=round(sum(token_counts) / len(token_counts), 2)
                if token_counts
                else 0.0,
                question_like=question_like,
                conversational=conversational,
                formal=formal,
                typo_examples=typo_examples,
            )
        )
    return summaries


def review_dataset(source: Path) -> DatasetReview:
    """Run the complete deterministic dataset audit."""

    records, load_issues = load_records(source)
    content_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    distribution = Counter(record.intent for record in records)
    return DatasetReview(
        row_count=len(records),
        sha256=content_hash,
        distribution=dict(sorted(distribution.items())),
        issues=tuple([*load_issues, *validate_records(records)]),
        near_duplicates=tuple(find_near_duplicates(records)),
        variation=tuple(summarize_variation(records)),
    )


def write_review_artifacts(review: DatasetReview, destination: Path) -> None:
    """Write machine-readable audit summary and near-duplicate candidates."""

    destination.mkdir(parents=True, exist_ok=True)
    summary_path = destination / "intents-audit.json"
    summary_payload = {
        "row_count": review.row_count,
        "sha256": review.sha256,
        "distribution": review.distribution,
        "issues": [asdict(issue) for issue in review.issues],
        "near_duplicate_count": len(review.near_duplicates),
        "variation": [asdict(summary) for summary in review.variation],
    }
    summary_path.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    candidates_path = destination / "intents-near-duplicates.csv"
    candidate_fields = (
        "id_a",
        "intent_a",
        "text_a",
        "id_b",
        "intent_b",
        "text_b",
        "sequence_similarity",
        "token_jaccard",
    )
    with candidates_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=candidate_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(asdict(candidate) for candidate in review.near_duplicates)

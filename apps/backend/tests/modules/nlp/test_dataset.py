from pathlib import Path

from app.modules.nlp.dataset import UTTERANCES, iter_records, write_dataset
from app.modules.nlp.review import (
    find_near_duplicates,
    normalize_for_comparison,
    review_dataset,
    validate_records,
)
from app.modules.nlp.taxonomy import INTENT_TAXONOMY, TOTAL_UTTERANCES


def test_utterance_source_matches_taxonomy_targets() -> None:
    assert sum(len(texts) for texts in UTTERANCES.values()) == TOTAL_UTTERANCES
    for definition in INTENT_TAXONOMY:
        assert len(UTTERANCES[definition.intent]) == definition.target_count


def test_records_have_stable_contiguous_ids() -> None:
    records = tuple(iter_records())

    assert records[0].id == "utt-0001"
    assert records[-1].id == "utt-0240"
    assert len({record.id for record in records}) == TOTAL_UTTERANCES


def test_generator_is_byte_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"

    assert write_dataset(first) == TOTAL_UTTERANCES
    assert write_dataset(second) == TOTAL_UTTERANCES
    assert first.read_bytes() == second.read_bytes()


def test_generated_dataset_passes_integrity_review(tmp_path: Path) -> None:
    dataset = tmp_path / "intents.csv"
    write_dataset(dataset)

    review = review_dataset(dataset)

    assert review.row_count == TOTAL_UTTERANCES
    assert review.issues == ()
    assert sum(review.distribution.values()) == TOTAL_UTTERANCES


def test_normalized_exact_duplicate_is_rejected() -> None:
    records = list(iter_records())
    records[1] = type(records[1])(
        id=records[1].id,
        text="  HALO!!! ",
        intent=records[1].intent,
        source=records[1].source,
    )

    issues = validate_records(records)

    assert any(issue.code == "exact_duplicate" for issue in issues)


def test_near_duplicate_detection_finds_template_variation() -> None:
    base = next(iter(iter_records()))
    record_type = type(base)
    records = [
        record_type("utt-0001", "Saya mau memesan tukang listrik besok", "start_reservation"),
        record_type("utt-0002", "Saya mau memesan tukang listrik lusa", "start_reservation"),
    ]

    candidates = find_near_duplicates(records)

    assert len(candidates) == 1
    assert candidates[0].id_a == "utt-0001"
    assert candidates[0].id_b == "utt-0002"


def test_comparison_normalization_ignores_case_and_punctuation() -> None:
    assert normalize_for_comparison("  HALO, Kak!! ") == "halo kak"

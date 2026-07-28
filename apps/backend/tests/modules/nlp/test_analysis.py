import csv
import json
from pathlib import Path

from app.modules.nlp.analysis import analyze_dataset, write_analysis_artifacts
from app.modules.nlp.dataset import write_dataset
from app.modules.nlp.preprocessing_examples import (
    build_preprocessing_examples,
    write_preprocessing_examples,
)
from app.modules.nlp.taxonomy import EXPECTED_DISTRIBUTION, TOTAL_UTTERANCES


def test_analysis_reports_distribution_and_text_lengths(tmp_path: Path) -> None:
    dataset = tmp_path / "intents.csv"
    write_dataset(dataset)

    analysis = analyze_dataset(dataset)

    assert analysis.total == TOTAL_UTTERANCES
    assert {row.intent: row.count for row in analysis.distribution} == EXPECTED_DISTRIBUTION
    assert sum(row.percentage for row in analysis.distribution) == 100.0
    assert len(analysis.text_lengths) == TOTAL_UTTERANCES
    assert analysis.length_summary[0].scope == "all"
    assert analysis.length_summary[0].min_tokens >= 1
    assert analysis.length_summary[0].max_tokens >= analysis.length_summary[0].min_tokens


def test_analysis_artifacts_are_deterministic(tmp_path: Path) -> None:
    dataset = tmp_path / "intents.csv"
    first_output = tmp_path / "first"
    second_output = tmp_path / "second"
    write_dataset(dataset)
    analysis = analyze_dataset(dataset)

    write_analysis_artifacts(analysis, first_output)
    write_analysis_artifacts(analysis, second_output)

    expected_files = {
        "dataset-analysis.json",
        "dataset-distribution.csv",
        "text-length-summary.csv",
        "text-lengths.csv",
    }
    assert {path.name for path in first_output.iterdir()} == expected_files
    for filename in expected_files:
        assert (first_output / filename).read_bytes() == (second_output / filename).read_bytes()

    summary = json.loads((first_output / "dataset-analysis.json").read_text(encoding="utf-8"))
    assert summary["total"] == TOTAL_UTTERANCES


def test_preprocessing_example_export_contains_generated_values(tmp_path: Path) -> None:
    output = tmp_path / "preprocessing-examples.csv"

    count = write_preprocessing_examples(output)

    with output.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert count == 5
    assert rows[0] == {
        "example_id": "example-01",
        "original_text": "Halo Kak!! Ada jasa tukang listrik?",
        "cleaned_text": "halo kak ada jasa tukang listrik",
        "tokens": '["halo","kak","ada","jasa","tukang","listrik"]',
    }
    assert rows[3]["cleaned_text"] == "hubungi phonetoken atau emailtoken"


def test_preprocessing_examples_can_be_built_from_custom_input() -> None:
    rows = build_preprocessing_examples(["HARGA rumah?"])

    assert len(rows) == 1
    assert rows[0].cleaned_text == "harga rumah"

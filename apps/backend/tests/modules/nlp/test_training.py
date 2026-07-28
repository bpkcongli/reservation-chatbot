import csv
import json
from collections import Counter
from pathlib import Path

from app.modules.nlp.evaluation import write_evaluation_artifacts
from app.modules.nlp.preprocessing import clean_text, tokenize_cleaned_text
from app.modules.nlp.taxonomy import EXPECTED_DISTRIBUTION
from app.modules.nlp.training import (
    METADATA_FILENAME,
    MODEL_FILENAME,
    MODEL_VERSION,
    RANDOM_STATE,
    TrainingRun,
    save_model_artifact,
    select_fallback_threshold,
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


def test_training_uses_reproducible_stratified_split_and_canonical_pipeline(
    trained_intent_run: TrainingRun,
) -> None:
    run = trained_intent_run

    assert len(run.train_records) == 192
    assert len(run.test_records) == 48
    assert set(record.id for record in run.train_records).isdisjoint(
        record.id for record in run.test_records
    )
    assert Counter(record.intent for record in run.train_records) == {
        label: expected - Counter(record.intent for record in run.test_records)[label]
        for label, expected in EXPECTED_DISTRIBUTION.items()
    }

    vectorizer = run.pipeline.named_steps["tfidf"]
    classifier = run.pipeline.named_steps["classifier"]
    assert isinstance(vectorizer, TfidfVectorizer)
    assert vectorizer.preprocessor is clean_text
    assert vectorizer.tokenizer is tokenize_cleaned_text
    assert vectorizer.sublinear_tf is True
    assert isinstance(classifier, LogisticRegression)
    assert classifier.random_state == RANDOM_STATE
    assert classifier.class_weight == "balanced"
    assert classifier.max_iter == 1000
    assert run.best_parameters["tfidf__ngram_range"] in ((1, 1), (1, 2))


def test_threshold_policy_uses_accuracy_and_coverage() -> None:
    selection = select_fallback_threshold(
        ["a", "a", "b", "b"],
        ["a", "b", "b", "a"],
        [0.91, 0.31, 0.89, 0.32],
        minimum_coverage=0.5,
    )

    assert selection.threshold == 0.33
    assert selection.accepted_accuracy == 1.0
    assert selection.coverage == 0.5


def test_model_artifact_contains_dataset_checksum_and_version_metadata(
    trained_intent_run: TrainingRun,
    tmp_path: Path,
) -> None:
    artifact_path, metadata_path = save_model_artifact(trained_intent_run, tmp_path)

    assert artifact_path.name == MODEL_FILENAME
    assert metadata_path.name == METADATA_FILENAME
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["model_version"] == MODEL_VERSION
    assert metadata["dataset"]["sha256"] == trained_intent_run.dataset_sha256
    assert metadata["artifact"]["sha256"]
    assert metadata["training"]["train_samples"] == 192
    assert metadata["training"]["test_samples"] == 48
    assert metadata["inference"]["labels"] == list(trained_intent_run.labels)
    assert metadata["runtime"]["libraries"]["scikit-learn"]


def test_evaluation_writes_complete_metric_evidence(
    trained_intent_run: TrainingRun,
    tmp_path: Path,
) -> None:
    write_evaluation_artifacts(trained_intent_run, tmp_path)

    expected_files = {
        "classification-report.csv",
        "confusion-matrix.csv",
        "confusion-matrix.png",
        "metrics.json",
        "misclassified.csv",
        "split-distribution.csv",
    }
    assert {path.name for path in tmp_path.iterdir()} == expected_files

    metrics = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert metrics["test_samples"] == 48
    assert set(metrics) >= {"accuracy", "macro_average", "weighted_average", "fallback"}

    with (tmp_path / "classification-report.csv").open(encoding="utf-8", newline="") as csv_file:
        report_rows = list(csv.DictReader(csv_file))
    assert {row["scope"] for row in report_rows} == {
        *trained_intent_run.labels,
        "macro_average",
        "weighted_average",
        "accuracy",
    }

    with (tmp_path / "confusion-matrix.csv").open(encoding="utf-8", newline="") as csv_file:
        confusion_rows = list(csv.DictReader(csv_file))
    assert [row["actual_intent"] for row in confusion_rows] == list(trained_intent_run.labels)
    assert (
        sum(
            int(row[predicted_label])
            for row in confusion_rows
            for predicted_label in trained_intent_run.labels
        )
        == 48
    )
    assert (tmp_path / "confusion-matrix.png").stat().st_size > 0

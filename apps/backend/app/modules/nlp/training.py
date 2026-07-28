"""Reproducible TF-IDF and Logistic Regression intent-model training."""

import hashlib
import json
import platform
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (
    GridSearchCV,
    StratifiedKFold,
    cross_val_predict,
    train_test_split,
)
from sklearn.pipeline import Pipeline

from app.modules.nlp.dataset import UtteranceRecord
from app.modules.nlp.preprocessing import clean_text, tokenize_cleaned_text
from app.modules.nlp.review import load_records, validate_records

RANDOM_STATE = 42
TEST_SIZE = 0.20
CV_FOLDS = 5
MODEL_VERSION = "tfidf-logreg-v1"
ARTIFACT_SCHEMA_VERSION = 1
MODEL_FILENAME = "intent-classifier.joblib"
METADATA_FILENAME = "intent-classifier.metadata.json"
MINIMUM_COVERAGE = 0.50
REPOSITORY_ROOT = Path(__file__).resolve().parents[5]

PARAMETER_GRID: dict[str, list[object]] = {
    "tfidf__ngram_range": [(1, 1), (1, 2)],
    "tfidf__min_df": [1, 2],
    "classifier__C": [0.5, 1.0, 2.0],
}


@dataclass(frozen=True, slots=True)
class ThresholdSelection:
    """Validation-only evidence used to choose the runtime fallback threshold."""

    threshold: float
    accepted_accuracy: float
    coverage: float
    accepted_count: int
    validation_count: int
    minimum_coverage: float


@dataclass(frozen=True, slots=True)
class TrainingRun:
    """Trained model plus the untouched test split and reproducibility metadata."""

    pipeline: Pipeline
    labels: tuple[str, ...]
    train_records: tuple[UtteranceRecord, ...]
    test_records: tuple[UtteranceRecord, ...]
    test_predictions: tuple[str, ...]
    test_confidences: tuple[float, ...]
    dataset_sha256: str
    dataset_path: str
    best_parameters: dict[str, object]
    best_cv_macro_f1: float
    threshold_selection: ThresholdSelection
    trained_at_utc: str

    @property
    def confidence_threshold(self) -> float:
        """Runtime threshold selected exclusively from out-of-fold train predictions."""

        return self.threshold_selection.threshold


def build_pipeline() -> Pipeline:
    """Build the canonical baseline without fitting it."""

    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    preprocessor=clean_text,
                    tokenizer=tokenize_cleaned_text,
                    token_pattern=None,
                    lowercase=False,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def _threshold_candidates() -> tuple[float, ...]:
    return tuple(round(float(value), 2) for value in np.arange(0.10, 0.91, 0.01))


def select_fallback_threshold(
    actual_labels: Sequence[str],
    predicted_labels: Sequence[str],
    confidences: Sequence[float],
    *,
    minimum_coverage: float = MINIMUM_COVERAGE,
) -> ThresholdSelection:
    """Maximize accepted accuracy while retaining minimum validation coverage.

    Inputs must come from validation or out-of-fold training predictions. The
    held-out test set must never be used by this function.
    """

    if not actual_labels or not (len(actual_labels) == len(predicted_labels) == len(confidences)):
        raise ValueError("Threshold selection inputs must be non-empty and equally sized.")

    observations: list[ThresholdSelection] = []
    total = len(actual_labels)
    for threshold in _threshold_candidates():
        accepted_indices = [
            index for index, confidence in enumerate(confidences) if confidence >= threshold
        ]
        accepted_count = len(accepted_indices)
        coverage = accepted_count / total
        correct = sum(predicted_labels[index] == actual_labels[index] for index in accepted_indices)
        accepted_accuracy = correct / accepted_count if accepted_count else 0.0
        observations.append(
            ThresholdSelection(
                threshold=threshold,
                accepted_accuracy=round(accepted_accuracy, 6),
                coverage=round(coverage, 6),
                accepted_count=accepted_count,
                validation_count=total,
                minimum_coverage=minimum_coverage,
            )
        )

    covered = [
        observation for observation in observations if observation.coverage >= minimum_coverage
    ]
    if not covered:
        covered = observations
    return max(
        covered,
        key=lambda observation: (
            observation.accepted_accuracy,
            observation.coverage,
            -observation.threshold,
        ),
    )


def _validated_records(source: Path) -> list[UtteranceRecord]:
    records, load_issues = load_records(source)
    issues = [*load_issues, *validate_records(records)]
    if issues:
        issue_codes = ", ".join(dict.fromkeys(issue.code for issue in issues))
        raise ValueError(f"Dataset validation failed: {issue_codes}")
    return records


def _portable_dataset_path(source: Path) -> str:
    resolved_source = source.resolve()
    try:
        return resolved_source.relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError:
        return str(resolved_source)


def _class_labels(pipeline: Pipeline) -> tuple[str, ...]:
    classifier = pipeline.named_steps["classifier"]
    classes = getattr(classifier, "classes_", None)
    if classes is None:
        raise RuntimeError("Fitted classifier does not expose classes_.")
    return tuple(str(label) for label in classes)


def train_intent_model(
    source: Path,
    *,
    trained_at_utc: str | None = None,
) -> TrainingRun:
    """Train and evaluate the main baseline with one deterministic data split."""

    records = _validated_records(source)
    labels = [record.intent for record in records]
    train_records, test_records = train_test_split(
        records,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=labels,
    )
    train_texts = [record.text for record in train_records]
    train_labels = [record.intent for record in train_records]

    cross_validation = StratifiedKFold(
        n_splits=CV_FOLDS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )
    search = GridSearchCV(
        estimator=build_pipeline(),
        param_grid=PARAMETER_GRID,
        scoring="f1_macro",
        cv=cross_validation,
        n_jobs=1,
        refit=True,
        return_train_score=False,
    )
    search.fit(train_texts, train_labels)
    pipeline = search.best_estimator_
    if not isinstance(pipeline, Pipeline):
        raise RuntimeError("Grid search did not return an sklearn Pipeline.")

    validation_probabilities = cross_val_predict(
        pipeline,
        train_texts,
        train_labels,
        cv=cross_validation,
        method="predict_proba",
        n_jobs=1,
    )
    validation_array = np.asarray(validation_probabilities, dtype=np.float64)
    class_labels = _class_labels(pipeline)
    validation_indices = validation_array.argmax(axis=1)
    validation_predictions = [class_labels[index] for index in validation_indices]
    validation_confidences = validation_array.max(axis=1).tolist()
    threshold_selection = select_fallback_threshold(
        train_labels,
        validation_predictions,
        validation_confidences,
    )

    test_probabilities = np.asarray(
        pipeline.predict_proba([record.text for record in test_records]),
        dtype=np.float64,
    )
    test_indices = test_probabilities.argmax(axis=1)
    test_predictions = tuple(class_labels[index] for index in test_indices)
    test_confidences = tuple(float(value) for value in test_probabilities.max(axis=1))

    timestamp = trained_at_utc or datetime.now(UTC).isoformat(timespec="seconds")
    return TrainingRun(
        pipeline=pipeline,
        labels=class_labels,
        train_records=tuple(train_records),
        test_records=tuple(test_records),
        test_predictions=test_predictions,
        test_confidences=test_confidences,
        dataset_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        dataset_path=_portable_dataset_path(source),
        best_parameters=dict(search.best_params_),
        best_cv_macro_f1=round(float(search.best_score_), 6),
        threshold_selection=threshold_selection,
        trained_at_utc=timestamp,
    )


def _json_parameter(value: object) -> object:
    if isinstance(value, tuple):
        return list(value)
    return value


def _dependency_versions() -> dict[str, str]:
    return {
        package: version(package)
        for package in ("joblib", "matplotlib", "numpy", "scikit-learn", "scipy")
    }


def build_model_metadata(
    run: TrainingRun,
    *,
    artifact_filename: str,
    artifact_sha256: str,
) -> dict[str, Any]:
    """Build the versioned sidecar consumed by the model loader."""

    train_distribution = Counter(record.intent for record in run.train_records)
    test_distribution = Counter(record.intent for record in run.test_records)
    return {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "model_version": MODEL_VERSION,
        "artifact": {
            "filename": artifact_filename,
            "sha256": artifact_sha256,
            "format": "joblib",
        },
        "dataset": {
            "path": run.dataset_path,
            "sha256": run.dataset_sha256,
            "total_samples": len(run.train_records) + len(run.test_records),
        },
        "training": {
            "trained_at_utc": run.trained_at_utc,
            "random_state": RANDOM_STATE,
            "test_size": TEST_SIZE,
            "cv_folds": CV_FOLDS,
            "train_samples": len(run.train_records),
            "test_samples": len(run.test_records),
            "train_distribution": dict(sorted(train_distribution.items())),
            "test_distribution": dict(sorted(test_distribution.items())),
            "best_cv_macro_f1": run.best_cv_macro_f1,
            "best_parameters": {
                key: _json_parameter(value) for key, value in sorted(run.best_parameters.items())
            },
        },
        "inference": {
            "labels": list(run.labels),
            "confidence_threshold": run.confidence_threshold,
            "threshold_selection": {
                "source": "5-fold out-of-fold predictions on training split",
                "policy": "maximize accepted accuracy with minimum validation coverage",
                "accepted_accuracy": run.threshold_selection.accepted_accuracy,
                "coverage": run.threshold_selection.coverage,
                "accepted_count": run.threshold_selection.accepted_count,
                "validation_count": run.threshold_selection.validation_count,
                "minimum_coverage": run.threshold_selection.minimum_coverage,
            },
            "preprocessor": "app.modules.nlp.preprocessing.clean_text",
            "tokenizer": "app.modules.nlp.preprocessing.tokenize_cleaned_text",
        },
        "runtime": {
            "python": platform.python_version(),
            "libraries": _dependency_versions(),
        },
    }


def sha256_file(path: Path) -> str:
    """Return a lowercase SHA-256 digest for an artifact."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_model_artifact(
    run: TrainingRun,
    destination: Path,
) -> tuple[Path, Path]:
    """Persist the fitted pipeline and an integrity-verifiable metadata sidecar."""

    destination.mkdir(parents=True, exist_ok=True)
    artifact_path = destination / MODEL_FILENAME
    metadata_path = destination / METADATA_FILENAME
    joblib.dump(run.pipeline, artifact_path, compress=3)
    artifact_sha256 = sha256_file(artifact_path)
    metadata = build_model_metadata(
        run,
        artifact_filename=artifact_path.name,
        artifact_sha256=artifact_sha256,
    )

    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return artifact_path, metadata_path

"""Evaluation artifact generation for the held-out intent test split."""

import csv
import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

import matplotlib
import numpy as np
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)

from app.modules.nlp.training import MODEL_VERSION, RANDOM_STATE, TrainingRun

matplotlib.use("Agg")
from matplotlib import pyplot as plt


def _write_csv(
    destination: Path,
    fieldnames: Sequence[str],
    rows: Iterable[Mapping[str, object]],
) -> None:
    with destination.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _score_row(
    scope: str,
    precision: float,
    recall: float,
    f1_score: float,
    support: int,
) -> dict[str, object]:
    return {
        "scope": scope,
        "precision": round(float(precision), 6),
        "recall": round(float(recall), 6),
        "f1_score": round(float(f1_score), 6),
        "support": support,
    }


def _classification_rows(run: TrainingRun) -> list[dict[str, object]]:
    actual = [record.intent for record in run.test_records]
    predicted = list(run.test_predictions)
    precision, recall, f1_score, support = precision_recall_fscore_support(
        actual,
        predicted,
        labels=list(run.labels),
        zero_division=0,
    )
    rows = [
        _score_row(
            label,
            float(precision[index]),
            float(recall[index]),
            float(f1_score[index]),
            int(support[index]),
        )
        for index, label in enumerate(run.labels)
    ]
    for average in ("macro", "weighted"):
        avg_precision, avg_recall, avg_f1, _ = precision_recall_fscore_support(
            actual,
            predicted,
            average=average,
            zero_division=0,
        )
        rows.append(
            _score_row(
                f"{average}_average",
                float(avg_precision),
                float(avg_recall),
                float(avg_f1),
                len(actual),
            )
        )
    accuracy = float(accuracy_score(actual, predicted))
    rows.append(_score_row("accuracy", accuracy, accuracy, accuracy, len(actual)))
    return rows


def _write_confusion_matrix_png(matrix: np.ndarray, labels: Sequence[str], path: Path) -> None:
    figure, axis = plt.subplots(figsize=(12, 10))
    display = ConfusionMatrixDisplay(confusion_matrix=matrix, display_labels=labels)
    display.plot(ax=axis, cmap="Blues", colorbar=False, values_format="d")
    axis.set_title("Intent Classification Confusion Matrix")
    axis.tick_params(axis="x", rotation=45)
    figure.tight_layout()
    figure.savefig(path, dpi=160, metadata={"Software": "reservation-chatbot"})
    plt.close(figure)


def write_evaluation_artifacts(run: TrainingRun, destination: Path) -> None:
    """Write all NLP-09 evidence from the single held-out test evaluation."""

    destination.mkdir(parents=True, exist_ok=True)
    actual = [record.intent for record in run.test_records]
    predicted = list(run.test_predictions)
    classification_rows = _classification_rows(run)
    accuracy = float(accuracy_score(actual, predicted))
    macro_row = next(row for row in classification_rows if row["scope"] == "macro_average")
    weighted_row = next(row for row in classification_rows if row["scope"] == "weighted_average")
    fallback_count = sum(
        confidence < run.confidence_threshold for confidence in run.test_confidences
    )
    metrics = {
        "model_version": MODEL_VERSION,
        "dataset_sha256": run.dataset_sha256,
        "random_state": RANDOM_STATE,
        "train_samples": len(run.train_records),
        "test_samples": len(run.test_records),
        "best_cv_macro_f1": run.best_cv_macro_f1,
        "accuracy": round(accuracy, 6),
        "macro_average": {
            key: macro_row[key] for key in ("precision", "recall", "f1_score", "support")
        },
        "weighted_average": {
            key: weighted_row[key] for key in ("precision", "recall", "f1_score", "support")
        },
        "fallback": {
            "confidence_threshold": run.confidence_threshold,
            "count": fallback_count,
            "rate": round(fallback_count / len(actual), 6),
            "threshold_source": "5-fold out-of-fold predictions on training split",
            "validation_accepted_accuracy": run.threshold_selection.accepted_accuracy,
            "validation_coverage": run.threshold_selection.coverage,
            "minimum_validation_coverage": run.threshold_selection.minimum_coverage,
        },
    }
    (destination / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    _write_csv(
        destination / "classification-report.csv",
        ("scope", "precision", "recall", "f1_score", "support"),
        classification_rows,
    )

    matrix = confusion_matrix(actual, predicted, labels=list(run.labels))
    confusion_rows = [
        {
            "actual_intent": actual_label,
            **{
                predicted_label: int(matrix[row_index, column_index])
                for column_index, predicted_label in enumerate(run.labels)
            },
        }
        for row_index, actual_label in enumerate(run.labels)
    ]
    _write_csv(
        destination / "confusion-matrix.csv",
        ("actual_intent", *run.labels),
        confusion_rows,
    )
    _write_confusion_matrix_png(matrix, run.labels, destination / "confusion-matrix.png")

    misclassified_rows = [
        {
            "id": record.id,
            "text": record.text,
            "actual": record.intent,
            "predicted": prediction,
            "confidence": round(confidence, 6),
        }
        for record, prediction, confidence in zip(
            run.test_records,
            run.test_predictions,
            run.test_confidences,
            strict=True,
        )
        if record.intent != prediction
    ]
    _write_csv(
        destination / "misclassified.csv",
        ("id", "text", "actual", "predicted", "confidence"),
        misclassified_rows,
    )

    split_rows: list[dict[str, object]] = []
    for split, records in (("train", run.train_records), ("test", run.test_records)):
        counts = Counter(record.intent for record in records)
        for label in run.labels:
            split_rows.append(
                {
                    "split": split,
                    "intent": label,
                    "count": counts[label],
                    "percentage": round((counts[label] / len(records)) * 100, 2),
                }
            )
    _write_csv(
        destination / "split-distribution.csv",
        ("split", "intent", "count", "percentage"),
        split_rows,
    )

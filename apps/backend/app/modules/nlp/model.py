"""Integrity-checked intent-model loading and confidence fallback inference."""

import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.pipeline import Pipeline

from app.modules.nlp.taxonomy import INTENT_BY_LABEL, Intent
from app.modules.nlp.training import (
    ARTIFACT_SCHEMA_VERSION,
    METADATA_FILENAME,
    MODEL_VERSION,
    sha256_file,
)


class ModelArtifactError(RuntimeError):
    """Raised when a model or its sidecar metadata is missing or inconsistent."""


@dataclass(frozen=True, slots=True)
class IntentPrediction:
    """Top classifier result plus the threshold routing decision."""

    intent: Intent | None
    top_intent: Intent
    confidence: float
    is_fallback: bool


class IntentModel:
    """Loaded sklearn pipeline with a stable inference contract."""

    def __init__(
        self,
        pipeline: Pipeline,
        *,
        labels: tuple[str, ...],
        confidence_threshold: float,
        model_version: str,
    ) -> None:
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ModelArtifactError("Confidence threshold must be between 0 and 1.")
        unknown_labels = sorted(set(labels) - INTENT_BY_LABEL.keys())
        if unknown_labels:
            raise ModelArtifactError(f"Model metadata contains unknown labels: {unknown_labels}.")

        classifier = pipeline.named_steps.get("classifier")
        pipeline_classes = getattr(classifier, "classes_", None)
        if pipeline_classes is None:
            raise ModelArtifactError("Model pipeline has no fitted classifier classes.")
        if tuple(str(value) for value in pipeline_classes) != labels:
            raise ModelArtifactError("Pipeline classes do not match metadata labels.")

        self._pipeline = pipeline
        self.labels = labels
        self.confidence_threshold = confidence_threshold
        self.model_version = model_version

    def predict(self, text: str, *, threshold: float | None = None) -> IntentPrediction:
        """Classify one utterance and route low confidence to fallback."""

        selected_threshold = self.confidence_threshold if threshold is None else threshold
        if not 0.0 <= selected_threshold <= 1.0:
            raise ValueError("Inference threshold must be between 0 and 1.")
        probabilities = np.asarray(self._pipeline.predict_proba([text]), dtype=np.float64)
        if probabilities.shape != (1, len(self.labels)):
            raise ModelArtifactError("Classifier returned an unexpected probability shape.")
        top_index = int(probabilities[0].argmax())
        confidence = float(probabilities[0, top_index])
        top_intent = Intent(self.labels[top_index])
        is_fallback = confidence < selected_threshold
        return IntentPrediction(
            intent=None if is_fallback else top_intent,
            top_intent=top_intent,
            confidence=confidence,
            is_fallback=is_fallback,
        )


def _metadata_object(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ModelArtifactError(f"Model metadata field {field!r} must be an object.")
    return value


def _metadata_labels(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(label, str) for label in value):
        raise ModelArtifactError("Model metadata labels must be a list of strings.")
    return tuple(value)


def load_intent_model(
    artifact_path: Path,
    *,
    metadata_path: Path | None = None,
    verify_checksum: bool = True,
) -> IntentModel:
    """Load a trusted local artifact after validating its versioned sidecar."""

    sidecar_path = metadata_path or artifact_path.with_name(METADATA_FILENAME)
    try:
        raw_metadata: object = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ModelArtifactError(f"Could not read model metadata: {sidecar_path}.") from error
    metadata = _metadata_object(raw_metadata, "root")
    if metadata.get("artifact_schema_version") != ARTIFACT_SCHEMA_VERSION:
        raise ModelArtifactError("Unsupported model artifact schema version.")
    if metadata.get("model_version") != MODEL_VERSION:
        raise ModelArtifactError("Unsupported intent model version.")

    artifact = _metadata_object(metadata.get("artifact"), "artifact")
    expected_filename = artifact.get("filename")
    expected_sha256 = artifact.get("sha256")
    if expected_filename != artifact_path.name:
        raise ModelArtifactError("Artifact filename does not match its metadata.")
    if verify_checksum:
        try:
            checksum_matches = (
                isinstance(expected_sha256, str) and sha256_file(artifact_path) == expected_sha256
            )
        except OSError as error:
            raise ModelArtifactError(f"Could not read model artifact: {artifact_path}.") from error
        if not checksum_matches:
            raise ModelArtifactError("Model artifact checksum verification failed.")

    inference = _metadata_object(metadata.get("inference"), "inference")
    labels = _metadata_labels(inference.get("labels"))
    threshold = inference.get("confidence_threshold")
    model_version = metadata.get("model_version")
    if not isinstance(threshold, (float, int)) or isinstance(threshold, bool):
        raise ModelArtifactError("Model confidence threshold is invalid.")
    if not isinstance(model_version, str):
        raise ModelArtifactError("Model version is invalid.")

    try:
        loaded: object = joblib.load(artifact_path)
    except (EOFError, OSError, ValueError, pickle.UnpicklingError) as error:
        raise ModelArtifactError(f"Could not load model artifact: {artifact_path}.") from error
    if not isinstance(loaded, Pipeline):
        raise ModelArtifactError("Model artifact must contain an sklearn Pipeline.")
    return IntentModel(
        loaded,
        labels=labels,
        confidence_threshold=float(threshold),
        model_version=model_version,
    )

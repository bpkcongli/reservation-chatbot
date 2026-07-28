from pathlib import Path

import pytest
from app.modules.nlp.model import ModelArtifactError, load_intent_model
from app.modules.nlp.taxonomy import Intent
from app.modules.nlp.training import TrainingRun, save_model_artifact


@pytest.fixture()
def saved_model(trained_intent_run: TrainingRun, tmp_path: Path) -> Path:
    artifact_path, _ = save_model_artifact(trained_intent_run, tmp_path)
    return artifact_path


def test_loader_runs_single_text_inference(saved_model: Path) -> None:
    model = load_intent_model(saved_model)

    prediction = model.predict("Halo")

    assert prediction.top_intent is Intent.GREETING
    assert prediction.intent is Intent.GREETING
    assert 0.0 <= prediction.confidence <= 1.0
    assert prediction.is_fallback is False


def test_inference_returns_fallback_below_threshold(saved_model: Path) -> None:
    model = load_intent_model(saved_model)

    prediction = model.predict("kalimat yang benar benar di luar domain")

    assert prediction.intent is None
    assert prediction.is_fallback is True
    assert prediction.confidence < model.confidence_threshold
    assert prediction.top_intent in Intent


def test_loader_rejects_artifact_with_wrong_checksum(saved_model: Path) -> None:
    with saved_model.open("ab") as model_file:
        model_file.write(b"tampered")

    with pytest.raises(ModelArtifactError, match="checksum"):
        load_intent_model(saved_model)

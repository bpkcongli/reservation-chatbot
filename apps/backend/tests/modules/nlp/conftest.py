from pathlib import Path

import pytest
from app.modules.nlp.training import TrainingRun, train_intent_model

REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
DATASET_PATH = REPOSITORY_ROOT / "data" / "raw" / "intents.csv"


@pytest.fixture(scope="session")
def trained_intent_run() -> TrainingRun:
    return train_intent_model(
        DATASET_PATH,
        trained_at_utc="2026-07-29T00:00:00+00:00",
    )

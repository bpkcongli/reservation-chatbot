"""Train the intent classifier and write model plus evaluation artifacts."""

import argparse
from pathlib import Path

from app.modules.nlp.evaluation import write_evaluation_artifacts
from app.modules.nlp.training import save_model_artifact, train_intent_model

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = REPOSITORY_ROOT / "data" / "raw" / "intents.csv"
DEFAULT_MODEL_OUTPUT = REPOSITORY_ROOT / "artifacts" / "models"
DEFAULT_EVALUATION_OUTPUT = REPOSITORY_ROOT / "artifacts" / "evaluation"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--model-output", type=Path, default=DEFAULT_MODEL_OUTPUT)
    parser.add_argument(
        "--evaluation-output",
        type=Path,
        default=DEFAULT_EVALUATION_OUTPUT,
    )
    args = parser.parse_args()

    run = train_intent_model(args.input)
    artifact_path, metadata_path = save_model_artifact(run, args.model_output)
    write_evaluation_artifacts(run, args.evaluation_output)
    print(
        f"Trained {artifact_path.name} on {len(run.train_records)} samples; "
        f"test accuracy artifacts written to {args.evaluation_output}."
    )
    print(
        f"Best CV macro F1={run.best_cv_macro_f1:.4f}; "
        f"fallback threshold={run.confidence_threshold:.2f}; "
        f"metadata={metadata_path}."
    )


if __name__ == "__main__":
    main()

"""Analyze intent distribution and text lengths in the raw dataset."""

import argparse
from pathlib import Path

from app.modules.nlp.analysis import analyze_dataset, write_analysis_artifacts

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = REPOSITORY_ROOT / "data" / "raw" / "intents.csv"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "artifacts" / "evaluation"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    analysis = analyze_dataset(args.input)
    write_analysis_artifacts(analysis, args.output)
    print(
        f"Analyzed {analysis.total} utterances across "
        f"{len(analysis.distribution)} intents; artifacts written to {args.output}."
    )


if __name__ == "__main__":
    main()

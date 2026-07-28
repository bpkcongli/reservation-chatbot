"""Export reproducible before/after preprocessing examples."""

import argparse
from pathlib import Path

from app.modules.nlp.preprocessing_examples import write_preprocessing_examples

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = REPOSITORY_ROOT / "artifacts" / "evaluation" / "preprocessing-examples.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    example_count = write_preprocessing_examples(args.output)
    print(f"Wrote {example_count} preprocessing examples to {args.output}.")


if __name__ == "__main__":
    main()

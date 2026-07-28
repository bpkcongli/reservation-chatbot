"""Generate data/raw/intents.csv from the canonical utterance source."""

import argparse
from pathlib import Path

from app.modules.nlp.dataset import write_dataset

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = REPOSITORY_ROOT / "data" / "raw" / "intents.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    row_count = write_dataset(args.output)
    print(f"Wrote {row_count} utterances to {args.output}")


if __name__ == "__main__":
    main()

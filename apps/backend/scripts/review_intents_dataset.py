"""Audit the raw intent dataset and write reproducible review artifacts."""

import argparse
from pathlib import Path

from app.modules.nlp.review import review_dataset, write_review_artifacts

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = REPOSITORY_ROOT / "data" / "raw" / "intents.csv"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "data" / "reviews"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    review = review_dataset(args.input)
    write_review_artifacts(review, args.output)
    print(
        f"Reviewed {review.row_count} utterances: "
        f"{len(review.issues)} issue(s), "
        f"{len(review.near_duplicates)} near-duplicate candidate(s)."
    )
    if review.issues:
        for issue in review.issues:
            print(f"- {issue.code}: {issue.message}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

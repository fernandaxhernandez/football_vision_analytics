# scripts/run_pipeline.py

import argparse
from match_analysis.pipeline import run_pipeline  # [file:46]


def main():
    parser = argparse.ArgumentParser(
        description="Run team assignment and ball possession pipeline."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to JSON file with detection/tracking records.",
    )
    parser.add_argument(
        "--output",
        default="outputs/tracks_annotated.json",
        help="Where to save the annotated JSON output.",
    )
    args = parser.parse_args()

    run_pipeline(args.input, args.output)


if __name__ == "__main__":
    main()

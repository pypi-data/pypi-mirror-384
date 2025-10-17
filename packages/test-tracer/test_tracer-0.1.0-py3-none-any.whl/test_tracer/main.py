"""Entry point for test-tracer command line interface."""

import argparse
from pathlib import Path

from test_tracer.trace_requirements import trace_requirements


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-r",
        "--requirements",
        required=True,
        type=Path,
        help="Project requirements file path",
    )
    parser.add_argument(
        "-td", "--test-directory",
        type=Path,
        help="Test directory path"
    )
    parser.add_argument("--bi-directional", help="Add bi-directional mapping page.")
    parser.add_argument(
        "-o",
        "--output-excel",
        default="test_trace_matrix.xlsx",
    )
    parser.add_argument(
        "-s", "--soup",
        help="Run tests to track SOUP component usage (Warning: Can be slow!)",
        default=None
    )

    return parser.parse_args()


def main() -> None:
    args = cli()

    trace_requirements(
        args.requirements,
        args.test_directory,
        args.output_excel,
        args.bi_directional,
        args.soup
    )


if __name__ == "__main__":
    main()

"""CLI tool for concatenating files with skeleton extraction."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loppers.concatenator import concatenate_files


def main() -> None:
    """CLI entry point for concatenating files with skeleton extraction.

    Processes files and directories, extracting code skeletons.
    """
    parser = argparse.ArgumentParser(
        description="Concatenate files with skeleton extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  loppers file1.py file2.js              # Multiple files
  loppers src/                           # Directory (non-recursive)
  loppers -r src/                        # Recursively process directory
  loppers -r src/ tests/                 # Multiple directories
  loppers -o skeletons.txt -r .          # All supported files from current dir
  loppers -v *.py                        # Verbose output
  loppers -o combined.txt -r src/        # Recursive with output file
        """,
    )

    parser.add_argument(
        "files",
        nargs="+",
        help="Files and/or directories to process",
    )

    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively traverse directories for supported files",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Output file (default: stdout)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print verbose output to stderr",
    )

    parser.add_argument(
        "--no-extract",
        action="store_true",
        help="Include original files without skeleton extraction",
    )

    args = parser.parse_args()

    # Concatenate files
    result = concatenate_files(
        args.files,
        recursive=args.recursive,
        verbose=args.verbose,
        extract_skeletons=not args.no_extract,
    )

    # Output result
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        if args.verbose:
            print(f"✓ Written to {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()

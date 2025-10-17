"""CLI tool for concatenating files with skeleton extraction."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loppers.loppers import extract
from loppers.mapping import get_language


def concatenate_files(
    file_paths: list[str | Path],
    verbose: bool = False,
) -> str:
    """Concatenate files with skeleton extraction and file headers.

    Attempts to extract skeleton from each file using its language.
    If extraction fails, includes the original file content.
    Files are separated with headers indicating their names.

    Args:
        file_paths: List of file paths to concatenate
        verbose: Print debug information to stderr

    Returns:
        Concatenated content with file headers and skeletons
    """
    results: list[str] = []

    for file_path in file_paths:
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            if verbose:
                print(f"Warning: File not found: {path}", file=sys.stderr)
            continue

        # Read file content
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, IOError) as e:
            if verbose:
                print(f"Warning: Could not read {path}: {e}", file=sys.stderr)
            continue

        # Create header
        header = f"--- {path}\n"

        # Attempt skeleton extraction
        language = get_language(str(path.suffix))

        if language:
            try:
                skeleton = extract(content, language)
                body = skeleton
                if verbose:
                    print(f"✓ Extracted skeleton from {path.name}", file=sys.stderr)
            except Exception as e:
                if verbose:
                    print(
                        f"⚠ Could not extract skeleton from {path.name}: {e}",
                        file=sys.stderr,
                    )
                body = content
        else:
            if verbose:
                print(f"⚠ Unknown language for {path.name}, keeping as-is", file=sys.stderr)
            body = content

        results.append(header + body + "\n")

    return "\n".join(results).rstrip()


def main() -> None:
    """CLI entry point for concatenating files.

    Usage:
        loppers file1.py file2.js file3.java
        loppers --output combined.txt *.py
        loppers --verbose *.py
    """
    parser = argparse.ArgumentParser(
        description="Concatenate files with skeleton extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  loppers file1.py file2.js
  loppers -o skeletons.txt *.py
  loppers -v *.java
  loppers -o combined.py src/**/*.py
        """,
    )

    parser.add_argument(
        "files",
        nargs="+",
        help="Files to concatenate",
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

    args = parser.parse_args()

    # Concatenate files
    result = concatenate_files(args.files, verbose=args.verbose)

    # Output result
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        if args.verbose:
            print(f"✓ Written to {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()

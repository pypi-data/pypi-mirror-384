"""File concatenation with automatic skeleton extraction and binary detection."""

from __future__ import annotations

import sys
from pathlib import Path

from binaryornot.check import is_binary

from loppers.loppers import extract
from loppers.mapping import get_language


def is_binary_file(file_path: Path) -> bool:
    """Detect if a file is binary.

    Uses the binaryornot library which employs multiple detection methods:
    - Known binary file extensions
    - Null byte detection
    - UTF-8 decoding validation

    Args:
        file_path: Path to the file to check

    Returns:
        True if file appears to be binary, False if text-based
    """
    try:
        return is_binary(str(file_path))
    except (IOError, OSError):
        # If we can't read the file, assume it's binary
        return True


def collect_files(
    paths: list[str | Path],
    recursive: bool = False,
    verbose: bool = False,
    include_all_text_files: bool = True,
) -> list[Path]:
    """Collect files from paths, expanding directories if requested.

    Automatically skips binary files and optionally filters by supported
    programming languages. Returns files in sorted order.

    Args:
        paths: List of file paths or directory paths
        recursive: If True, recursively traverse directories
        verbose: Print debug information to stderr
        include_all_text_files: If True, include all text files. If False,
            only include files with recognized programming language extensions.

    Returns:
        Sorted list of file paths to process
    """
    collected: set[Path] = set()

    for path_item in paths:
        path = Path(path_item)

        if path.is_file():
            if not is_binary_file(path):
                collected.add(path)
        elif path.is_dir():
            if recursive:
                # Recursively find all non-binary files
                for file_path in path.rglob("*"):
                    if file_path.is_file() and not is_binary_file(file_path):
                        if include_all_text_files or get_language(str(file_path.suffix)):
                            collected.add(file_path)
            else:
                # Only find files in the directory (non-recursive)
                for file_path in path.iterdir():
                    if file_path.is_file() and not is_binary_file(file_path):
                        if include_all_text_files or get_language(str(file_path.suffix)):
                            collected.add(file_path)
                        elif verbose:
                            print(
                                f"⊘ Skipping unsupported file: {file_path.name}",
                                file=sys.stderr,
                            )
        else:
            if verbose:
                print(f"Warning: Path not found: {path}", file=sys.stderr)

    # Return sorted list for consistent output
    return sorted(collected)


def concatenate_files(
    file_paths: list[str | Path],
    recursive: bool = False,
    verbose: bool = False,
    extract_skeletons: bool = True,
) -> str:
    """Concatenate files with optional skeleton extraction.

    Accepts files and/or directories. Automatically skips binary files.
    Attempts to extract skeleton from supported programming languages.
    Falls back to original content for unsupported file types.

    Files are separated with headers indicating their names.

    Args:
        file_paths: List of file and/or directory paths
        recursive: If True, recursively traverse directories for files
        verbose: Print debug information to stderr
        extract_skeletons: If True, attempt skeleton extraction for supported languages.
            If False, include all files as-is.

    Returns:
        Concatenated content with file headers and optionally extracted skeletons
    """
    # Collect all files to process
    files_to_process = collect_files(
        file_paths,
        recursive=recursive,
        verbose=verbose,
        include_all_text_files=True,
    )

    if not files_to_process:
        if verbose:
            print("Warning: No files to process", file=sys.stderr)
        return ""

    results: list[str] = []

    for file_path in files_to_process:
        path = Path(file_path)

        # Read file content
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, IOError) as e:
            if verbose:
                print(f"Warning: Could not read {path}: {e}", file=sys.stderr)
            continue

        # Create header
        header = f"--- {path}\n"

        body = content

        # Attempt skeleton extraction if enabled
        if extract_skeletons:
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
                    print(
                        f"ℹ No skeleton extraction for {path.name}, including as-is",
                        file=sys.stderr,
                    )

        results.append(header + body + "\n")

    return "\n".join(results).rstrip()

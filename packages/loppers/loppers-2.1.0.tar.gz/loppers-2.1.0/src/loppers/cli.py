"""CLI tool for Loppers: skeleton extraction with multiple commands."""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from loppers import extract_skeleton, find_files, get_skeleton, get_tree
from loppers.extensions import get_language


def get_app_version() -> str:
    """Get the application version."""
    try:
        return version("loppers")
    except PackageNotFoundError:
        return "unknown"


def add_shared_args(parser: argparse.ArgumentParser) -> None:
    """Add shared arguments for directory-based commands."""
    parser.add_argument(
        "root",
        help="Root directory to process",
    )

    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Don't recursively traverse directories",
    )

    parser.add_argument(
        "-I",
        "--ignore-pattern",
        action="append",
        dest="ignore_patterns",
        help="Add custom ignore pattern (gitignore syntax, can be used multiple times)",
    )

    parser.add_argument(
        "--no-default-ignore",
        action="store_true",
        help="Disable built-in ignore patterns",
    )

    parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Don't respect .gitignore file",
    )

    parser.add_argument(
        "--collapse-single-dirs",
        action="store_true",
        help="Collapse directories with single children (e.g., main/java/com/example)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file (default: stdout)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print verbose output to stderr",
    )


def cmd_extract(args: argparse.Namespace) -> None:
    """Extract skeleton from a file or stdin."""
    # Determine input source
    if args.file:
        file_path = Path(args.file)
        if not file_path.is_file():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        try:
            source = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            print(f"Error: Could not read file as text: {e}", file=sys.stderr)
            sys.exit(1)

        # Determine language
        if args.language:
            language = args.language
        else:
            language = get_language(str(file_path.suffix))
            if not language:
                print(
                    f"Error: Could not auto-detect language from {file_path.suffix}",
                    file=sys.stderr,
                )
                sys.exit(1)
    else:
        # Read from stdin
        source = sys.stdin.read()
        if not args.language:
            print("Error: Language required when reading from stdin (use -l/--language)",
                  file=sys.stderr)
            sys.exit(1)
        language = args.language

    # Extract skeleton
    try:
        skeleton = extract_skeleton(source, language)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Output result
    if args.output:
        Path(args.output).write_text(skeleton, encoding="utf-8")
        if args.verbose:
            print(f"✓ Written to {args.output}", file=sys.stderr)
    else:
        print(skeleton)


def cmd_concatenate(args: argparse.Namespace) -> None:
    """Concatenate files with optional skeleton extraction."""
    root_path = Path(args.root)

    # Find files
    try:
        files = find_files(
            root_path,
            recursive=not args.no_recursive,
            ignore_patterns=args.ignore_patterns,
            use_default_ignore=not args.no_default_ignore,
            respect_gitignore=not args.no_gitignore,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not files:
        print("Warning: No files found", file=sys.stderr)
        sys.exit(1)

    # Concatenate files with optional skeleton extraction
    results: list[str] = []
    for relative_file_path in files:
        full_file_path = root_path / relative_file_path
        try:
            is_extracted = False
            if args.no_extract:
                # Include original file
                content = full_file_path.read_text(encoding="utf-8")
            else:
                # Try to extract skeleton, fall back to original for unsupported types
                try:
                    content = get_skeleton(full_file_path, add_header=False)
                    is_extracted = True
                except ValueError as e:
                    # File type not supported for extraction, include as-is
                    if "Unsupported file type" in str(e):
                        content = full_file_path.read_text(encoding="utf-8")
                        is_extracted = False
                    else:
                        raise

            # Add header with relative path
            header = f"--- {relative_file_path}\n"
            results.append(header + content + "\n")

            if args.verbose:
                if args.no_extract:
                    print(f"ℹ Included {relative_file_path}", file=sys.stderr)
                elif is_extracted:
                    print(f"✓ Extracted skeleton from {relative_file_path}", file=sys.stderr)
                else:
                    print(f"ℹ Included {relative_file_path} (unsupported type, no extraction)",
                          file=sys.stderr)
        except Exception as e:
            if args.verbose:
                print(f"⚠ Could not process {relative_file_path}: {e}", file=sys.stderr)
            continue

    result = "\n".join(results).rstrip()

    # Output result
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        if args.verbose:
            print(f"✓ Written to {args.output}", file=sys.stderr)
    else:
        print(result)


def cmd_tree(args: argparse.Namespace) -> None:
    """Show directory tree of discovered files."""
    try:
        tree_output = get_tree(
            args.root,
            recursive=not args.no_recursive,
            ignore_patterns=args.ignore_patterns,
            use_default_ignore=not args.no_default_ignore,
            respect_gitignore=not args.no_gitignore,
            collapse_single_dirs=args.collapse_single_dirs,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not tree_output:
        print("No files found", file=sys.stderr)
        return

    # Output result
    if args.output:
        Path(args.output).write_text(tree_output, encoding="utf-8")
        if args.verbose:
            print(f"✓ Written to {args.output}", file=sys.stderr)
    else:
        print(tree_output)


def cmd_files(args: argparse.Namespace) -> None:
    """List all discovered files."""
    try:
        files = find_files(
            args.root,
            recursive=not args.no_recursive,
            ignore_patterns=args.ignore_patterns,
            use_default_ignore=not args.no_default_ignore,
            respect_gitignore=not args.no_gitignore,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not files:
        print("No files found", file=sys.stderr)
        return

    # Format output (files are already relative to root)
    result = "\n".join(files)

    # Output result
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        if args.verbose:
            print(f"✓ Written to {args.output}", file=sys.stderr)
    else:
        print(result)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="loppers",
        description="Extract source file skeletons using tree-sitter queries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_app_version()}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Extract command
    extract_parser = subparsers.add_parser(
        "extract",
        help="Extract skeleton from file or stdin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  loppers extract file.py                         # From file
  cat file.py | loppers extract -l python         # From stdin
  echo 'def foo(): pass' | loppers extract -l python
        """,
    )
    extract_parser.add_argument(
        "file",
        nargs="?",
        help="File to extract (omit for stdin)",
    )
    extract_parser.add_argument(
        "-l",
        "--language",
        help="Language (auto-detected from extension if FILE provided)",
    )
    extract_parser.add_argument(
        "-o",
        "--output",
        help="Output file (default: stdout)",
    )
    extract_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print verbose output to stderr",
    )
    extract_parser.set_defaults(func=cmd_extract)

    # Concatenate command (default)
    concatenate_parser = subparsers.add_parser(
        "concatenate",
        help="Concatenate files with skeleton extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  loppers concatenate src/                       # Recursive (default)
  loppers concatenate --no-recursive src/        # Only immediate files
  loppers concatenate -I "*.test.py" src/        # Add ignore pattern
  loppers concatenate --no-default-ignore src/   # No built-in ignores
  loppers concatenate --no-extract src/          # Include original content
        """,
    )
    add_shared_args(concatenate_parser)
    concatenate_parser.add_argument(
        "--no-extract",
        action="store_true",
        help="Include original files without skeleton extraction",
    )
    concatenate_parser.set_defaults(func=cmd_concatenate)

    # Tree command
    tree_parser = subparsers.add_parser(
        "tree",
        help="Show directory tree of discovered files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  loppers tree src/                              # Recursive tree
  loppers tree --no-recursive src/               # Non-recursive tree
  loppers tree -I "*.test.py" src/               # With custom ignore
  loppers tree --collapse-single-dirs src/       # Collapse deep packages (e.g., main/java/com/example)
        """,
    )
    add_shared_args(tree_parser)
    tree_parser.set_defaults(func=cmd_tree)

    # Files command
    files_parser = subparsers.add_parser(
        "files",
        help="List all discovered files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  loppers files src/                             # List files
  loppers files src/ tests/                      # Multiple paths
  loppers files --no-recursive src/              # Non-recursive
        """,
    )
    add_shared_args(files_parser)
    files_parser.set_defaults(func=cmd_files)

    args = parser.parse_args()

    # If no command specified, default to concatenate
    if not hasattr(args, "func"):
        if not args.command:
            # No command provided, show help
            parser.print_help()
            sys.exit(0)
        else:
            parser.print_help()
            sys.exit(1)

    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()

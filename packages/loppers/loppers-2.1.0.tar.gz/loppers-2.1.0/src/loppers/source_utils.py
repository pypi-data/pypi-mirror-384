from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from pathlib import Path

from binaryornot.check import is_binary
from pathspec import PathSpec

from loppers.extensions import get_language
from loppers.ignore_patterns import DEFAULT_IGNORE_PATTERNS
from loppers.loppers import SkeletonExtractor

Tree = defaultdict[str, "Tree"]


def tree_as_str(paths: list[str], *, collapse_single_dirs: bool = False) -> str:
    """Return a formatted tree-like string representation of the given paths.

    Args:
        paths: List of file paths
        collapse_single_dirs: Collapse directories with single children (e.g., java/com/example)
    """

    def build_tree(paths: list[str]) -> Tree:
        """Build a nested dict representing the directory tree from a list of file paths."""

        def node_factory() -> Tree:
            return defaultdict(node_factory)

        root: Tree = node_factory()
        for path in paths:
            parts = Path(path).parts
            node = root
            for part in parts:
                node = node[part]
        return root

    def render_tree(node: Tree, prefix: str = "") -> list[str]:
        """Recursively render the tree as a list of formatted lines."""
        lines: list[str] = []
        entries = sorted(node.keys(), key=lambda n: (not node[n], n.lower()))  # dirs first
        for i, name in enumerate(entries):
            connector = "└─ " if i == len(entries) - 1 else "├─ "

            # Collect collapsed path if enabled
            display_name = name
            current_node = node[name]

            if collapse_single_dirs:
                # Keep collapsing while there's a single child that's a directory
                while current_node and len(current_node) == 1:
                    child_name = list(current_node.keys())[0]
                    child_node = current_node[child_name]

                    if not child_node:
                        # Child is a file (empty dict), stop collapsing
                        break

                    # Child is a directory, collapse it into current path
                    display_name = f"{display_name}/{child_name}"
                    current_node = child_node

            lines.append(f"{prefix}{connector}{display_name}")
            if current_node:
                extension = "   " if i == len(entries) - 1 else "│  "
                lines.extend(render_tree(current_node, prefix + extension))
        return lines

    tree = build_tree(paths)
    lines = [".", *render_tree(tree)]
    return "\n".join(lines)


def describe_repository(
    root: str | Path,
    *,
    ignore_patterns: Sequence[str] | None = None,
    use_default_ignore: bool = True,
    respect_gitignore: bool = True,
) -> tuple[str, list[str]]:
    """Produce a tree-style text view of a repository and collect file paths.

    Args:
        root: Path to the repository root directory.
        ignore_patterns: Additional gitignore-style patterns to ignore.
        use_default_ignore: Whether to apply the built-in ignore patterns.
        respect_gitignore: Merge patterns from a `.gitignore` file in the root when True.

    Returns:
        A tuple where the first element is a string containing the hierarchical
        listing of all directories and files (relative to the provided root),
        and the second element is a list of file paths relative to the root.

    Raises:
        FileNotFoundError: If the provided root does not exist.
        NotADirectoryError: If the provided root is not a directory.
    """
    root_path = Path(root)
    if not root_path.exists():
        raise FileNotFoundError(f"Root not found: {root_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"Expected a directory at: {root_path}")

    patterns: list[str] = []
    if use_default_ignore:
        patterns.extend(DEFAULT_IGNORE_PATTERNS)
    if respect_gitignore:
        gitignore_path = root_path / ".gitignore"
        if gitignore_path.exists():
            gitignore_lines = [
                line.strip()
                for line in gitignore_path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
            patterns.extend(gitignore_lines)
    if ignore_patterns:
        patterns.extend(ignore_patterns)
    spec = PathSpec.from_lines("gitwildmatch", patterns) if patterns else None

    tree_lines: list[str] = []
    file_list: list[str] = []

    def iter_entries(path: Path) -> Iterable[Path]:
        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        yield from entries

    def walk(current: Path, depth: int) -> None:
        indent = "  " * depth
        for entry in iter_entries(current):
            relative_path = entry.relative_to(root_path)
            display_name = f"{relative_path.name}/" if entry.is_dir() else relative_path.name
            relative_str = relative_path.as_posix()
            if spec:
                if entry.is_dir():
                    if spec.match_file(f"{relative_str}/") or spec.match_file(relative_str):
                        continue
                else:
                    if spec.match_file(relative_str):
                        continue
            tree_lines.append(f"{indent}{display_name}")
            if entry.is_dir():
                walk(entry, depth + 1)
            else:
                file_list.append(str(relative_path))

    walk(root_path, 0)
    file_tree = tree_as_str(file_list)
    return file_tree, file_list


def extract_skeleton(source: str, language: str) -> str:
    """Extract skeleton from source code.

    Lower-level function that extracts skeleton for a given language.

    Args:
        source: Source code to process
        language: Programming language identifier

    Returns:
        Skeleton with function implementations removed

    Raises:
        ValueError: If language is not supported
    """
    extractor = SkeletonExtractor(language)
    return extractor.extract(source)


def get_skeleton(file_path: Path | str, *, add_header: bool = False) -> str:
    """Extract skeleton from a file by auto-detecting language from extension.

    Args:
        file_path: Path to the file
        add_header: If True, prepend "--- <filepath>" header to skeleton

    Returns:
        Skeleton with function implementations removed, optionally with header

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file language is not supported
    """
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    # Auto-detect language from extension
    language = get_language(str(path.suffix))
    if not language:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    # Read file content
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"Could not read file as text: {e}")

    # Extract skeleton
    skeleton = extract_skeleton(content, language)

    # Add header if requested
    if add_header:
        skeleton = f"--- {path}\n{skeleton}"

    return skeleton


def find_files(
    root: str | Path,
    *,
    recursive: bool = True,
    ignore_patterns: Sequence[str] | None = None,
    use_default_ignore: bool = True,
    respect_gitignore: bool = True,
) -> list[str]:
    """Collect all non-binary text files from a root directory.

    Args:
        root: Root directory path
        recursive: Recursively traverse directories (default True)
        ignore_patterns: Additional gitignore-style patterns to ignore
        use_default_ignore: Apply built-in ignore patterns (node_modules, .git, etc.)
        respect_gitignore: Respect .gitignore file in root when True

    Returns:
        List of file paths relative to root (respects ignore patterns and binary detection)

    Raises:
        FileNotFoundError: If root does not exist
        NotADirectoryError: If root is not a directory
    """
    root_path = Path(root)
    if not root_path.exists():
        raise FileNotFoundError(f"Root not found: {root_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"Expected a directory at: {root_path}")

    patterns: list[str] = []
    if use_default_ignore:
        patterns.extend(DEFAULT_IGNORE_PATTERNS)
    if respect_gitignore:
        gitignore_path = root_path / ".gitignore"
        if gitignore_path.exists():
            gitignore_lines = [
                line.strip()
                for line in gitignore_path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
            patterns.extend(gitignore_lines)
    if ignore_patterns:
        patterns.extend(ignore_patterns)
    spec = PathSpec.from_lines("gitwildmatch", patterns) if patterns else None

    files_to_process: list[str] = []

    if not recursive:
        # Non-recursive: just get immediate files
        for entry in sorted(root_path.iterdir()):
            if entry.is_file():
                relative_str = entry.relative_to(root_path).as_posix()
                if spec and spec.match_file(relative_str):
                    continue
                if not is_binary(str(entry)):
                    files_to_process.append(relative_str)
    else:
        # Recursive: collect all files
        def walk(current: Path) -> None:
            for entry in sorted(current.iterdir()):
                relative_path = entry.relative_to(root_path)
                relative_str = relative_path.as_posix()
                if spec:
                    if entry.is_dir():
                        if spec.match_file(f"{relative_str}/") or spec.match_file(relative_str):
                            continue
                    else:
                        if spec.match_file(relative_str):
                            continue
                if entry.is_dir():
                    walk(entry)
                else:
                    if not is_binary(str(entry)):
                        files_to_process.append(relative_str)

        walk(root_path)

    return sorted(files_to_process)


def get_tree(
    root: str | Path,
    *,
    recursive: bool = True,
    ignore_patterns: Sequence[str] | None = None,
    use_default_ignore: bool = True,
    respect_gitignore: bool = True,
    collapse_single_dirs: bool = False,
) -> str:
    """Display formatted directory tree from a root directory.

    Args:
        root: Root directory path
        recursive: Recursively traverse directories (default True)
        ignore_patterns: Additional gitignore-style patterns to ignore
        use_default_ignore: Apply built-in ignore patterns (node_modules, .git, etc.)
        respect_gitignore: Respect .gitignore file in root when True
        collapse_single_dirs: Collapse directories with single children (default False)

    Returns:
        Formatted tree representation

    Raises:
        FileNotFoundError: If root does not exist
        NotADirectoryError: If root is not a directory
    """
    files = find_files(
        root,
        recursive=recursive,
        ignore_patterns=ignore_patterns,
        use_default_ignore=use_default_ignore,
        respect_gitignore=respect_gitignore,
    )
    return tree_as_str(files, collapse_single_dirs=collapse_single_dirs)

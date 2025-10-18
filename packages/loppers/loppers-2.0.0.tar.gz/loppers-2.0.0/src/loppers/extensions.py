"""File extension to language mapping."""

from __future__ import annotations

# Map file extensions to language identifiers
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    # Python
    ".py": "python",
    ".pyi": "python",
    ".pyw": "python",
    # JavaScript
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    # TypeScript
    ".ts": "typescript",
    ".tsx": "tsx",
    ".mts": "typescript",
    ".cts": "typescript",
    # Java
    ".java": "java",
    # Go
    ".go": "go",
    # Rust
    ".rs": "rust",
    # C++
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".c++": "cpp",
    ".hpp": "cpp",
    # C
    ".c": "c",
    ".h": "c",
    # C#
    ".cs": "csharp",
    # Ruby
    ".rb": "ruby",
    ".erb": "ruby",
    ".rbx": "ruby",
    # PHP
    ".php": "php",
    ".phtml": "php",
    ".php3": "php",
    ".php4": "php",
    ".php5": "php",
    ".phps": "php",
    # Kotlin
    ".kt": "kotlin",
    ".kts": "kotlin",
}


def get_language(extension: str) -> str | None:
    """Get language for file extension.

    Args:
        extension: File extension (with or without dot)

    Returns:
        Language identifier, or None if not found
    """
    ext = extension if extension.startswith(".") else f".{extension}"
    return EXTENSION_TO_LANGUAGE.get(ext.lower())

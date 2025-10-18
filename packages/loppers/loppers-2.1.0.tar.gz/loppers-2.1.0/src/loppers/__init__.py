"""Loppers: Extract source file skeletons using tree-sitter queries.

Remove function implementations while preserving structure using AST queries.
Compatible with tree-sitter >= 0.25
"""

from __future__ import annotations

from loppers.extensions import EXTENSION_TO_LANGUAGE, get_language
from loppers.source_utils import (
    extract_skeleton,
    find_files,
    get_skeleton,
    get_tree,
)

__all__ = [
    "get_skeleton",
    "find_files",
    "get_tree",
    "extract_skeleton",
    "EXTENSION_TO_LANGUAGE",
    "get_language",
]

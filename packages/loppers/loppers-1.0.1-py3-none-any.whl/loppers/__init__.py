"""Loppers: Extract source file skeletons using tree-sitter queries.

Remove function implementations while preserving structure using AST queries.
Compatible with tree-sitter >= 0.25
"""

from __future__ import annotations

from loppers.cli import concatenate_files
from loppers.loppers import SkeletonExtractor, extract
from loppers.mapping import EXTENSION_TO_LANGUAGE, get_language

__all__ = [
    "SkeletonExtractor",
    "extract",
    "concatenate_files",
    "EXTENSION_TO_LANGUAGE",
    "get_language",
]

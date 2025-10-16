"""Loppers: Extract source file skeletons using tree-sitter queries.

Remove function implementations while preserving structure using AST queries.
Compatible with tree-sitter >= 0.25
"""

from __future__ import annotations

from loppers.loppers import SkeletonExtractor, extract
from loppers.mapping import EXTENSION_TO_LANGUAGE, get_language

__all__ = [
    "SkeletonExtractor",
    "extract",
    "EXTENSION_TO_LANGUAGE",
    "get_language",
]

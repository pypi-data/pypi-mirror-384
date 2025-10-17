"""Loppers: Extract source file skeletons using tree-sitter queries.

Remove function implementations while preserving structure using AST queries.
Compatible with tree-sitter >= 0.25
"""

from __future__ import annotations

from loppers.concatenator import collect_files, concatenate_files, is_binary_file
from loppers.loppers import SkeletonExtractor, extract
from loppers.mapping import EXTENSION_TO_LANGUAGE, get_language

__all__ = [
    "SkeletonExtractor",
    "extract",
    "concatenate_files",
    "collect_files",
    "is_binary_file",
    "EXTENSION_TO_LANGUAGE",
    "get_language",
]

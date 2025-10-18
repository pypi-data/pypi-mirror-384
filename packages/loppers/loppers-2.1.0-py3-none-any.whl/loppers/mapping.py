"""File extension to language mapping (backwards compatibility module).

This module re-exports from extensions.py for backwards compatibility.
New code should import directly from extensions.
"""

from __future__ import annotations

from loppers.extensions import EXTENSION_TO_LANGUAGE, get_language

__all__ = ["EXTENSION_TO_LANGUAGE", "get_language"]

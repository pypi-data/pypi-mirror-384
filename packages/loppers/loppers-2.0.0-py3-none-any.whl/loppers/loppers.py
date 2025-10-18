"""Loppers: Extract source file skeletons using tree-sitter queries.

Remove function implementations while preserving structure using AST queries.
Compatible with tree-sitter >= 0.25
"""

from __future__ import annotations

from dataclasses import dataclass

import tree_sitter_language_pack
from tree_sitter import Language, Node, Parser, Query, QueryCursor, Tree


@dataclass
class LanguageConfig:
    """Configuration for a programming language.

    Attributes:
        name: Language identifier (e.g., "python", "javascript")
        body_query: Tree-sitter query to find function/method bodies to remove
    """

    name: str
    body_query: str


# Language-specific queries for finding bodies to remove

LANGUAGE_CONFIGS: dict[str, LanguageConfig] = {
    "python": LanguageConfig(
        name="python",
        body_query=("[(function_definition body: (block) @body)]"),
    ),
    "javascript": LanguageConfig(
        name="javascript",
        body_query=(
            "[(function_declaration body: (statement_block) @body) "
            "(arrow_function body: (_) @body) "
            "(function_expression body: (statement_block) @body) "
            "(method_definition body: (statement_block) @body)]"
        ),
    ),
    "typescript": LanguageConfig(
        name="typescript",
        body_query=(
            "[(function_declaration body: (statement_block) @body) "
            "(arrow_function body: (_) @body) "
            "(function_expression body: (statement_block) @body) "
            "(method_definition body: (statement_block) @body)]"
        ),
    ),
    "tsx": LanguageConfig(
        name="typescript",
        body_query=(
            "[(function_declaration body: (statement_block) @body) "
            "(arrow_function body: (_) @body) "
            "(function_expression body: (statement_block) @body) "
            "(method_definition body: (statement_block) @body)]"
        ),
    ),
    "java": LanguageConfig(
        name="java",
        body_query=(
            "[(method_declaration body: (block) @body) "
            "(constructor_declaration (constructor_body) @body)]"
        ),
    ),
    "go": LanguageConfig(
        name="go",
        body_query=(
            "[(function_declaration body: (block) @body) (method_declaration body: (block) @body)]"
        ),
    ),
    "rust": LanguageConfig(
        name="rust",
        body_query=("[(function_item body: (block) @body)]"),
    ),
    "cpp": LanguageConfig(
        name="cpp",
        body_query=("[(function_definition body: (compound_statement) @body)]"),
    ),
    "c": LanguageConfig(
        name="c",
        body_query=("[(function_definition body: (compound_statement) @body)]"),
    ),
    "csharp": LanguageConfig(
        name="csharp",
        body_query=(
            "[(method_declaration body: (block) @body) (accessor_declaration body: (block) @body)]"
        ),
    ),
    "ruby": LanguageConfig(
        name="ruby",
        body_query=(
            "[(method body: (body_statement) @body) "
            "(singleton_method body: (body_statement) @body)]"
        ),
    ),
    "php": LanguageConfig(
        name="php",
        body_query=("[(method_declaration body: (compound_statement) @body)]"),
    ),
    "kotlin": LanguageConfig(
        name="kotlin",
        body_query=(
            "[(function_declaration (function_body) @body) "
            "(getter (function_body) @body) "
            "(setter (function_body) @body)]"
        ),
    ),
    "swift": LanguageConfig(
        name="swift",
        body_query=("[(function_declaration (function_body) @body)]"),
    ),
    "lua": LanguageConfig(
        name="lua",
        body_query=("[(function_declaration (block) @body)]"),
    ),
    "scala": LanguageConfig(
        name="scala",
        body_query=("[(function_definition (block) @body)]"),
    ),
    "groovy": LanguageConfig(
        name="groovy",
        body_query=("[((block (unit (func))) @body)]"),
    ),
    "objc": LanguageConfig(
        name="objc",
        body_query=("[(compound_statement) @body]"),
    ),
}


class SkeletonExtractor:
    """Extract source skeletons using tree-sitter queries.

    This class parses source code and removes function/method implementations
    while preserving signatures, class definitions, and docstrings (for Python).
    """

    def __init__(self, language: str) -> None:
        """Initialize extractor for a language.

        Args:
            language: Programming language (python, javascript, java, etc.)

        Raises:
            ValueError: If language not supported
        """
        if language not in LANGUAGE_CONFIGS:
            supported = ", ".join(LANGUAGE_CONFIGS.keys())
            msg = f"Language '{language}' not supported. Supported: {supported}"
            raise ValueError(msg)

        self.language: str = language
        self.config: LanguageConfig = LANGUAGE_CONFIGS[language]

        # Load language with tree-sitter >= 0.25 API
        self.lang: Language = tree_sitter_language_pack.get_language(language)  # type: ignore

        self.parser: Parser = Parser()
        self.parser.language = self.lang

    def extract(self, source_code: str) -> str:
        """Extract skeleton from source code.

        Parses the source code and removes function/method bodies while
        preserving signatures, class definitions, and docstrings (Python only).

        Args:
            source_code: Source code to process

        Returns:
            Skeleton with function implementations removed
        """
        tree: Tree = self.parser.parse(source_code.encode())
        lines: list[str] = source_code.splitlines(keepends=True)

        # Find all function bodies to remove
        query: Query = Query(self.lang, self.config.body_query)
        cursor: QueryCursor = QueryCursor(query)
        captures = cursor.captures(tree.root_node)

        # Collect line ranges to remove
        lines_to_remove: set[int] = set()
        for capture_name, node_list in captures.items():
            for node in node_list:
                start_line: int = node.start_point[0]
                end_line: int = node.end_point[0]

                # For Python, preserve docstrings (first string in body)
                skip_start: int = start_line
                if self.language == "python" and node.child_count > 0:
                    first_child: Node = node.child(0)  # type: ignore
                    if (
                        first_child.type == "expression_statement"
                        and first_child.child_count > 0
                        and first_child.child(0).type == "string"  # type: ignore
                    ):
                        # Skip the docstring lines when removing
                        skip_start = first_child.end_point[0] + 1

                # For languages with braces, skip the opening brace line if it contains the declaration
                # (Ruby uses def...end, so body capture doesn't include the def line)
                # (Lua uses def...end, so body capture doesn't include the def line)
                if self.language not in ("python", "ruby", "lua") and start_line < end_line:
                    skip_start = start_line + 1

                # For single-line bodies (like Lua), include the line in removal
                if start_line == end_line:
                    end_inclusive = end_line + 1
                # For multi-line bodies:
                # - Python/Ruby/Lua: remove everything including end_line
                # - Other languages: preserve closing brace (don't include end_line)
                else:
                    end_inclusive = (
                        end_line + 1 if self.language in ("python", "ruby", "lua") else end_line
                    )

                for line_num in range(skip_start, end_inclusive):
                    lines_to_remove.add(line_num)

        # Build skeleton by keeping non-body lines
        skeleton: list[str] = []
        for i, line in enumerate(lines):
            if i not in lines_to_remove:
                skeleton.append(line)

        return "".join(skeleton).rstrip()


def extract(source_code: str, language: str) -> str:
    """Extract skeleton from source code.

    Convenience function that creates an extractor and extracts the skeleton
    in one call.

    Args:
        source_code: Source code to process
        language: Programming language

    Returns:
        Skeleton with implementations removed

    Raises:
        ValueError: If language not supported
    """
    extractor: SkeletonExtractor = SkeletonExtractor(language)
    return extractor.extract(source_code)

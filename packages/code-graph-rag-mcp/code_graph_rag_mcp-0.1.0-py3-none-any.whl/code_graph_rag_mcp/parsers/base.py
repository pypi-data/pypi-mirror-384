from __future__ import annotations

import abc
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, TYPE_CHECKING

from tree_sitter import Language, Parser
from tree_sitter_languages import get_language

from code_graph_rag_mcp.models.graph import ParseResult

if TYPE_CHECKING:
    from code_graph_rag_mcp.chunker import ChunkBuilder

LOGGER = logging.getLogger(__name__)


class TreeSitterParseError(RuntimeError):
    pass


@dataclass(slots=True)
class ParserContext:
    root_path: Path
    file_path: Path
    content: str


class LanguageAdapter(abc.ABC):
    """Abstract base for language-specific symbol extraction."""

    language_id: str

    def __init__(self, chunk_builder: "ChunkBuilder" | None = None) -> None:
        self._parser = Parser()
        self._parser.set_language(self.language)
        self.chunk_builder = chunk_builder

    @property
    def language(self) -> Language:
        try:
            return get_language(self.language_id)
        except Exception as exc:  # pragma: no cover - upstream failures are rare
            raise TreeSitterParseError(f"Tree-sitter language '{self.language_id}' unavailable") from exc

    def parse(self, context: ParserContext) -> ParseResult:
        LOGGER.debug("Parsing %s", context.file_path)
        tree = self._parser.parse(context.content.encode("utf-8"))
        return self.collect(context, tree.root_node)

    @abc.abstractmethod
    def collect(self, context: ParserContext, root_node) -> ParseResult:  # type: ignore[override]
        """Walk the syntax tree and return extracted graph elements."""


class ParserRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, LanguageAdapter] = {}

    def register(self, adapter: LanguageAdapter) -> None:
        LOGGER.debug("Registering language adapter %s", adapter.language_id)
        self._adapters[adapter.language_id] = adapter

    def get(self, language_id: str) -> Optional[LanguageAdapter]:
        return self._adapters.get(language_id)

    def supported(self) -> List[str]:
        return list(self._adapters.keys())


registry = ParserRegistry()


__all__ = [
    "LanguageAdapter",
    "ParserContext",
    "ParseResult",
    "ParserRegistry",
    "registry",
]

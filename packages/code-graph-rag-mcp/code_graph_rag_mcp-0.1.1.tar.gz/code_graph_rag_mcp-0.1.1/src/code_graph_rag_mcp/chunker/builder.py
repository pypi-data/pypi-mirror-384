from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from tree_sitter import Node

from code_graph_rag_mcp.config.models import ChunkConfig
from code_graph_rag_mcp.models.graph import Chunk, Symbol
from code_graph_rag_mcp.parsers.base import ParserContext


@dataclass(slots=True)
class ChunkBuilder:
    config: ChunkConfig

    def build_chunk(self, context: ParserContext, symbol: Symbol, node: Node) -> Chunk:
        snippet = self._slice_content(context.content, node)
        prelude = self._build_prelude(context.file_path, symbol)
        metadata: Dict[str, object] = {
            "kind": symbol.kind.value,
            "prelude": prelude,
            "span": [symbol.span_start, symbol.span_end],
        }
        return Chunk(
            symbol_id=symbol.metadata["id"],
            file_path=symbol.file_path,
            content=snippet,
            metadata=metadata,
        )

    def _build_prelude(self, path: Path, symbol: Symbol) -> str:
        parts = [str(path)]
        if "signature" in symbol.metadata:
            parts.append(symbol.metadata["signature"])
        return " - ".join(parts)

    def _slice_content(self, content: str, node: Node) -> str:
        data = content.encode("utf-8")
        return data[node.start_byte : node.end_byte].decode("utf-8", errors="ignore")


__all__ = ["ChunkBuilder"]

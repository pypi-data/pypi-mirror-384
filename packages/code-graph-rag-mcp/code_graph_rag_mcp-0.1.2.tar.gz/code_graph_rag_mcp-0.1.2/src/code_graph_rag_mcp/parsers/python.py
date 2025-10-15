from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from tree_sitter import Node

from code_graph_rag_mcp.models.graph import Chunk, EdgeKind, NodeKind, ParseResult, Relation, Symbol
from code_graph_rag_mcp.parsers.base import LanguageAdapter, ParserContext, registry

PY_SYMBOLS = {
    "function_definition": NodeKind.FUNCTION,
    "class_definition": NodeKind.CLASS,
}


class PythonAdapter(LanguageAdapter):
    language_id = "python"

    def __init__(self, chunk_builder=None) -> None:
        super().__init__(chunk_builder=chunk_builder)

    def collect(self, context: ParserContext, root_node: Node) -> ParseResult:  # type: ignore[override]
        result = ParseResult()
        file_symbol = self._create_file_symbol(context)
        result.symbols.append(file_symbol)

        for node in self._walk(root_node):
            base_kind = PY_SYMBOLS.get(node.type)
            if not base_kind:
                continue

            kind = self._resolve_kind(node, base_kind)
            symbol = self._symbol_from_node(context, node, kind)
            if not symbol:
                continue

            result.symbols.append(symbol)
            target_id = file_symbol.metadata["id"]
            if kind is NodeKind.METHOD:
                class_symbol = self._nearest_class_symbol(result, node.parent)
                if class_symbol:
                    target_id = class_symbol.metadata["id"]
                    result.relations.append(
                        Relation(
                            source=symbol.metadata["id"],
                            target=class_symbol.metadata["id"],
                            kind=EdgeKind.BELONGS_TO,
                        )
                    )
            else:
                result.relations.append(
                    Relation(
                        source=symbol.metadata["id"],
                        target=file_symbol.metadata["id"],
                        kind=EdgeKind.BELONGS_TO,
                    )
                )

            result.chunks.append(self._build_chunk(context, symbol, node))

        return result

    def _create_file_symbol(self, context: ParserContext) -> Symbol:
        path = self._relative_path(context.root_path, context.file_path)
        content_bytes = context.content.encode("utf-8")
        identifier = self._symbol_id(str(path), "file", 0, len(content_bytes))
        return Symbol(
            name=str(path),
            kind=NodeKind.FILE,
            file_path=context.file_path,
            span_start=0,
            span_end=len(content_bytes),
            metadata={"id": identifier},
        )

    def _symbol_from_node(self, context: ParserContext, node: Node, kind: NodeKind) -> Optional[Symbol]:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return None
        name = name_node.text.decode("utf-8")
        span_start = node.start_byte
        span_end = node.end_byte
        identifier = self._symbol_id(name, kind.value, span_start, span_end)
        metadata = {
            "id": identifier,
            "signature": name,
        }
        if kind is NodeKind.METHOD and node.parent:
            class_name_node = node.parent.child_by_field_name("name")
            if class_name_node:
                metadata["class_name"] = class_name_node.text.decode("utf-8")
        return Symbol(
            name=name,
            kind=kind,
            file_path=context.file_path,
            span_start=span_start,
            span_end=span_end,
            metadata=metadata,
        )

    def _resolve_kind(self, node: Node, base_kind: NodeKind) -> NodeKind:
        if base_kind is NodeKind.FUNCTION and node.parent and node.parent.type == "class_definition":
            return NodeKind.METHOD
        return base_kind

    def _nearest_class_symbol(self, result: ParseResult, parent: Optional[Node]) -> Optional[Symbol]:
        if parent is None:
            return None
        name_node = parent.child_by_field_name("name")
        if not name_node:
            return None
        class_name = name_node.text.decode("utf-8")
        for symbol in result.symbols:
            if symbol.kind is NodeKind.CLASS and symbol.name == class_name:
                return symbol
        return None

    def _walk(self, root: Node) -> Iterable[Node]:
        stack = [root]
        while stack:
            node = stack.pop()
            yield node
            stack.extend(node.children)

    def _relative_path(self, root: Path, path: Path) -> Path:
        try:
            return path.relative_to(root)
        except ValueError:
            return path

    def _symbol_id(self, name: str, kind: str, start: int, end: int) -> str:
        return f"{kind}:{name}:{start}-{end}"

    def _build_chunk(self, context: ParserContext, symbol: Symbol, node: Node) -> Chunk:
        if self.chunk_builder:
            return self.chunk_builder.build_chunk(context, symbol, node)
        content_bytes = context.content.encode("utf-8")
        snippet = content_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="ignore")
        return Chunk(
            symbol_id=symbol.metadata["id"],
            file_path=symbol.file_path,
            content=snippet,
            metadata={
                "kind": symbol.kind.value,
                "span": [symbol.span_start, symbol.span_end],
            },
        )


def register() -> None:
    registry.register(PythonAdapter())


__all__ = ["PythonAdapter", "register"]

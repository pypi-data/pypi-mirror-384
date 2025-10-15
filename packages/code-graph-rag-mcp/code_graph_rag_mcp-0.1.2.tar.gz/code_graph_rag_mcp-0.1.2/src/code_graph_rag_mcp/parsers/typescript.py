from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from tree_sitter import Node

from code_graph_rag_mcp.models.graph import Chunk, EdgeKind, NodeKind, ParseResult, Relation, Symbol
from code_graph_rag_mcp.parsers.base import LanguageAdapter, ParserContext, registry

SYMBOL_NODE_TYPES = {
    "function_declaration": NodeKind.FUNCTION,
    "class_declaration": NodeKind.CLASS,
    "method_definition": NodeKind.METHOD,
    "lexical_declaration": NodeKind.VARIABLE,
    "variable_statement": NodeKind.VARIABLE,
}


class TypeScriptAdapter(LanguageAdapter):
    language_id = "typescript"

    def __init__(self, language_id: str = "typescript", chunk_builder=None) -> None:
        self.language_id = language_id
        super().__init__(chunk_builder=chunk_builder)

    def collect(self, context: ParserContext, root_node: Node) -> ParseResult:  # type: ignore[override]
        result = ParseResult()
        file_symbol = self._create_file_symbol(context)
        result.symbols.append(file_symbol)

        for node in self._walk(root_node):
            kind = SYMBOL_NODE_TYPES.get(node.type)
            if not kind:
                continue
            symbol = self._symbol_from_node(context, node, kind)
            if not symbol:
                continue
            result.symbols.append(symbol)
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

    def _symbol_from_node(
        self,
        context: ParserContext,
        node: Node,
        kind: NodeKind,
    ) -> Optional[Symbol]:
        name_node = self._extract_name(node)
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
        if node.type == "method_definition" and node.parent:
            class_name = self._extract_name(node.parent)
            if class_name is not None:
                metadata["class_name"] = class_name.text.decode("utf-8")
        return Symbol(
            name=name,
            kind=kind,
            file_path=context.file_path,
            span_start=span_start,
            span_end=span_end,
            metadata=metadata,
        )

    def _extract_name(self, node: Node) -> Optional[Node]:
        for child in node.children:
            if child.type in {"identifier", "property_identifier"}:
                return child
            if child.type == "variable_declarator" and child.child_count:
                return child.child_by_field_name("name")
        return node.child_by_field_name("name")

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
    registry.register(TypeScriptAdapter("typescript"))
    registry.register(TypeScriptAdapter("javascript"))


__all__ = ["TypeScriptAdapter", "register"]

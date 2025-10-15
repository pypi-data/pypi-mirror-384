"""Tree-sitter language adapters."""

from code_graph_rag_mcp.parsers.base import LanguageAdapter, ParserContext, ParseResult, registry
from code_graph_rag_mcp.parsers.python import PythonAdapter, register as register_python
from code_graph_rag_mcp.parsers.typescript import TypeScriptAdapter, register as register_typescript

register_python()
register_typescript()

__all__ = [
    "LanguageAdapter",
    "ParserContext",
    "ParseResult",
    "registry",
    "PythonAdapter",
    "TypeScriptAdapter",
]

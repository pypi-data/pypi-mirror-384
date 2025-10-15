from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class NodeKind(str, Enum):
    MODULE = "module"
    FILE = "file"
    CLASS = "class"
    FUNCTION = "func"
    METHOD = "method"
    VARIABLE = "var"
    INTERFACE = "interface"


class EdgeKind(str, Enum):
    DEFINES = "defines"
    BELONGS_TO = "belongs_to"
    IMPORTS = "imports"
    CALLS = "calls"
    INHERITS = "inherits"
    OVERRIDES = "overrides"
    EXPORTS = "exports"


@dataclass(slots=True)
class Symbol:
    name: str
    kind: NodeKind
    file_path: Path
    span_start: int
    span_end: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Relation:
    source: str
    target: str
    kind: EdgeKind
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Chunk:
    symbol_id: str
    file_path: Path
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ParseResult:
    symbols: List[Symbol] = field(default_factory=list)
    relations: List[Relation] = field(default_factory=list)
    chunks: List[Chunk] = field(default_factory=list)
    diagnostics: List[Dict[str, Any]] = field(default_factory=list)


__all__ = [
    "NodeKind",
    "EdgeKind",
    "Symbol",
    "Relation",
    "Chunk",
    "ParseResult",
]

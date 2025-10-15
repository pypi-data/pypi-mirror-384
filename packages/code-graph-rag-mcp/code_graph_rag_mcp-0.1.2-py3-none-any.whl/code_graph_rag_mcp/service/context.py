from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from code_graph_rag_mcp.config.models import ServerConfig
from code_graph_rag_mcp.db import DatabaseManager
from code_graph_rag_mcp.indexer import Indexer


@dataclass(slots=True)
class ServiceContext:
    config: ServerConfig
    root: Path
    db: DatabaseManager
    indexer: Indexer


__all__ = ["ServiceContext"]

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from code_graph_rag_mcp.db import DatabaseManager


@dataclass(slots=True)
class DiagnosticReport:
    sqlite_extensions: Dict[str, bool]


def check_extensions(db: DatabaseManager) -> DiagnosticReport:
    return DiagnosticReport(sqlite_extensions=db.extension_status())


__all__ = ["DiagnosticReport", "check_extensions"]

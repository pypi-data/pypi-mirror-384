from __future__ import annotations

from typing import Dict

from code_graph_rag_mcp.db.queries import fetch_status
from code_graph_rag_mcp.service import ServiceContext
from code_graph_rag_mcp.service.diagnostics import check_extensions


async def status(ctx: ServiceContext) -> Dict[str, object]:
    with ctx.db.connection(read_only=True) as connection:
        counts = fetch_status(connection)
    diagnostics = check_extensions(ctx.db)
    return {
        "project": ctx.config.project,
        "root": str(ctx.root),
        "counts": counts,
        "supported_languages": ctx.config.parser.languages,
        "extensions": diagnostics.sqlite_extensions,
    }


__all__ = ["status"]

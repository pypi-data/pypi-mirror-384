from __future__ import annotations

from pathlib import Path
from typing import Dict

from code_graph_rag_mcp.db import operations
from code_graph_rag_mcp.db.queries import fetch_status
from code_graph_rag_mcp.service import ServiceContext


async def ingest_repo(ctx: ServiceContext, force: bool = True) -> Dict[str, object]:
    ctx.indexer.ingest_repository(force=force)
    with ctx.db.connection(read_only=True) as connection:
        status = fetch_status(connection)
    return {"status": status}


async def refresh_path(ctx: ServiceContext, path: str, force: bool = False) -> Dict[str, object]:
    relative = Path(path)
    ctx.indexer.ingest_path(relative, force=force)
    with ctx.db.connection(read_only=True) as connection:
        status = fetch_status(connection)
    return {"status": status, "path": str(relative)}


async def purge_path(ctx: ServiceContext, path: str) -> Dict[str, object]:
    relative = Path(path)
    with ctx.db.connection() as connection:
        row = connection.execute("SELECT id FROM files WHERE path = ?", (str(relative),)).fetchone()
        if row:
            file_id = row[0]
            operations.clear_file_artifacts(connection, file_id)
            connection.execute("DELETE FROM files WHERE id = ?", (file_id,))
    return {"path": str(relative), "status": "deleted"}


__all__ = ["ingest_repo", "refresh_path", "purge_path"]

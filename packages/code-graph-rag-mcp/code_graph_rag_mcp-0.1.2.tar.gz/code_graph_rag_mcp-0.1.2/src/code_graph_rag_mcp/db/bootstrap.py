from __future__ import annotations

import logging
import sqlite3
from typing import Iterable

from code_graph_rag_mcp.config.models import DatabaseConfig, EmbedConfig
from code_graph_rag_mcp.db import schema
from code_graph_rag_mcp.db.extensions import load_extensions

LOGGER = logging.getLogger(__name__)


def bootstrap_database(config: DatabaseConfig, embed: EmbedConfig | None = None) -> None:
    """Ensure the SQLite database exists with schema and extensions."""
    sqlite_path = config.resolved_path

    if config.ensure_parent:
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(sqlite_path)
    try:
        _initialize_database(connection, config, embed or EmbedConfig())
    finally:
        connection.close()


def _initialize_database(
    connection: sqlite3.Connection,
    config: DatabaseConfig,
    embed: EmbedConfig,
) -> None:
    _apply_pragmas(connection, schema.PRAGMA_STATEMENTS)
    load_extensions(connection, config, require=True)

    with connection:
        for statement in schema.SCHEMA_STATEMENTS:
            connection.executescript(statement)

        for statement in schema.vector_virtual_tables(embed.dim):
            connection.executescript(statement)

        connection.executescript(schema.bfs_virtual_table())


def _apply_pragmas(connection: sqlite3.Connection, pragmas: Iterable[str]) -> None:
    for pragma in pragmas:
        connection.execute(pragma)

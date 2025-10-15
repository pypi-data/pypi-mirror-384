from __future__ import annotations

import contextlib
import sqlite3
from typing import Iterator

from code_graph_rag_mcp.config.models import DatabaseConfig, EmbedConfig
from code_graph_rag_mcp.db import schema
from code_graph_rag_mcp.db.extensions import EXTENSION_LOAD_ORDER, resolve_extension_paths


class DatabaseManager:
    """Factory for SQLite connections with consistent pragmas and extensions."""

    def __init__(self, config: DatabaseConfig, embed: EmbedConfig | None = None) -> None:
        self.config = config
        self.embed = embed or EmbedConfig()
        self._extension_paths = resolve_extension_paths(config)

    def connect(self, read_only: bool = False) -> sqlite3.Connection:
        if read_only:
            uri = f"file:{self.config.resolved_path}?mode=ro"
            connection = sqlite3.connect(uri, uri=True, check_same_thread=False)
            self._apply_read_pragmas(connection)
        else:
            connection = sqlite3.connect(self.config.resolved_path, check_same_thread=False)
            self._apply_write_pragmas(connection)

        self._load_extensions(connection)
        return connection

    @contextlib.contextmanager
    def connection(self, read_only: bool = False) -> Iterator[sqlite3.Connection]:
        connection = self.connect(read_only=read_only)
        try:
            yield connection
            if not read_only:
                connection.commit()
        except Exception:
            if not read_only:
                connection.rollback()
            raise
        finally:
            connection.close()

    def extension_status(self) -> dict[str, bool]:
        return {attr: True for attr in self._extension_paths}

    def _apply_write_pragmas(self, connection: sqlite3.Connection) -> None:
        for pragma in schema.PRAGMA_STATEMENTS:
            connection.execute(pragma)

    def _apply_read_pragmas(self, connection: sqlite3.Connection) -> None:
        for pragma in schema.READ_ONLY_PRAGMAS:
            connection.execute(pragma)

    def _load_extensions(self, connection: sqlite3.Connection) -> None:
        if not self._extension_paths:
            return
        connection.enable_load_extension(True)
        try:
            for attr, entrypoint in EXTENSION_LOAD_ORDER:
                path = self._extension_paths.get(attr)
                if not path:
                    continue
                try:
                    connection.load_extension(str(path), entrypoint)
                except TypeError:
                    connection.execute("SELECT load_extension(?, ?)", (str(path), entrypoint))
        finally:
            connection.enable_load_extension(False)


__all__ = ["DatabaseManager"]
